# Error Codes System Comparison

**Date:** February 7, 2026  
**Comparing:** GQL_Agreement_Valiasek vs gql_property

---

## Executive Summary

Both projects implement error code systems, but with significant differences in approach and maturity:

| Aspect | GQL_Agreement_Valiasek | gql_property | Can Be Transferred? |
|--------|------------------------|--------------|---------------------|
| **Error Code Format** | `E-AUTH-001` (prefix + category + number) | `f42da7e9...` (UUID strings) | ✅ YES - Either approach works |
| **Error Code Storage** | Dataclass with metadata | Dict + NamedTuple | ✅ YES - Similar patterns |
| **Integration with Extensions** | ✅ Fully integrated | ❌ Not integrated | ✅ YES - Can integrate |
| **Error Categories** | 7 categories, 24 codes | 6 categories, 17 codes | ✅ YES - Can expand |
| **Documentation** | Comprehensive MD file | Comprehensive MD file | ✅ YES - Both good |
| **Helper Functions** | `format_error_response()` | `get_error_info()`, `get_error_by_uuid()` | ✅ YES - Similar utility |
| **Usage in Resolvers** | ✅ Consistent usage | ❌ Inconsistent usage | ✅ YES - Need refactoring |

**Verdict:** ✅ **YES, the GQL_Agreement error code system can be brought over to gql_property with modifications.**

---

## Detailed Comparison

### 1. Error Code Format

#### GQL_Agreement_Valiasek Approach
```python
# Format: E-{CATEGORY}-{NUMBER}
"E-AUTH-001"    # Authentication error #1
"E-AUTHZ-002"   # Authorization error #2
"E-VAL-003"     # Validation error #3

@dataclass
class ErrorCode:
    code: str               # "E-AUTH-001"
    name: str              # "AUTH_NO_TOKEN"
    category: ErrorCategory # Enum
    message: str           # User-friendly message
    description: str       # Technical explanation
    resolution: str        # How to fix
```

**Pros:**
- Human-readable pattern
- Easy to categorize at a glance
- Shorter strings (11 chars vs 36 chars)
- Sortable alphabetically by category

**Cons:**
- Requires coordination to avoid number conflicts
- Manual numbering

#### gql_property Approach
```python
# Format: UUID strings
"f42da7e9-0b8b-4229-bc4b-c0dc73d55c3e"

class ErrorCodeInfo(NamedTuple):
    uuid: str               # Full UUID
    code: str              # "AUTH-002"
    message: str           # User-friendly message
    description: str       # Technical explanation
    resolution: str        # How to fix
    category: str          # String category
```

**Pros:**
- Globally unique, no conflicts possible
- Can generate programmatically
- No numbering coordination needed

**Cons:**
- Less human-readable
- Longer strings (36 characters)
- Harder to remember/type

---

### 2. Integration with RBAC Extensions

#### GQL_Agreement_Valiasek - FULLY INTEGRATED ✅

```python
# src/GraphTypeDefinitions/unified_rbac_extensions.py
from src.Utils.error_codes import ERROR_CODES

class UnifiedRbacAccessControlExtension(FieldExtension):
    async def resolve_async(self, next_, source, info, **kwargs):
        # ... authorization logic ...
        
        if not user_roles:
            error_code = ERROR_CODES["AUTHZ_ROLE_REQUIRED"]
            return self._return_error_or_raise(
                info, 
                message=f"[{error_code.code}] {error_code.message} (not creator and has no roles)", 
                code="NO_ROLES"
            )
        
        # ... more checks ...
        
        if not user_has_required_role:
            error_code = ERROR_CODES["AUTHZ_INSUFFICIENT_PERMISSIONS"]
            return self._return_error_or_raise(
                info,
                message=f"[{error_code.code}] {error_code.message} (required: {', '.join(self.required_roles)})",
                code="INSUFFICIENT_ROLE"
            )
```

**Benefits:**
- Consistent error messages across all resolvers
- Error codes included in response
- Easy to update error messages centrally
- Structured error responses

#### gql_property - NOT INTEGRATED ❌

```python
# src/GraphTypeDefinitions/authz_extensions.py
# NO import from src.error_codes

raise PermissionError(
    f"Permission denied. User '{user_fullname}' (ID: {user_id}) cannot create this entity. "
    f"Required roles: [{required_roles_str}]. "
    f"Your current roles: [{roles_str}]. "
    f"You need at least one of the required roles in a group to create content."
)
# ❌ No error code attached
# ❌ Message construction is ad-hoc
# ❌ No consistency across different errors
```

**Issues:**
- Error messages are ad-hoc strings
- No error codes in authorization failures
- Hard to track specific error types
- Inconsistent formatting

---

### 3. Error Categories

#### GQL_Agreement_Valiasek Categories

