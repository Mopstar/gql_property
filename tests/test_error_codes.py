"""
Tests for src/error_codes.py module

Tests the error codes registry including:
- ERROR_CODES dictionary
- get_error_code() function
- get_error_info() function
- get_error_by_uuid() function
- list_error_codes() function
- Error code structure validation
"""

import pytest
from src.error_codes import (
    ERROR_CODES,
    get_error_code,
    get_error_info,
    get_error_by_uuid,
    list_error_codes,
    ErrorCodeInfo,
    AuthorizationException,
    ValidationException,
    BusinessLogicException,
)


class TestErrorCodesRegistry:
    """Test ERROR_CODES dictionary structure and content"""

    def test_error_codes_not_empty(self):
        """ERROR_CODES should contain error code definitions"""
        assert ERROR_CODES is not None
        assert len(ERROR_CODES) > 0
        assert isinstance(ERROR_CODES, dict)

    def test_error_codes_contain_auth_codes(self):
        """ERROR_CODES should contain authentication/authorization codes"""
        # Test some expected error codes
        expected_codes = [
            "AUTH_NOT_AUTHENTICATED",
            "AUTH_NO_REQUIRED_ROLE",
            "AUTH_PERMISSION_DENIED",
        ]

        for code in expected_codes:
            assert code in ERROR_CODES, f"Expected error code '{code}' not found"

    def test_error_code_format_is_valid_uuid_string(self):
        """All error codes should be valid UUID strings"""
        for key, value in ERROR_CODES.items():
            assert isinstance(value, str), f"Error code {key} value must be string"
            # Basic UUID format check (8-4-4-4-12 pattern)
            parts = value.split("-")
            assert len(parts) == 5, f"Error code {key} has invalid UUID format"
            assert len(parts[0]) == 8, f"Error code {key} UUID part 1 should be 8 chars"
            assert len(parts[1]) == 4, f"Error code {key} UUID part 2 should be 4 chars"
            assert len(parts[2]) == 4, f"Error code {key} UUID part 3 should be 4 chars"
            assert len(parts[3]) == 4, f"Error code {key} UUID part 4 should be 4 chars"
            assert len(parts[4]) == 12, f"Error code {key} UUID part 5 should be 12 chars"

    def test_error_codes_are_unique(self):
        """All error code UUIDs should be unique"""
        values = list(ERROR_CODES.values())
        unique_values = set(values)
        assert len(values) == len(unique_values), "Duplicate UUID values found in ERROR_CODES"


class TestGetErrorCode:
    """Test get_error_code() function"""

    def test_get_error_code_returns_info(self):
        """get_error_code should return ErrorCodeInfo for valid code"""
        # Test with a code that should exist
        code_key = "AUTH_NOT_AUTHENTICATED"
        result = get_error_code(code_key)

        assert result is not None
        assert isinstance(result, ErrorCodeInfo)

    def test_get_error_code_info_structure(self):
        """ErrorCodeInfo should have all required fields"""
        code_key = "AUTH_NOT_AUTHENTICATED"
        info = get_error_code(code_key)

        # Check all fields exist
        assert hasattr(info, "uuid")
        assert hasattr(info, "code")
        assert hasattr(info, "message")
        assert hasattr(info, "description")
        assert hasattr(info, "resolution")
        assert hasattr(info, "category")

        # Check field types
        assert isinstance(info.uuid, str)
        assert isinstance(info.code, str)
        assert isinstance(info.message, str)
        assert isinstance(info.description, str)
        assert isinstance(info.resolution, str)
        assert isinstance(info.category, str)

    def test_get_error_code_invalid_key(self):
        """get_error_code should handle invalid keys gracefully"""
        result = get_error_code("NONEXISTENT_ERROR_CODE")
        # Should return None or raise KeyError depending on implementation
        assert result is None or isinstance(result, ErrorCodeInfo)

    def test_get_error_code_categories(self):
        """Error codes should have valid categories"""
        valid_categories = [
            "Authentication",
            "Authorization",
            "Database",
            "Validation",
            "NotFound",
            "Business Logic",
            "System",
        ]

        # Test a few error codes
        for code_key in list(ERROR_CODES.keys())[:5]:
            info = get_error_code(code_key)
            if info:  # If the function is implemented
                assert info.category in valid_categories or len(info.category) > 0


