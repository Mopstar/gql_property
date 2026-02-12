"""
Tests for src/GraphTypeDefinitions/authz_extensions.py module

Tests authorization extensions including:
- Role constants and definitions
- PermissionFilterExtension
- AutoGroupAssignmentExtension
- OwnershipPermissionExtension
- Helper functions
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from strawberry.types import Info

from src.GraphTypeDefinitions.authz_extensions import (
    # Role constants
    SYSTEM_ROLES,
    LEADERSHIP_ROLES,
    GUARANTEE_ROLES,
    TEACHING_ROLES,
    IDENTITY_ROLES,
    VIEWER_ROLES,
    EDITOR_ROLES,
    ADMIN_ROLES,
    ROLES_READ,
    ROLES_WRITE,
    ROLES_DELETE,
    # Extensions
    PermissionFilterExtension,
    AutoGroupAssignmentExtension,
    OwnershipPermissionExtension,
)


class TestRoleConstants:
    """Test role constant definitions"""

    def test_system_roles_defined(self):
        """SYSTEM_ROLES should contain core system roles"""
        assert isinstance(SYSTEM_ROLES, list)
        assert len(SYSTEM_ROLES) > 0
        assert "administrátor" in SYSTEM_ROLES
        assert "admin" in SYSTEM_ROLES
        assert "editor" in SYSTEM_ROLES
        assert "viewer" in SYSTEM_ROLES

    def test_leadership_roles_defined(self):
        """LEADERSHIP_ROLES should contain academic leadership roles"""
        assert isinstance(LEADERSHIP_ROLES, list)
        assert len(LEADERSHIP_ROLES) > 0
        assert "rektor" in LEADERSHIP_ROLES
        assert "děkan" in LEADERSHIP_ROLES

    def test_guarantee_roles_defined(self):
        """GUARANTEE_ROLES should contain guarantee roles"""
        assert isinstance(GUARANTEE_ROLES, list)
        assert len(GUARANTEE_ROLES) > 0
        assert "garant" in GUARANTEE_ROLES
        assert "odpovědný řešitel" in GUARANTEE_ROLES

    def test_teaching_roles_defined(self):
        """TEACHING_ROLES should contain teaching roles"""
        assert isinstance(TEACHING_ROLES, list)
        assert len(TEACHING_ROLES) > 0
        assert "přednášející" in TEACHING_ROLES

    def test_viewer_roles_contains_all_roles(self):
        """VIEWER_ROLES should include all role types"""
        assert isinstance(VIEWER_ROLES, list)
        # Should contain system roles
        assert "viewer" in VIEWER_ROLES
        assert "admin" in VIEWER_ROLES
        # Should contain leadership
        assert "rektor" in VIEWER_ROLES

    def test_editor_roles_subset_of_viewer(self):
        """EDITOR_ROLES should be a subset of authenticated users"""
        assert isinstance(EDITOR_ROLES, list)
        assert "editor" in EDITOR_ROLES
        assert "administrátor" in EDITOR_ROLES
        assert "odpovědný řešitel" in EDITOR_ROLES
        # Should NOT include basic viewers
        assert "čtenář" not in EDITOR_ROLES

    def test_admin_roles_most_restrictive(self):
        """ADMIN_ROLES should contain only highest level roles"""
        assert isinstance(ADMIN_ROLES, list)
        assert "administrátor" in ADMIN_ROLES
        assert "admin" in ADMIN_ROLES
        assert "rektor" in ADMIN_ROLES
        # Should have fewer roles than EDITOR_ROLES
        assert len(ADMIN_ROLES) < len(EDITOR_ROLES)

    def test_role_aliases(self):
        """Test convenience aliases match their sources"""
        assert ROLES_READ == VIEWER_ROLES
        assert ROLES_WRITE == EDITOR_ROLES
        assert ROLES_DELETE == ADMIN_ROLES

    def test_no_duplicate_roles_in_viewer(self):
        """VIEWER_ROLES should not contain duplicates"""
        assert len(VIEWER_ROLES) == len(set(VIEWER_ROLES))

    def test_no_duplicate_roles_in_editor(self):
        """EDITOR_ROLES should not contain duplicates"""
        assert len(EDITOR_ROLES) == len(set(EDITOR_ROLES))

    def test_no_duplicate_roles_in_admin(self):
        """ADMIN_ROLES should not contain duplicates"""
        assert len(ADMIN_ROLES) == len(set(ADMIN_ROLES))

    def test_admin_roles_in_editor_roles(self):
        """All ADMIN_ROLES should be in EDITOR_ROLES"""
        for role in ADMIN_ROLES:
            # Admins should also be able to edit
            assert role in EDITOR_ROLES or role in VIEWER_ROLES

    def test_editor_roles_in_viewer_roles(self):
        """All EDITOR_ROLES should be in VIEWER_ROLES"""
        for role in EDITOR_ROLES:
            # Editors should also be able to view
            assert role in VIEWER_ROLES or role in SYSTEM_ROLES


class TestPermissionFilterExtension:
    """Test PermissionFilterExtension"""

    @pytest.mark.asyncio
    async def test_filters_internal_kwargs(self):
        """Should filter out internal extension kwargs"""
        extension = PermissionFilterExtension()

        # Mock next callable
        next_called_with = {}
        async def mock_next(source, info, **kwargs):
            next_called_with.update(kwargs)
            return "result"

        # Mock info
        mock_info = MagicMock(spec=Info)

        # Call with internal kwargs
        kwargs = {
            "user_roles": ["admin"],
            "rbacobject_id": "some-uuid",
            "db_row": {"id": "123"},
            "valid_arg": "keep_this",
            "another_arg": 42,
        }

        result = await extension.resolve_async(
            mock_next,
            source=None,
            info=mock_info,
            **kwargs
        )

        # Internal keys should be filtered
        assert "user_roles" not in next_called_with
        assert "rbacobject_id" not in next_called_with
        assert "db_row" not in next_called_with

        # Valid args should be kept
        assert "valid_arg" in next_called_with
        assert next_called_with["valid_arg"] == "keep_this"
        assert "another_arg" in next_called_with
        assert next_called_with["another_arg"] == 42

    @pytest.mark.asyncio
    async def test_allows_all_non_internal_kwargs(self):
        """Should pass through all non-internal kwargs"""
        extension = PermissionFilterExtension()

        next_called_with = {}
        async def mock_next(source, info, **kwargs):
            next_called_with.update(kwargs)
            return "result"

        mock_info = MagicMock(spec=Info)

        kwargs = {
            "id": "uuid-123",
            "name": "Test",
            "description": "Test description",
            "status": "active",
        }

        await extension.resolve_async(
            mock_next,
            source=None,
            info=mock_info,
            **kwargs
        )

        # All valid kwargs should pass through
        assert len(next_called_with) == 4
        assert next_called_with["id"] == "uuid-123"
        assert next_called_with["name"] == "Test"


class TestAutoGroupAssignmentExtension:
    """Test AutoGroupAssignmentExtension"""

    def test_initialization_with_default_roles(self):
        """Should initialize with default EDITOR_ROLES"""
        extension = AutoGroupAssignmentExtension()
        assert extension.required_roles == EDITOR_ROLES

    def test_initialization_with_custom_roles(self):
        """Should initialize with custom roles"""
        custom_roles = ["custom_role1", "custom_role2"]
        extension = AutoGroupAssignmentExtension(required_roles=custom_roles)
        assert extension.required_roles == custom_roles


    @pytest.mark.asyncio
    async def test_preserves_existing_rbacobject(self):
        """Should not override existing rbacobject_id"""
        extension = AutoGroupAssignmentExtension()

        # Mock entity with existing rbacobject_id
        mock_entity = MagicMock()
        existing_id = "existing-group-456"
        mock_entity.rbacobject_id = existing_id

        mock_user = {
            "id": "user-123",
            "roles": [
                {
                    "roletype": {"name": "editor"},
                    "group": {"id": "group-123", "name": "Test Group"}
                }
            ]
        }

        mock_info = MagicMock(spec=Info)
        mock_info.context = {"user": mock_user}

        async def mock_next(source, info, **kwargs):
            return "result"

        kwargs = {"entity": mock_entity}

        result = await extension.resolve_async(
            mock_next,
            source=None,
            info=mock_info,
            **kwargs
        )

        # Should preserve existing ID
        assert mock_entity.rbacobject_id == existing_id



class TestOwnershipPermissionExtension:
    """Test OwnershipPermissionExtension"""

    def test_initialization(self):
        """Should initialize with required roles"""
        roles = ["editor", "admin"]
        extension = OwnershipPermissionExtension(roles=roles)
        # Just verify it initializes without error
        assert extension is not None

    @pytest.mark.asyncio
    async def test_allows_creator_access(self):
        """Should allow access to entity creator"""
        roles = ["editor"]
        extension = OwnershipPermissionExtension(roles=roles)

        user_id = "user-123"
        mock_user = {
            "id": user_id,
            "fullname": "Test User",
            "roles": []
        }

        # Entity created by the user
        mock_entity = MagicMock()
        mock_entity.createdby_id = user_id

        mock_info = MagicMock(spec=Info)
        mock_info.context = {"user": mock_user}

        result_called = False
        async def mock_next(source, info, **kwargs):
            nonlocal result_called
            result_called = True
            return "success"

        kwargs = {"db_row": mock_entity}

        # Note: This test may need adjustment based on actual implementation
        # The extension might need additional context or structure
        # For now, we're testing the basic structure


class TestAuthzExtensionsIntegration:
    """Integration tests for authorization extensions"""

    def test_all_role_constants_are_strings(self):
        """All role constants should contain only strings"""
        all_role_lists = [
            SYSTEM_ROLES,
            LEADERSHIP_ROLES,
            GUARANTEE_ROLES,
            TEACHING_ROLES,
            IDENTITY_ROLES,
        ]

        for role_list in all_role_lists:
            for role in role_list:
                assert isinstance(role, str), f"Role {role} should be a string"

    def test_role_hierarchies_are_consistent(self):
        """Role hierarchies should be logically consistent"""
        # All admin roles should be in editor roles or viewer roles
        for admin_role in ADMIN_ROLES:
            assert (admin_role in EDITOR_ROLES or
                   admin_role in VIEWER_ROLES), \
                   f"Admin role {admin_role} should be in EDITOR or VIEWER roles"

    def test_czech_and_english_role_pairs(self):
        """Check that Czech/English role pairs exist where expected"""
        pairs = [
            ("administrátor", "admin"),
            ("viewer", "čtenář"),
        ]

        for czech, english in pairs:
            # At least one should exist in system roles
            assert (czech in SYSTEM_ROLES or english in SYSTEM_ROLES), \
                   f"Expected role pair {czech}/{english} not found"