```python
class ErrorCategory(str, Enum):
    AUTHENTICATION = "AUTHENTICATION"       # 3 codes
    AUTHORIZATION = "AUTHORIZATION"         # 5 codes
    VALIDATION = "VALIDATION"               # 4 codes
    NOT_FOUND = "NOT_FOUND"                # 2 codes
    CONFLICT = "CONFLICT"                   # 3 codes
    DATABASE = "DATABASE"                   # 3 codes
    EXTERNAL_SERVICE = "EXTERNAL_SERVICE"   # 2 codes
    INTERNAL = "INTERNAL"                   # 3 codes

# Total: 24 error codes
```

#### gql_property Categories

```python
# Implicit categories (string-based, not Enum)
"Authentication"      # 1 code
"Authorization"       # 2 codes  
"Database"           # 3 codes
"Exception"          # 3 codes
"Concurrency"        # 1 code
"Business"           # 1 code
"Validation"         # 3 codes

# Total: 17 error codes (7 missing AUTH-002 details)
```

**Gap Analysis:**
- gql_property MISSING:
  - `NOT_FOUND` category (uses generic errors)
  - `EXTERNAL_SERVICE` category (no external service errors)
  - `INTERNAL` category (uses generic exceptions)
- gql_property HAS:
  - `Concurrency` category (optimistic locking)
  - Event-specific errors (invitation management)

---

### 4. Usage Patterns

#### GQL_Agreement_Valiasek - Consistent Usage

```python
# In extensions
error = ERROR_CODES["AUTHZ_INSUFFICIENT_PERMISSIONS"]
return UpdateError[AgreementGQLModel](
    msg=error.message,
    code=error.code
)

# In resolvers
error_response = format_error_response(
    "AUTHZ_ROLE_REQUIRED",
    details={
        "required_role": "editor",
        "user_role": "viewer",
        "entity_id": str(entity_id)
    }
)
return UpdateError[AgreementGQLModel](
    msg=error_response["message"],
    code=error_response["code"]
)
```

**Pattern:**
1. Import `ERROR_CODES` from central module
2. Lookup error by name
3. Use error code and message
4. Return structured error response

#### gql_property - Inconsistent Usage

```python
# Some resolvers use UUID codes (EventInvitation)
return UpdateError[EventInvitationGQLModel](
    msg="You are not authorized",
    code="48f0a626-f31a-4429-9e53-819ca865786d"
)

# Most resolvers DON'T use error codes
raise PermissionError(
    f"Permission denied. User '{user_fullname}'..."
)
# ❌ No code attached

# Generic uoishelpers errors
return InsertError[PurchaseGQLModel](
    msg="insert failed",
    code="ca8b4531-9419-4b87-badd-823d364f6c9b"
)
```

**Issues:**
- Hardcoded UUID strings in resolvers
- No import from `src/error_codes.py`
- Authorization errors don't include codes
- Inconsistent between different entity types

---

## Migration Path: Bringing Agreement's System to gql_property

### Phase 1: Decide on Error Code Format

**Option A: Keep UUIDs (Minimal Change)**
```python
# Keep existing UUID format
ERROR_CODES = {
    "AUTH_NO_REQUIRED_ROLE": "f42da7e9-0b8b-4229-bc4b-c0dc73d55c3e",
    # ... existing codes
}
```

**Option B: Switch to Agreement's Format (Breaking Change)**
```python
# Migrate to E-XXX-NNN format
ERROR_CODES = {
    "AUTH_NO_REQUIRED_ROLE": "E-AUTHZ-001",
    # ... all codes need new IDs
}
# ⚠️ Would break any clients parsing UUID codes
```

**Recommendation:** ✅ **Option A - Keep UUIDs**
- Less disruption
- No breaking changes for API consumers
- Can add human-readable codes as separate field

### Phase 2: Enhance ErrorCodeInfo Structure

**Current:**
```python
class ErrorCodeInfo(NamedTuple):
    uuid: str
    code: str          # "AUTH-002"
    message: str
    description: str
    resolution: str
    category: str      # Plain string
```

**Enhanced (Agreement-style):**
```python
from enum import Enum

class ErrorCategory(str, Enum):
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    VALIDATION = "VALIDATION"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    DATABASE = "DATABASE"
    BUSINESS = "BUSINESS"
    CONCURRENCY = "CONCURRENCY"
    INTERNAL = "INTERNAL"

@dataclass
class ErrorCode:
    """Error code definition with full metadata."""
    uuid: str           # Keep existing UUIDs
    code: str          # "E-AUTHZ-001" style code
    name: str          # "AUTH_NO_REQUIRED_ROLE"
    category: ErrorCategory  # Enum instead of string
    message: str       # User-friendly message
    description: str   # Technical explanation
    resolution: str    # How to fix
```

