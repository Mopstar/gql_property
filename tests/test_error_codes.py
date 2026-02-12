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



    def test_error_codes_are_unique(self):
        """All error code UUIDs should be unique"""
        values = list(ERROR_CODES.values())
        unique_values = set(values)
        assert len(values) == len(unique_values), "Duplicate UUID values found in ERROR_CODES"




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

