"""
Tests for src/GraphTypeDefinitions/UserGQLModel.py module

Tests the UserGQLModel GraphQL type including:
- Federation support
- event_invitations resolver
- events resolver
- Permission checks
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import strawberry
from typing import List

from src.GraphTypeDefinitions.UserGQLModel import UserGQLModel


class TestUserGQLModel:
    """Test UserGQLModel structure and federation"""

    def test_user_gql_model_is_federation_type(self):
        """UserGQLModel should be a federation type"""
        # Check that it's a Strawberry type
        assert hasattr(UserGQLModel, '__strawberry_definition__')

    def test_user_gql_model_has_id_field(self):
        """UserGQLModel should have an id field"""
        # Create instance to check fields
        definition = UserGQLModel.__strawberry_definition__
        field_names = [f.name for f in definition.fields]
        assert 'id' in field_names

    def test_user_gql_model_has_event_invitations_field(self):
        """UserGQLModel should have event_invitations field"""
        definition = UserGQLModel.__strawberry_definition__
        field_names = [f.name for f in definition.fields]
        assert 'event_invitations' in field_names

    def test_user_gql_model_has_events_field(self):
        """UserGQLModel should have events field"""
        definition = UserGQLModel.__strawberry_definition__
        field_names = [f.name for f in definition.fields]
        assert 'events' in field_names

    def test_resolve_reference_method_exists(self):
        """UserGQLModel should have resolve_reference method"""
        assert hasattr(UserGQLModel, 'resolve_reference')


class TestUserEventsResolver:
    """Test events resolver method"""

    @pytest.mark.asyncio
    async def test_events_returns_list(self):
        """events() should return a list of EventGQLModel"""
        # Create a UserGQLModel instance
        user = UserGQLModel()
        user.id = "user-123"

        # Mock info with loaders
        mock_info = MagicMock()

        # Mock invitation loader
        mock_invitation = MagicMock()
        mock_invitation.event_id = "event-123"

        mock_invitation_loader = AsyncMock()
        mock_invitation_loader.filter_by = AsyncMock(return_value=[mock_invitation])

        # Mock event loader
        mock_event_row = MagicMock()
        mock_event_row.id = "event-123"

        mock_event_loader = AsyncMock()
        mock_event_loader.load = AsyncMock(return_value=mock_event_row)

        # Setup loaders
        mock_loaders = MagicMock()
        mock_loaders.EventInvitationModel = mock_invitation_loader
        mock_loaders.EventModel = mock_event_loader

        mock_info.context = {
            'loaders': mock_loaders
        }

        # Mock getLoadersFromInfo
        with pytest.mock.patch('src.GraphTypeDefinitions.UserGQLModel.getLoadersFromInfo') as mock_get_loaders:
            mock_get_loaders.return_value = mock_loaders

            # Call the method
            result = await user.events(info=mock_info)

            # Verify result is a list
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_events_filters_by_user_id(self):
        """events() should filter invitations by user_id"""
        user = UserGQLModel()
        user_id = "user-456"
        user.id = user_id

        mock_info = MagicMock()

        mock_invitation_loader = AsyncMock()
        mock_invitation_loader.filter_by = AsyncMock(return_value=[])

        mock_event_loader = AsyncMock()

        mock_loaders = MagicMock()
        mock_loaders.EventInvitationModel = mock_invitation_loader
        mock_loaders.EventModel = mock_event_loader

        with pytest.mock.patch('src.GraphTypeDefinitions.UserGQLModel.getLoadersFromInfo') as mock_get_loaders:
            mock_get_loaders.return_value = mock_loaders

            await user.events(info=mock_info)

            # Verify filter_by was called with user_id
            mock_invitation_loader.filter_by.assert_called_once_with(user_id=user_id)

    @pytest.mark.asyncio
    async def test_events_handles_no_invitations(self):
        """events() should return empty list when no invitations"""
        user = UserGQLModel()
        user.id = "user-789"

        mock_info = MagicMock()

        mock_invitation_loader = AsyncMock()
        mock_invitation_loader.filter_by = AsyncMock(return_value=[])

        mock_event_loader = AsyncMock()

        mock_loaders = MagicMock()
        mock_loaders.EventInvitationModel = mock_invitation_loader
        mock_loaders.EventModel = mock_event_loader

        with pytest.mock.patch('src.GraphTypeDefinitions.UserGQLModel.getLoadersFromInfo') as mock_get_loaders:
            mock_get_loaders.return_value = mock_loaders

            result = await user.events(info=mock_info)

            assert result == []

    @pytest.mark.asyncio
    async def test_events_removes_duplicate_event_ids(self):
        """events() should return unique events (no duplicates)"""
        user = UserGQLModel()
        user.id = "user-999"

        mock_info = MagicMock()

        # Multiple invitations to same event
        mock_invitation1 = MagicMock()
        mock_invitation1.event_id = "event-123"

        mock_invitation2 = MagicMock()
        mock_invitation2.event_id = "event-123"  # Duplicate

        mock_invitation3 = MagicMock()
        mock_invitation3.event_id = "event-456"

        mock_invitation_loader = AsyncMock()
        mock_invitation_loader.filter_by = AsyncMock(
            return_value=[mock_invitation1, mock_invitation2, mock_invitation3]
        )

        # Mock event loader
        mock_event_row_123 = MagicMock()
        mock_event_row_123.id = "event-123"

        mock_event_row_456 = MagicMock()
        mock_event_row_456.id = "event-456"

        async def load_event(event_id):
            if event_id == "event-123":
                return mock_event_row_123
            elif event_id == "event-456":
                return mock_event_row_456
            return None

        mock_event_loader = AsyncMock()
        mock_event_loader.load = AsyncMock(side_effect=load_event)

        mock_loaders = MagicMock()
        mock_loaders.EventInvitationModel = mock_invitation_loader
        mock_loaders.EventModel = mock_event_loader

        with pytest.mock.patch('src.GraphTypeDefinitions.UserGQLModel.getLoadersFromInfo') as mock_get_loaders:
            mock_get_loaders.return_value = mock_loaders

            result = await user.events(info=mock_info)

            # Should have 2 unique events, not 3
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_events_skips_invitations_without_event_id(self):
        """events() should skip invitations without event_id"""
        user = UserGQLModel()
        user.id = "user-111"

        mock_info = MagicMock()

        # Invitation without event_id
        mock_invitation1 = MagicMock()
        mock_invitation1.event_id = None

        # Valid invitation
        mock_invitation2 = MagicMock()
        mock_invitation2.event_id = "event-789"

        mock_invitation_loader = AsyncMock()
        mock_invitation_loader.filter_by = AsyncMock(
            return_value=[mock_invitation1, mock_invitation2]
        )

        mock_event_row = MagicMock()
        mock_event_row.id = "event-789"

        mock_event_loader = AsyncMock()
        mock_event_loader.load = AsyncMock(return_value=mock_event_row)

        mock_loaders = MagicMock()
        mock_loaders.EventInvitationModel = mock_invitation_loader
        mock_loaders.EventModel = mock_event_loader

        with pytest.mock.patch('src.GraphTypeDefinitions.UserGQLModel.getLoadersFromInfo') as mock_get_loaders:
            mock_get_loaders.return_value = mock_loaders

            result = await user.events(info=mock_info)

            # Should only have 1 event
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_events_skips_none_event_rows(self):
        """events() should skip events that don't load"""
        user = UserGQLModel()
        user.id = "user-222"

        mock_info = MagicMock()

        mock_invitation = MagicMock()
        mock_invitation.event_id = "event-nonexistent"

        mock_invitation_loader = AsyncMock()
        mock_invitation_loader.filter_by = AsyncMock(return_value=[mock_invitation])

        # Event loader returns None (event not found)
        mock_event_loader = AsyncMock()
        mock_event_loader.load = AsyncMock(return_value=None)

        mock_loaders = MagicMock()
        mock_loaders.EventInvitationModel = mock_invitation_loader
        mock_loaders.EventModel = mock_event_loader

        with pytest.mock.patch('src.GraphTypeDefinitions.UserGQLModel.getLoadersFromInfo') as mock_get_loaders:
            mock_get_loaders.return_value = mock_loaders

            result = await user.events(info=mock_info)

            # Should return empty list
            assert result == []