### Phase 3: Add Helper Functions (from Agreement)

```python
def format_error_response(
    error_name: str, 
    details: Optional[Dict] = None,
    custom_message: Optional[str] = None
) -> Dict:
    """Format standardized error response.
    
    Args:
        error_name: Name of error code (e.g., "AUTH_NO_REQUIRED_ROLE")
        details: Additional context/details dictionary
        custom_message: Optional custom message to override default
        
    Returns:
        Formatted error response dictionary
    """
    error = ERROR_CODES_DETAIL.get(error_name)
    if not error:
        error = ERROR_CODES_DETAIL["INT_UNEXPECTED_ERROR"]
        details = {**(details or {}), "original_error_name": error_name}
    
    return {
        "uuid": error.uuid,        # Keep UUID for compatibility
        "code": error.code,        # Human-readable code
        "name": error.name,
        "category": error.category.value,
        "message": custom_message or error.message,
        "details": details or {},
        "resolution": error.resolution
    }
```

### Phase 4: Integrate with authz_extensions.py

**Current (no integration):**
```python
# src/GraphTypeDefinitions/authz_extensions.py
raise PermissionError(
    f"Permission denied. User '{user_fullname}' (ID: {user_id}) cannot create this entity. "
    f"Required roles: [{required_roles_str}]. Your current roles: [{roles_str}]."
)
```

**Migrated (integrated):**
```python
# src/GraphTypeDefinitions/authz_extensions.py
from src.error_codes import ERROR_CODES, ERROR_CODE_DETAILS, format_error_response

class AutoRbacAssignmentExtension(FieldExtension):
    async def resolve_async(self, next_, source, info, **kwargs):
        # ... logic ...
        
        if not write_groups:
            error = ERROR_CODE_DETAILS["AUTH_NO_REQUIRED_ROLE"]
            error_response = format_error_response(
                "AUTH_NO_REQUIRED_ROLE",
                details={
                    "user_id": str(user_id),
                    "user_fullname": user_fullname,
                    "required_roles": self.required_roles[:5],
                    "current_roles": all_user_roles
                }
            )
            raise PermissionError(
                f"[{error.code}] {error_response['message']}: {error_response['details']}"
            )
```

### Phase 5: Extend Error Coverage

**Missing Error Codes to Add:**

```python
# NOT_FOUND category
"NF_ENTITY_NOT_FOUND": ErrorCode(
    uuid="<new-uuid>",
    code="E-NF-001",
    name="NF_ENTITY_NOT_FOUND",
    category=ErrorCategory.NOT_FOUND,
    message="Entity not found",
    description="Requested entity ID doesn't exist in database",
    resolution="Verify entity ID is correct and entity hasn't been deleted"
),

"NF_PARENT_NOT_FOUND": ErrorCode(
    uuid="<new-uuid>",
    code="E-NF-002",
    name="NF_PARENT_NOT_FOUND",
    category=ErrorCategory.NOT_FOUND,
    message="Parent entity not found",
    description="Cannot operate on child entity - parent doesn't exist",
    resolution="Ensure parent entity exists before creating/updating child"
),

# INTERNAL category
"INT_UNEXPECTED_ERROR": ErrorCode(
    uuid="<new-uuid>",
    code="E-INT-001",
    name="INT_UNEXPECTED_ERROR",
    category=ErrorCategory.INTERNAL,
    message="Unexpected internal error occurred",
    description="Unhandled exception or unexpected system state",
    resolution="Contact administrator with error details and timestamp"
),
```

---

## Implementation Checklist

### ✅ Already Done in gql_property
- [x] `src/error_codes.py` exists with error definitions
- [x] `ERROR_CODES.md` documentation exists
- [x] Some resolvers use error codes (EventInvitation)
- [x] ErrorCodeInfo structure with metadata
- [x] Helper functions (`get_error_info`, `get_error_by_uuid`)

### ❌ Needs to Be Done (Migration Tasks)

#### High Priority
- [ ] **Integrate error codes into `authz_extensions.py`**
  - Import ERROR_CODES and ERROR_CODE_DETAILS
  - Replace PermissionError strings with error code lookups
  - Use format_error_response() for consistent messages
  
- [ ] **Add format_error_response() helper function**
  - Port from Agreement project
  - Adapt for UUID format
  
- [ ] **Change ErrorCategory from string to Enum**
  - Create ErrorCategory enum
  - Update all ErrorCodeInfo definitions
  - Update helper functions

#### Medium Priority
- [ ] **Add missing error codes**
  - NOT_FOUND category (2 codes)
  - INTERNAL category (3 codes)
  - More specific authorization codes
  
- [ ] **Update custom exceptions**
  - Make AuthorizationException use error codes
  - Add code parameter to all custom exceptions
  
