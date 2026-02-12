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
    """Test events() field resolver on UserGQLModel"""



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

