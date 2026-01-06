"""
Authorization Extensions for GraphQL Resolvers

This module provides permission checking extensions that combine creator-based 
ownership with group-based role permissions. Users can always manage content 
they created, while group admins can manage content in their groups.

Key Features:
- Creator ownership: Users have permanent access to content they create
- Group permissions: Role-based access through group membership
- Hierarchical groups: Parent group admins can access child group content
- Auto-assignment: Automatically assigns group ownership on creation
- Root admin: Top-level admins have universal access

Role Definitions:
- viewer: Can read content
- editor: Can create and update content
- administrátor/admin: Can delete content and manage everything
"""

import typing
from strawberry.types import Info
from uoishelpers.gqlpermissions.TwoStageGenericBaseExtension import TwoStageGenericBaseExtension
from uoishelpers.gqlpermissions.LoadDataExtension import LoadDataExtension
from uoishelpers.gqlpermissions.RbacProviderExtension import RbacProviderExtension
from uoishelpers.gqlpermissions.RbacInsertProviderExtension import RbacInsertProviderExtension
from uoishelpers.gqlpermissions.UserRoleProviderExtension import UserRoleProviderExtension

# Standard role constants
VIEWER_ROLES = ["viewer", "editor", "administrátor", "admin"]
EDITOR_ROLES = ["editor", "administrátor", "admin"]
ADMIN_ROLES = ["administrátor", "admin"]


# ===========================================================================================
# PERMISSION FILTER - Filters extension kwargs before passing to resolver
# ===========================================================================================

class PermissionFilterExtension(TwoStageGenericBaseExtension):
    """Filters internal extension kwargs before calling the resolver.
    
    Extensions add kwargs like 'user_roles', 'rbacobject_id', 'db_row' during
    processing, but Strawberry resolvers use strict parameter matching and will
    reject unknown kwargs. This extension removes internal kwargs before calling
    the actual resolver function.
    
    Must be first in extension list (executes last).
    """
    
    async def resolve_async(
        self,
        next_: typing.Callable,
        source: typing.Any,
        info: Info,
        **kwargs
    ) -> typing.Any:
        """Filter out extension-internal kwargs before calling resolver."""
        # Extension-internal kwargs that should never reach the resolver
        internal_keys = {'user_roles', 'rbacobject_id', 'db_row'}
        
        # Filter out internal kwargs, keep all GraphQL arguments
        filtered_kwargs = {
            key: value 
            for key, value in kwargs.items() 
            if key not in internal_keys
        }
        
        return await next_(source, info, **filtered_kwargs)


# ===========================================================================================
# AUTO GROUP ASSIGNMENT - Assigns rbacobject_id automatically for inserts
# ===========================================================================================

class AutoGroupAssignmentExtension(TwoStageGenericBaseExtension):
    """Automatically assigns rbacobject_id from user's primary write group.
    
    When creating entities, if rbacobject_id is not provided, this extension
    automatically assigns the user's most specific (leaf) write group. This
    makes the API easier to use - users don't need to specify groups manually.
    
    Selection logic:
    - One write group: Use that group
    - Multiple groups: Use most specific (leaf) group
    - Leaf group: Group that is NOT a parent of any other user group
    """
    
    async def resolve_async(
        self,
        next_: typing.Callable,
        source: typing.Any,
        info: Info,
        **kwargs
    ) -> typing.Any:
        """Auto-assign rbacobject_id from user's write groups if not set."""
        # Find the input entity
        entity_input = None
        for key, value in kwargs.items():
            if hasattr(value, 'rbacobject_id'):
                entity_input = value
                break
        
        if entity_input:
            current_rbac = getattr(entity_input, 'rbacobject_id', None)
            
            if current_rbac is None:
                # Get user's write groups
                user = info.context.get("user", {})
                roles = user.get("roles", [])
                
                write_roles = EDITOR_ROLES
                write_groups = []
                for role in roles:
                    roletype_name = role.get("roletype", {}).get("name", "")
                    group_id = role.get("group", {}).get("id")
                    
                    if roletype_name in write_roles and group_id:
                        write_groups.append(group_id)
                
                if len(write_groups) >= 1:
                    # Find leaf groups (not parents of other groups)
                    parent_groups = set()
                    for group_id in write_groups:
                        for other_group_id in write_groups:
                            if group_id != other_group_id:
                                descendants = await get_group_children(info, group_id)
                                if other_group_id in descendants:
                                    parent_groups.add(group_id)
                    
                    leaf_groups = [g for g in write_groups if g not in parent_groups]
                    
                    if leaf_groups:
                        entity_input.rbacobject_id = leaf_groups[0]
                        kwargs['rbacobject_id'] = leaf_groups[0]
                    else:
                        entity_input.rbacobject_id = write_groups[0]
                        kwargs['rbacobject_id'] = write_groups[0]
                else:
                    raise PermissionError(
                        f"User does not have editor/admin role in any group. "
                        f"Cannot auto-assign group for creation."
                    )
            else:
                kwargs['rbacobject_id'] = current_rbac
        
        return await next_(source, info, **kwargs)


