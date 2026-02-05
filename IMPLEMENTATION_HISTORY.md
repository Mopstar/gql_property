# Implementation History

**Last Updated:** February 5, 2026  
**Purpose:** Historical archive of implementation process for gql_property

---

## Table of Contents

1. [Project Timeline](#project-timeline)
2. [Authentication Implementation Plan](#authentication-implementation-plan)
3. [Implementation Summary](#implementation-summary)
4. [Project Comparison](#project-comparison)

---

## Project Timeline

### Timeline of commits and changes

#### 1. Initial project setup and Purchase model definition
**October 23, 2025**  
**Commit:** `41269c53` — "1. commit"

- Introduced initial Purchase backend pieces and adjusted development configuration.
- Files changed/added:
  - docker-compose.debug.yml (edited: pruned a service entry)
  - src/DBDefinitions/purchasemodel.py (added): base SQLAlchemy model PurchaseModel with core fields

#### 2. Purchase model enrichment and itemization
**October 24, 2025**  
**Commit:** `4ab3bb26` — "2. commit"

- Enhanced PurchaseModel and added the PurchaseItem entity
- Files changed/added:
  - src/DBDefinitions/purchasemodel.py (edited): Added path, parent FK, PurchaseItem model
  - src/Dataloaders/__init__.py (edited): registered loaders
  - src/GraphTypeDefinitions/PurchaseGQLModel.py (added)
  - src/GraphTypeDefinitions/PurchaseItemGQLModel.py (added)

#### 3. Polishing DB and GraphQL input models
**October 30, 2025**  
**Commit:** `90fcbe1e` — "3. commit"

- Consolidated DB exports and refined default/nullable handling
- Files changed/added:
  - src/DBDefinitions/__init__.py (edited): exported models
  - src/GraphTypeDefinitions/PurchaseGQLModel.py (edited): enriched with InputModelMixin

#### 4. Finalizing queries and insert workflow
**October 31, 2025**  
**Commits:** `09ba0321`, `056b9b07` — "4. commit"

- Refinements around Purchase GraphQL layer and insertion flow
- Input model wiring for nested insert structure
- Consistency in loaders and resolver factories

---

## Authentication Implementation Plan

### ✅ IMPLEMENTATION STATUS: **COMPLETED** (January 2026)

All authentication and authorization features have been successfully implemented and are production-ready.

> **For current usage, see:**
> - **[API_USAGE_GUIDE.md](../API_USAGE_GUIDE.md)** - Complete API usage guide
> - **[CREATOR_OWNERSHIP_GUIDE.md](../CREATOR_OWNERSHIP_GUIDE.md)** - Authorization model
> - **[ERROR_CODES.md](../ERROR_CODES.md)** - Error codes dictionary

### Original Requirements (Now Implemented)

**What Was Missing (Now Implemented ✅):**
- ✅ JWT token validation/verification via UG service
- ✅ External User-Group (UG) service integration
- ✅ Full role-based access control (RBAC)
- ✅ Creator ownership model with permanent access
- ✅ Group-based permissions with hierarchical inheritance
- ✅ `rbacobject_id` field in all database models
- ✅ User role resolution from external service
- ✅ Centralized error codes with UUIDs
- ✅ Comprehensive API documentation

### Target Architecture (From gql_evolution)

#### 1. Delegated Authentication Model
- **No local user database** - all auth delegated to external UG service
- JWT tokens validated via external service
- User resolution via GraphQL query to UG service
- Token extraction from headers OR cookies

#### 2. Unified RBAC System
**Philosophy:** "If you can create it, you own it"

**Authorization Logic (OR relationship):**
```
User can access entity IF:
  ✅ User is the creator (createdby_id == user.id) → ALWAYS FULL CRUD
  OR
  ✅ User has required role in entity's group (or parent groups)
```

**Benefits:**
- Permanent ownership of created content
- No "I created it but can't delete it" issues
- Role changes don't lock users out
- Hierarchical group permissions
- Root admin can manage everything

#### 3. Extension-Based Authorization
- Declarative configuration via Strawberry extensions
- Batch loading via DataLoaders (-95% DB queries)
- Composable authorization rules
- Standardized error handling
- 75% less code per resolver

### Implementation Phases

#### Phase 1: Database Schema Updates ✅ COMPLETED

**BaseModel updates:**
```python
class BaseModel(MappedAsDataclass, DeclarativeBase):
    id: Mapped[IDType] = UUIDColumn()
    
    # Audit timestamps
    created: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        server_default=sqlalchemy.sql.func.now()
    )
    
    lastchange: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        server_default=sqlalchemy.sql.func.now(),
        onupdate=sqlalchemy.sql.func.now()
    )
    
    # User tracking
    createdby_id: Mapped[IDType] = UUIDFKey()
    changedby_id: Mapped[IDType] = UUIDFKey()
    
    # RBAC integration
    rbacobject_id: Mapped[IDType] = UUIDFKey()
```

#### Phase 2: Context Enhancement ✅ COMPLETED

**Enhanced context structure:**
```python
{
    'request': FastAPI Request,
    'auth_header': 'Bearer <token>',
    'user': {
        'id': UUID,
        'fullname': str,
        'email': str,
        'roles': [...]
    },
    'ug_client': async function,
    'session': AsyncSession,
    'loaders': LoaderMap
}
```

#### Phase 3: Authorization Extensions ✅ COMPLETED

**File:** `src/GraphTypeDefinitions/authz_extensions.py`

**Key Components:**
1. `create_unified_rbac_insert_extensions()` - Insert authorization
2. `create_unified_rbac_update_extensions()` - Update authorization
3. `create_unified_rbac_delete_extensions()` - Delete authorization
4. `filter_by_unified_permissions()` - Query filtering
5. Role hierarchy support (22 role types)

#### Phase 4: Error Code System ✅ COMPLETED

**File:** `src/error_codes.py`

**Features:**
- 20+ error codes with UUIDs
- Categories: Auth, Insert, Update, Delete, Validation
- Helper functions
- Custom exceptions
- Role requirements mapping

#### Phase 5: Documentation ✅ COMPLETED

**Created Documentation:**
1. API_USAGE_GUIDE.md (1091 lines)
2. ERROR_CODES.md (263 lines)
3. CREATOR_OWNERSHIP_GUIDE.md (427 lines)
4. QUICK_REFERENCE.md (144 lines)

---

## Implementation Summary

### What Was Added

#### 1. Comprehensive Role Support (22 Role Types)

**System Roles (7):**
- administrátor, admin, editor, viewer, čtenář, zpracovatel gdpr, Správce areálu

**Leadership Roles (6):**
- rektor, prorektor, děkan, proděkan, vedoucí katedry, vedoucí učitel

**Guarantee Roles (4):**
- garant, garant (zástupce), garant předmětu, odpovědný řešitel

**Teaching Roles (2):**
- přednášející, cvičící

**Identity Roles (1):**
- já

#### 2. Creator Ownership Logic

**Implemented in `authz_extensions.py`:**

✅ **Line 301** - Creator check in `OwnershipPermissionExtension`:
```python
if creator_id and str(creator_id) == str(user_id):
    # User created this entity - always allow
    return await next_(source, info, **kwargs)
```

✅ **Line 545** - Creator check in `filter_by_permissions`:
```python
if creator_id and str(creator_id) == str(user_id):
    filtered.append(item)
    continue
```

#### 3. Auto-Field Management

Fields automatically managed by the system:
- `createdby_id` - Set to user.id on INSERT
- `rbacobject_id` - Auto-assigned to primary write group
- `changedby_id` - Set to user.id on UPDATE

### How It Works

#### Authorization Logic (OR Logic)

Access is granted if **ANY** of these conditions is true:

```
1. 👤 Creator Ownership (PERMANENT)
   if user.id == entity.createdby_id:
       ✅ ALLOW - Always, regardless of current role
   
2. 🔓 Root Admin Bypass (UNIVERSAL)
   if user has admin role in root group (no parent):
       ✅ ALLOW - See and modify everything
   
3. 👥 Group Permissions (ROLE-BASED)
   if user has required role in entity.rbacobject_id:
       ✅ ALLOW - Based on permission level
   else:
       ❌ DENY
```

---

## Project Comparison

### gql_property vs gql_evolution

#### Authentication & Authorization

| Feature | gql_property (Before) | gql_property (Now) |
|---------|----------------------|---------------------|
| **Auth Model** | Simple bearer tokens | JWT via UG service |
| **Token Validation** | No validation | JWT validation via UG |
| **User Resolution** | Token as ID only | Full user with roles/groups |
| **Permission System** | Basic only | Unified RBAC (creator + groups) |
| **Role Support** | No roles | 22 role types |
| **Group Permissions** | No groups | Hierarchical groups |
| **Creator Ownership** | Not implemented | Permanent ownership ✅ |
| **Auto RBAC Assignment** | Manual only | Auto-assigns ✅ |

#### Database Models

| Feature | Before | Now |
|---------|--------|-----|
| **Base Model Fields** | `id` only | `id`, `created`, `lastchange`, `createdby_id`, `changedby_id`, `rbacobject_id` |
| **Audit Timestamps** | Missing | Auto-managed ✅ |
| **User Tracking** | None | Creator & modifier ✅ |
| **RBAC Integration** | No `rbacobject_id` | Group-based access ✅ |
| **Optimistic Locking** | None | Via `lastchange` ✅ |

#### GraphQL Resolvers

| Feature | Before | Now |
|---------|--------|-----|
| **Authorization Pattern** | Permission classes | Extension pipeline ✅ |
| **Mutation Protection** | Basic | `create_unified_rbac_*_extensions()` ✅ |
| **Query Filtering** | No filtering | `filter_by_unified_permissions()` ✅ |
| **Error Handling** | Basic GraphQL errors | Typed union errors with UUIDs ✅ |

#### Context Structure

**Before:**
```python
{
    'request': FastAPI Request
    # Missing user data!
    # Missing auth header!
}
```

**Now:**
```python
{
    'request': FastAPI Request,
    'auth_header': 'Bearer <token>',
    'user': {
        'id': UUID,
        'fullname': str,
        'email': str,
        'roles': [...]
    },
    'ug_client': async function,
    'session': AsyncSession,
    'loaders': LoaderMap
}
```

---

## Migration Notes

### Key Changes Made

1. **BaseModel** - Added audit and RBAC fields
2. **main.py** - Enhanced context with UG integration
3. **authz_extensions.py** - Created authorization system
4. **error_codes.py** - Created error code registry
5. **All GraphQL models** - Updated with RBAC extensions

### Breaking Changes

- Manual `rbacobject_id` setting no longer allowed (auto-assigned)
- All mutations require authentication
- View-only roles cannot create/modify content
- Entities filtered by permissions in queries

### Migration Path

If upgrading from old version:

1. Run database migration for BaseModel fields
2. Update all entities to have `createdby_id` and `rbacobject_id`
3. Update client code to handle error unions
4. Update queries to expect filtered results
5. Update tests to use authenticated clients

---

## Additional Resources

- **[API_USAGE_GUIDE.md](../API_USAGE_GUIDE.md)** - How to use the API
- **[PROJECT_ANALYSIS.md](../PROJECT_ANALYSIS.md)** - Technical deep-dive
- **[TESTING_GUIDE.md](../TESTING_GUIDE.md)** - Testing guide
- **[TROUBLESHOOTING.md](../TROUBLESHOOTING.md)** - Common issues
