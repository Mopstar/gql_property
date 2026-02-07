"""
Tests for src/DBDefinitions/uuid.py module

Tests the UUID generation functionality used in database models.
"""

import pytest
from uuid import UUID
from src.DBDefinitions.uuid import uuid


class TestUUIDFunction:
    """Test uuid function from DBDefinitions"""

    def test_uuid_function_exists(self):
        """UUID function should be callable"""
        assert uuid is not None
        assert callable(uuid)

    def test_uuid_generates_valid_uuid(self):
        """UUID function should generate valid UUID objects"""
        result = uuid()
        assert result is not None
        assert isinstance(result, UUID)

    def test_uuid_generates_unique_values(self):
        """Each call should generate a different UUID"""
        uuid1 = uuid()
        uuid2 = uuid()
        uuid3 = uuid()

        assert uuid1 != uuid2
        assert uuid2 != uuid3
        assert uuid1 != uuid3

    def test_uuid_string_representation(self):
        """UUID should have valid string representation"""
        result = uuid()
        uuid_str = str(result)

        # Check UUID format (8-4-4-4-12)
        assert len(uuid_str) == 36  # Including hyphens
        parts = uuid_str.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12

    def test_uuid_version(self):
        """Generated UUID should be version 4 (random)"""
        result = uuid()
        assert result.version == 4

    def test_uuid_can_be_used_in_database_context(self):
        """UUID should be compatible with database usage"""
        result = uuid()

        # Should be convertible to string for DB storage
        str_repr = str(result)
        assert len(str_repr) > 0

        # Should be reconstructable from string
        reconstructed = UUID(str_repr)
        assert reconstructed == result

    def test_multiple_uuid_generations(self):
        """Generate multiple UUIDs to ensure consistency"""
        uuids = [uuid() for _ in range(100)]

        # All should be unique
        unique_uuids = set(uuids)
        assert len(unique_uuids) == 100

        # All should be valid UUIDs
        for u in uuids:
            assert isinstance(u, UUID)
            assert u.version == 4