# ===========================================================================================
# PERMISSION CHECK - Creator ownership OR group-based role check
# ===========================================================================================

class OwnershipPermissionExtension(TwoStageGenericBaseExtension):
    """Checks creator ownership OR group-based permissions.
    
    Authorization succeeds if EITHER:
    1. User created the entity (createdby_id matches user.id) → ALWAYS ALLOW
    2. User has required role in entity's group (or parent group)
    
    This allows users to always manage their own content while giving
    group admins control over their groups' content.
    
    Args:
        roles: Required role names for group-based access
    """
    
    def __init__(self, roles: typing.List[str]):
        super().__init__()
        self.required_roles = roles
    
    async def resolve_async(
        self,
        next_: typing.Callable,
        source: typing.Any,
        info: Info,
        **kwargs
    ) -> typing.Any:
        """Check creator ownership OR group permissions."""
        
        user = info.context.get("user", {})
        user_id = user.get("id")
        user_roles = kwargs.get("user_roles", [])
        rbacobject_id = kwargs.get("rbacobject_id")
        db_row = kwargs.get("db_row")  # Exists for UPDATE/DELETE
        
        if not user_id:
            return self.return_error(info, message="User not authenticated", code="NOT_AUTHENTICATED")
        
        if not user_roles:
            return self.return_error(info, message="User has no roles", code="NO_ROLES")
        
        # ===================================================================
        # CHECK 1: Creator Ownership (permanent access)
        # ===================================================================
        if db_row:
            creator_id = getattr(db_row, 'createdby_id', None)
            if creator_id and str(creator_id) == str(user_id):
                # User created this entity - always allow
                return await next_(source, info, **kwargs)
        
        # ===================================================================
        # CHECK 2: Root Admin (universal access)
        # ===================================================================
        if await check_root_admin(info, user_roles):
            # Root admin can access everything
            return await next_(source, info, **kwargs)
        
        # ===================================================================
        # CHECK 3: Group-Based Permissions
        # ===================================================================
        if rbacobject_id:
            # Get all groups accessible to user (including parent groups)
            accessible_groups = await get_accessible_groups(info, user_roles, self.required_roles)
            
            if str(rbacobject_id) in [str(g) for g in accessible_groups]:
                # User has required role in entity's group or parent group
                return await next_(source, info, **kwargs)
        
        # ===================================================================
        # DENIED - Neither creator nor group member
        # ===================================================================
        return self.return_error(
            info, 
            message=f"Permission denied. You must be the creator or have {'/'.join(self.required_roles)} role in the entity's group.",
            code="PERMISSION_DENIED"
        )


# ===========================================================================================
# CHILD ENTITY RBAC PROVIDER - Gets parent entity's rbacobject_id
# ===========================================================================================

class ParentGroupProviderExtension(TwoStageGenericBaseExtension):
    """Gets rbacobject_id from parent entity for child entities.
    
    Child entities (like purchase items) typically don't have their own
    rbacobject_id. This extension loads the parent entity and extracts
    its rbacobject_id for permission checking.
    
    Args:
        parent_field: Field name containing parent ID (e.g., 'purchase_id')
        parent_loader: Loader name for parent entity (e.g., 'PurchaseModel')
    """
    
    def __init__(self, parent_field: str, parent_loader: str):
        super().__init__()
        self.parent_field = parent_field
        self.parent_loader = parent_loader
    
    async def resolve_async(
        self,
        next_: typing.Callable,
        source: typing.Any,
        info: Info,
        **kwargs
    ) -> typing.Any:
        """Load parent entity and extract its rbacobject_id."""
        from uoishelpers.resolvers import getLoadersFromInfo
        
        loaders = getLoadersFromInfo(info)
        
        # Get parent ID from input or existing entity
        parent_id = None
        entity_input = None
        for key, value in kwargs.items():
            if hasattr(value, self.parent_field):
                entity_input = value
                parent_id = getattr(value, self.parent_field, None)
                break
        
        if not parent_id and kwargs.get('db_row'):
            parent_id = getattr(kwargs['db_row'], self.parent_field, None)
        
        if parent_id:
            # Load parent entity
            loader = getattr(loaders, self.parent_loader, None)
            if loader:
                parent_entity = await loader.load(parent_id)
                if parent_entity:
                    kwargs['rbacobject_id'] = getattr(parent_entity, 'rbacobject_id', None)
                    kwargs['db_row'] = parent_entity
        
        return await next_(source, info, **kwargs)