- [ ] **Standardize resolver error usage**
  - Update PurchaseGQLModel mutations
  - Update PropertyGQLModel mutations
  - Update all other entity resolvers

#### Low Priority
- [ ] **Add error code tests**
  - Test each error code can be retrieved
  - Test format_error_response()
  - Test authorization errors include codes
  
- [ ] **Generate error code documentation**
  - Auto-generate from ERROR_CODE_DETAILS
  - Keep ERROR_CODES.md in sync

---

## Code Examples: Before & After

### Example 1: Authorization Error in Insert

**Before (current gql_property):**
```python
raise PermissionError(
    f"Permission denied. User '{user_fullname}' (ID: {user_id}) cannot create this entity. "
    f"Required roles: [{required_roles_str}]. "
    f"Your current roles: [{roles_str}]. "
    f"You need at least one of the required roles in a group to create content."
)
```

**After (integrated with error codes):**
```python
from src.error_codes import ERROR_CODE_DETAILS, format_error_response

error_response = format_error_response(
    "AUTH_NO_REQUIRED_ROLE",
    details={
        "user_id": str(user_id),
        "user_fullname": user_fullname,
        "required_roles": self.required_roles[:5],
        "current_roles": all_user_roles
    }
)

raise PermissionError(
    f"[{error_response['code']}] {error_response['message']}"
)
# Error will include UUID in exception for tracking
```

### Example 2: Update Permission Check

**Before:**
```python
raise PermissionError(
    f"Permission denied for {user_fullname}. You must be the creator or have one of these roles "
    f"[{', '.join(self.required_roles)}] in the entity's group."
)
```

**After:**
```python
error_response = format_error_response(
    "AUTH_NOT_CREATOR_OR_EDITOR",
    details={
        "user_id": str(user_id),
        "user_fullname": user_fullname,
        "entity_id": str(db_row.id),
        "entity_group": str(rbacobject_id),
        "required_roles": self.required_roles
    }
)

raise PermissionError(
    f"[{error_response['code']}] {error_response['message']}"
)
```

### Example 3: Return Mutation Error with Code

**Before:**
```python
return UpdateError[PurchaseGQLModel](
    msg="You are not authorized",
    code="48f0a626-f31a-4429-9e53-819ca865786d"  # Hardcoded UUID
)
```

**After:**
```python
from src.error_codes import ERROR_CODES, ERROR_CODE_DETAILS

error = ERROR_CODE_DETAILS["UPDATE_NOT_AUTHORIZED"]
return UpdateError[PurchaseGQLModel](
    msg=error.message,
    code=ERROR_CODES["UPDATE_NOT_AUTHORIZED"]  # Centralized UUID
)
```

---

## Benefits of Migration

### 1. **Consistency Across Project**
- All errors follow same pattern
- Easy to understand error responses
- Predictable error handling for clients

### 2. **Maintainability**
- Centralized error definitions
- Change message once, updates everywhere
- Easy to add new error codes

### 3. **Debugging & Monitoring**
- Track specific error types by code
- Filter logs by error category
- Identify authorization vs validation issues quickly

### 4. **Documentation**
- Auto-generated error catalogs
- Clear resolution steps for users
- API documentation includes error codes

### 5. **Client Experience**
- Consistent error format
- Machine-readable error codes (UUID)
- Human-readable error codes (E-XXX-NNN)
- Clear guidance on how to fix issues

---

## Recommendation

✅ **YES - Migrate GQL_Agreement's error code system to gql_property**

**Approach:**
1. Keep existing UUID format (no breaking changes)
2. Add Agreement's helper functions and structure
3. Convert ErrorCategory to Enum
4. Integrate with authz_extensions.py (HIGH PRIORITY)
5. Gradually update all resolvers to use error codes
6. Add missing error code categories
7. Expand test coverage for error codes

**Estimated Effort:**
- Phase 1-3 (Structure): 2-3 hours
- Phase 4 (Integration): 3-4 hours
- Phase 5 (Coverage): 2-3 hours
- Testing: 2-3 hours

**Total: ~10-15 hours of development**

**Impact:**
- ✅ Significantly improves error handling consistency
- ✅ Better debugging and monitoring capabilities
- ✅ Improved API documentation
- ✅ Better client experience
- ⚠️ No breaking changes if done correctly
- ⚠️ Requires updating all resolvers over time

---

## Next Steps

1. **Review this comparison** with team/stakeholders
2. **Decide on migration approach** (recommended: incremental)
3. **Start with Phase 1-3** (structure improvements)
4. **Prioritize authz_extensions.py integration** (Phase 4)
5. **Gradually update resolvers** as you work on them
6. **Add tests** for error code coverage
7. **Update documentation** as you go

Would you like me to start implementing any of these phases?