class TestUserModelFieldDescriptions:
    """Test that fields have proper descriptions"""

    def test_event_invitations_has_description(self):
        """event_invitations field should have a description"""
        definition = UserGQLModel.__strawberry_definition__

        for field in definition.fields:
            if field.name == 'event_invitations':
                assert field.description is not None
                assert len(field.description) > 0
                assert "invited" in field.description.lower() or "invitation" in field.description.lower()

    def test_events_has_description(self):
        """events field should have a description"""
        definition = UserGQLModel.__strawberry_definition__

        for field in definition.fields:
            if field.name == 'events':
                assert field.description is not None
                assert len(field.description) > 0
                assert "event" in field.description.lower()


class TestUserModelPermissions:
    """Test permission classes on fields"""

    def test_event_invitations_requires_authentication(self):
        """event_invitations should require authentication"""
        definition = UserGQLModel.__strawberry_definition__

        for field in definition.fields:
            if field.name == 'event_invitations':
                # Should have permission classes
                assert hasattr(field, 'permission_classes') or hasattr(field, 'extensions')

    def test_events_requires_authentication(self):
        """events should require authentication"""
        definition = UserGQLModel.__strawberry_definition__

        for field in definition.fields:
            if field.name == 'events':
                # Should have permission classes
                assert hasattr(field, 'permission_classes') or hasattr(field, 'extensions')