# ===========================================================================================
# HELPER FUNCTIONS
# ===========================================================================================

async def get_group_children(info: Info, group_id: str) -> typing.List[str]:
    """Get all child groups of a given group (recursive).
    
    Args:
        info: Strawberry info context
        group_id: UUID of parent group
    
    Returns:
        List of child group UUIDs
    """
    ug_client = info.context.get('ug_client')
    if not ug_client:
        return []
    
    try:
        resp = await ug_client('''
            query($id: UUID!) {
                groupById(id: $id) {
                    id
                    subgroups {
                        id
                        subgroups {
                            id
                            subgroups { id }
                        }
                    }
                }
            }
        ''', {'id': group_id})
        
        group = resp.get('data', {}).get('groupById')
        if not group:
            return []
        
        def extract_ids(g):
            ids = []
            for sub in g.get('subgroups', []):
                ids.append(sub['id'])
                ids.extend(extract_ids(sub))
            return ids
        
        return extract_ids(group)
    except Exception:
        return []


async def check_root_admin(info: Info, user_roles: typing.List[dict]) -> bool:
    """Check if user is a root admin (admin in a group with no parent).
    
    Args:
        info: Strawberry info context
        user_roles: User's roles from UserRoleProviderExtension
    
    Returns:
        True if user is root admin, False otherwise
    """
    admin_role_names = ADMIN_ROLES
    
    for role in user_roles:
        roletype_name = role.get('roletype', {}).get('name', '')
        group = role.get('group', {})
        master_group_id = group.get('mastergroupId')
        
        if roletype_name in admin_role_names and master_group_id is None:
            # Admin role in a group with no parent = root admin
            return True
    
    return False


async def get_accessible_groups(
    info: Info, 
    user_roles: typing.List[dict], 
    required_roles: typing.List[str]
) -> typing.List[str]:
    """Get all groups where user has required roles (including parent groups).
    
    Args:
        info: Strawberry info context
        user_roles: User's roles
        required_roles: Required role names
    
    Returns:
        List of accessible group UUIDs
    """
    accessible = []
    
    for role in user_roles:
        roletype_name = role.get('roletype', {}).get('name', '')
        group_id = role.get('group', {}).get('id')
        
        if roletype_name in required_roles and group_id:
            accessible.append(group_id)
            # Add child groups (hierarchical permissions)
            children = await get_group_children(info, group_id)
            accessible.extend(children)
    
    return list(set(accessible))  # Remove duplicates


async def filter_by_permissions(
    info: Info,
    items: typing.List[typing.Any],
    required_roles: typing.List[str] = VIEWER_ROLES
) -> typing.List[typing.Any]:
    """Filter list of entities by user permissions.
    
    Returns only entities where user is either:
    1. The creator (createdby_id matches user.id)
    2. Has required role in entity's group or parent groups
    3. Is root admin (sees everything)
    
    Args:
        info: Strawberry info context
        items: List of entities to filter
        required_roles: Required roles for group access
    
    Returns:
        Filtered list of entities user can access
    """
    user = info.context.get("user", {})
    user_id = user.get("id")
    
    if not user_id:
        return []
    
    # Get user roles via UG service
    user_roles = []
    ug_client = info.context.get('ug_client')
    if ug_client:
        try:
            resp = await ug_client('''query { me { roles { group { id mastergroupId } roletype { name } } } }''')
            me = resp.get('data', {}).get('me', {})
            user_roles = me.get('roles', [])
        except Exception:
            pass
    
    # Check if root admin
    if await check_root_admin(info, user_roles):
        return items  # Root admin sees everything
    
    # Get accessible groups
    accessible_groups = await get_accessible_groups(info, user_roles, required_roles)
    
    # Filter items
    filtered = []
    for item in items:
        creator_id = getattr(item, 'createdby_id', None)
        rbacobject_id = getattr(item, 'rbacobject_id', None)
        
        # Check creator ownership
        if creator_id and str(creator_id) == str(user_id):
            filtered.append(item)
            continue
        
        # Check group permissions
        if rbacobject_id and str(rbacobject_id) in [str(g) for g in accessible_groups]:
            filtered.append(item)
    
    return filtered