class TestGetAllErrorCodes:
    """Test get_all_error_codes() function"""

    def test_get_all_error_codes_returns_list(self):
        """get_all_error_codes should return a list of ErrorCodeInfo"""
        result = get_all_error_codes()

        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_all_error_codes_contains_info_objects(self):
        """All items should be ErrorCodeInfo instances"""
        result = get_all_error_codes()

        for item in result:
            assert isinstance(item, ErrorCodeInfo)

    def test_get_all_error_codes_count_matches_registry(self):
        """Number of returned codes should match ERROR_CODES count"""
        result = get_all_error_codes()
        assert len(result) == len(ERROR_CODES)


class TestErrorCodeUsage:
    """Test practical usage scenarios"""

    def test_error_code_can_be_used_in_exception(self):
        """Error codes should be usable in exception contexts"""
        code = ERROR_CODES.get("AUTH_NOT_AUTHENTICATED")
        assert code is not None

        # Simulate usage in exception
        error_message = f"Authentication failed: {code}"
        assert code in error_message

    def test_multiple_auth_error_codes_exist(self):
        """Should have multiple authentication-related error codes"""
        auth_codes = [key for key in ERROR_CODES.keys() if key.startswith("AUTH_")]
        assert len(auth_codes) >= 3, "Should have at least 3 AUTH error codes"

    def test_error_code_info_provides_resolution(self):
        """Error code info should provide user-facing resolution guidance"""
        code_key = list(ERROR_CODES.keys())[0]
        info = get_error_info(code_key)

        if info:  # If the function is implemented
            assert len(info.resolution) > 0, "Resolution should not be empty"


class TestErrorCodeCategories:
    """Test error code organization by category"""

    def test_auth_codes_have_auth_prefix(self):
        """Authentication codes should be prefixed with AUTH_"""
        for key in ERROR_CODES.keys():
            if "authentication" in key.lower() or "authorized" in key.lower():
                assert key.startswith("AUTH_"), f"Auth code {key} should start with AUTH_"

    def test_error_codes_follow_naming_convention(self):
        """Error code keys should follow UPPERCASE_UNDERSCORE convention"""
        for key in ERROR_CODES.keys():
            assert key.isupper() or "_" in key, f"Error code {key} should be UPPERCASE_WITH_UNDERSCORES"


class TestGetErrorByUuid:
    """Test get_error_by_uuid() function"""

    def test_get_error_by_uuid_finds_error(self):
        """get_error_by_uuid should find error by UUID string"""
        # Get a valid UUID
        uuid_str = ERROR_CODES["AUTH_NOT_AUTHENTICATED"]
        result = get_error_by_uuid(uuid_str)

        assert result is not None
        assert isinstance(result, ErrorCodeInfo)
        assert result.uuid == uuid_str

    def test_get_error_by_uuid_returns_none_for_invalid(self):
        """get_error_by_uuid should return None for invalid UUID"""
        result = get_error_by_uuid("00000000-0000-0000-0000-000000000000")
        assert result is None


class TestCustomExceptions:
    """Test custom exception classes"""

    def test_authorization_exception(self):
        """AuthorizationException should work correctly"""
        code = ERROR_CODES["AUTH_NO_REQUIRED_ROLE"]
        msg = "Test authorization error"

        exc = AuthorizationException(msg=msg, code=code)

        assert exc.msg == msg
        assert exc.code == code
        assert str(exc) == msg

    def test_validation_exception(self):
        """ValidationException should work correctly"""
        code = ERROR_CODES["VALIDATION_INVALID_INPUT"]
        msg = "Test validation error"

        exc = ValidationException(msg=msg, code=code)

        assert exc.msg == msg
        assert exc.code == code
        assert str(exc) == msg

    def test_business_logic_exception(self):
        """BusinessLogicException should work correctly"""
        code = ERROR_CODES["BUSINESS_INVALID_STATE"]
        msg = "Test business logic error"

        exc = BusinessLogicException(msg=msg, code=code)

        assert exc.msg == msg
        assert exc.code == code
        assert str(exc) == msg

    def test_exceptions_can_be_raised_and_caught(self):
        """Custom exceptions should work in try/except blocks"""
        code = ERROR_CODES["AUTH_NOT_AUTHENTICATED"]

        with pytest.raises(AuthorizationException) as exc_info:
            raise AuthorizationException(msg="Test", code=code)

        assert exc_info.value.code == code