# ===========================================================================================
# EXTENSION FACTORY FUNCTIONS
# ===========================================================================================

def create_insert_permissions(
    error_type: typing.Any,
    model_type: typing.Any,
    required_roles: typing.List[str] = EDITOR_ROLES
) -> typing.List[typing.Any]:
    """Create extension list for INSERT operations.
    
    Pipeline:
    1. PermissionFilterExtension - filters kwargs (executes LAST)
    2. OwnershipPermissionExtension - checks user has required roles
    3. UserRoleProviderExtension - loads user roles from UG service
    4. AutoGroupAssignmentExtension - auto-assigns rbacobject_id
    
    Args:
        error_type: Error union type (e.g., InsertError[ModelGQLType])
        model_type: GraphQL model type
        required_roles: Required role names
    
    Returns:
        List of extensions in correct order
    """
    return [
        PermissionFilterExtension(),
        OwnershipPermissionExtension(roles=required_roles),
        UserRoleProviderExtension(),
        AutoGroupAssignmentExtension(),
    ]


def create_update_permissions(
    error_type: typing.Any,
    model_type: typing.Any,
    required_roles: typing.List[str] = EDITOR_ROLES
) -> typing.List[typing.Any]:
    """Create extension list for UPDATE operations.
    
    Pipeline:
    1. PermissionFilterExtension - filters kwargs (executes LAST)
    2. OwnershipPermissionExtension - checks creator OR group role
    3. UserRoleProviderExtension - loads user roles from UG service
    4. RbacProviderExtension - extracts rbacobject_id from entity
    5. LoadDataExtension - batch loads existing entity by input.id
    
    Args:
        error_type: Error union type
        model_type: GraphQL model type
        required_roles: Required role names
    
    Returns:
        List of extensions in correct order
    """
    return [
        PermissionFilterExtension(),
        OwnershipPermissionExtension(roles=required_roles),
        UserRoleProviderExtension(),
        RbacProviderExtension(),
        LoadDataExtension(),
    ]


def create_delete_permissions(
    error_type: typing.Any,
    model_type: typing.Any,
    required_roles: typing.List[str] = ADMIN_ROLES
) -> typing.List[typing.Any]:
    """Create extension list for DELETE operations.
    
    Pipeline: Same as UPDATE but requires admin roles
    
    Args:
        error_type: Error union type
        model_type: GraphQL model type
        required_roles: Required role names (default: admin only)
    
    Returns:
        List of extensions in correct order
    """
    return [
        PermissionFilterExtension(),
        OwnershipPermissionExtension(roles=required_roles),
        UserRoleProviderExtension(),
        RbacProviderExtension(),
        LoadDataExtension(),
    ]


def create_child_update_permissions(
    error_type: typing.Any,
    model_type: typing.Any,
    parent_field: str,
    parent_loader: str,
    required_roles: typing.List[str] = EDITOR_ROLES
) -> typing.List[typing.Any]:
    """Create extension list for child entity UPDATE operations.
    
    Pipeline:
    1. PermissionFilterExtension - filters kwargs (executes LAST)
    2. OwnershipPermissionExtension - checks permissions
    3. UserRoleProviderExtension - loads user roles
    4. ParentGroupProviderExtension - gets parent's rbacobject_id
    5. LoadDataExtension - loads child entity
    
    Args:
        error_type: Error union type
        model_type: GraphQL model type
        parent_field: Field name with parent ID (e.g., 'purchase_id')
        parent_loader: Loader name for parent (e.g., 'PurchaseModel')
        required_roles: Required role names
    
    Returns:
        List of extensions in correct order
    """
    return [
        PermissionFilterExtension(),
        OwnershipPermissionExtension(roles=required_roles),
        UserRoleProviderExtension(),
        ParentGroupProviderExtension(parent_field=parent_field, parent_loader=parent_loader),
        LoadDataExtension(),
    ]
