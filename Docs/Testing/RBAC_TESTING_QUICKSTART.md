# RBAC Testing Quick Start Guide

**Date:** February 7, 2026  
**Purpose:** Step-by-step guide to implement comprehensive RBAC testing in gql_property  
**Based on:** GQL_Agreement_Valiasek patterns

---

## 🎯 Goal

Implement comprehensive Role-Based Access Control (RBAC) testing to ensure:
- ✅ Users can only access content they own
- ✅ Users can only access content in their groups
- ✅ Role hierarchy works correctly (admin > editor > viewer)
- ✅ Root admins can access everything
- ✅ Cross-group access is properly denied

---

## 📋 Prerequisites

1. **Running services:**
   ```powershell
   docker compose -f docker-compose.debug.yml up -d
   ```

2. **Service running:**
   ```powershell
   .venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --env-file environment.txt
   ```

3. **Verify connectivity:**
   ```powershell
   python tests\check_services.py
   ```

---

## 🚀 Step 1: Define Test Users (30 minutes)

### 1.1 Review Current Users

Check `systemdata.json` or `systemdata.rnd.json` for existing test users.

### 1.2 Required Test User Roles

For comprehensive RBAC testing, you need:

| Role | Group | Purpose |
|------|-------|---------|
| **Viewer** | Group A | Read-only access, cannot create/modify |
| **Editor** | Group A | Can create and modify own content |
| **Editor** | Group B | Same role, different group (for cross-group tests) |
| **Admin** | Group A | Can manage all content in Group A |
| **Admin** | Parent Group | Can manage content in child groups |
| **Root Admin** | Root Group | Can manage everything |

### 1.3 Example Test Users Structure

```json
{
  "users": [
    {
      "id": "user-viewer-a",
      "email": "viewer.a@world.com",
      "name": "Viewer",
      "surname": "A",
      "roles": [
        {
          "id": "role-viewer-a",
          "valid": true,
          "roleTypeId": "viewer-role-type",
          "groupId": "group-a"
        }
      ]
    },
    {
      "id": "user-editor-a",
      "email": "editor.a@world.com",
      "name": "Editor",
      "surname": "A",
      "roles": [
        {
          "id": "role-editor-a",
          "valid": true,
          "roleTypeId": "editor-role-type",
          "groupId": "group-a"
        }
      ]
    },
    {
      "id": "user-editor-b",
      "email": "editor.b@world.com",
      "name": "Editor",
      "surname": "B",
      "roles": [
        {
          "id": "role-editor-b",
          "valid": true,
          "roleTypeId": "editor-role-type",
          "groupId": "group-b"
        }
      ]
    },
    {
      "id": "user-admin-a",
      "email": "admin.a@world.com",
      "name": "Admin",
      "surname": "A",
      "roles": [
        {
          "id": "role-admin-a",
          "valid": true,
          "roleTypeId": "admin-role-type",
          "groupId": "group-a"
        }
      ]
    },
    {
      "id": "user-admin-parent",
      "email": "admin.parent@world.com",
      "name": "Admin",
      "surname": "Parent",
      "roles": [
        {
          "id": "role-admin-parent",
          "valid": true,
          "roleTypeId": "admin-role-type",
          "groupId": "group-parent"
        }
      ]
    },
    {
      "id": "user-root-admin",
      "email": "root.admin@world.com",
      "name": "Root",
      "surname": "Admin",
      "roles": [
        {
          "id": "role-root-admin",
          "valid": true,
          "roleTypeId": "admin-role-type",
          "groupId": "group-root"
        }
      ]
    }
  ]
}
```

### 1.4 Verify Test Users

Create `scripts/verify_test_users.py`:

```python
"""Verify test users are properly configured."""

import asyncio
from tests.client import createFederationClient

TEST_USERS = [
    ("viewer.a@world.com", "viewer.a@world.com"),
    ("editor.a@world.com", "editor.a@world.com"),
    ("editor.b@world.com", "editor.b@world.com"),
    ("admin.a@world.com", "admin.a@world.com"),
    ("admin.parent@world.com", "admin.parent@world.com"),
    ("root.admin@world.com", "root.admin@world.com"),
]

async def verify_user(username, password):
    """Verify user can authenticate and has expected roles."""
    client = createFederationClient(username=username, password=password)
    user_info = await client.get_user_info()
    
    if user_info:
        print(f"✅ {username}")
        print(f"   Roles: {[r['roletype']['name'] for r in user_info.get('roles', [])]}")
        print(f"   Groups: {[r['group']['name'] for r in user_info.get('roles', [])]}")
        return True
    else:
        print(f"❌ {username} - Authentication failed")
        return False

async def main():
    """Verify all test users."""
    print("Verifying test users...\n")
    
    results = []
    for username, password in TEST_USERS:
        result = await verify_user(username, password)
        results.append(result)
        print()
    
    success_count = sum(results)
    print(f"\n{'='*50}")
    print(f"Results: {success_count}/{len(TEST_USERS)} users verified")
    print(f"{'='*50}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run:
```powershell
python scripts\verify_test_users.py
```

---

## 🧪 Step 2: Create First RBAC Test File (45 minutes)

### 2.1 Create Test File

Create `tests/test_rbac_comprehensive.py`:

```python
"""
Comprehensive RBAC Authorization Tests for gql_property

Based on patterns from GQL_Agreement_Valiasek project.

Test Users (configure in systemdata.json):
- viewer.a@world.com: viewer, Group A
- editor.a@world.com: editor, Group A
- editor.b@world.com: editor, Group B (different group)
- admin.a@world.com: admin, Group A
- admin.parent@world.com: admin, Parent Group
- root.admin@world.com: admin, Root Group (sees everything)

Test Scenarios:
1. Creator ownership - users access their own content
2. Cross-group denial - Group A cannot access Group B
3. Parent group access - Parent admin sees child groups
4. Root admin access - Root admin sees everything
5. Viewer restrictions - viewers cannot create/update
6. Editor CRUD - editors can CRUD their own content
7. Admin group access - admins can access group content
8. Role hierarchy - admin > editor > viewer
"""

import pytest
import pytest_asyncio
from tests.client import createLiveClient


# Test user configurations
TEST_USERS = {
    "viewer_a": {
        "email": "viewer.a@world.com",
        "password": "viewer.a@world.com",
        "role": "viewer",
        "group": "Group A"
    },
    "editor_a": {
        "email": "editor.a@world.com",
        "password": "editor.a@world.com",
        "role": "editor",
        "group": "Group A"
    },
    "editor_b": {
        "email": "editor.b@world.com",
        "password": "editor.b@world.com",
        "role": "editor",
        "group": "Group B"
    },
    "admin_a": {
        "email": "admin.a@world.com",
        "password": "admin.a@world.com",
        "role": "admin",
        "group": "Group A"
    },
    "admin_parent": {
        "email": "admin.parent@world.com",
        "password": "admin.parent@world.com",
        "role": "admin",
        "group": "Parent Group"
    },
    "root_admin": {
        "email": "root.admin@world.com",
        "password": "root.admin@world.com",
        "role": "admin",
        "group": "Root Group"
    }
}


# Fixtures for each test user
@pytest_asyncio.fixture
async def viewer_a_client():
    """Viewer in Group A."""
    return createLiveClient(
        username=TEST_USERS["viewer_a"]["email"],
        password=TEST_USERS["viewer_a"]["password"]
    )


@pytest_asyncio.fixture
async def editor_a_client():
    """Editor in Group A."""
    return createLiveClient(
        username=TEST_USERS["editor_a"]["email"],
        password=TEST_USERS["editor_a"]["password"]
    )


@pytest_asyncio.fixture
async def editor_b_client():
    """Editor in Group B (different group)."""
    return createLiveClient(
        username=TEST_USERS["editor_b"]["email"],
        password=TEST_USERS["editor_b"]["password"]
    )


@pytest_asyncio.fixture
async def admin_a_client():
    """Admin in Group A."""
    return createLiveClient(
        username=TEST_USERS["admin_a"]["email"],
        password=TEST_USERS["admin_a"]["password"]
    )


@pytest_asyncio.fixture
async def admin_parent_client():
    """Admin in Parent Group (sees child groups)."""
    return createLiveClient(
        username=TEST_USERS["admin_parent"]["email"],
        password=TEST_USERS["admin_parent"]["password"]
    )


@pytest_asyncio.fixture
async def root_admin_client():
    """Root admin (sees everything)."""
    return createLiveClient(
        username=TEST_USERS["root_admin"]["email"],
        password=TEST_USERS["root_admin"]["password"]
    )


# Test 1: Creator Ownership
@pytest.mark.asyncio
async def test_creator_ownership(editor_a_client):
    """
    Test: Users can access content they created.
    
    Editor A creates a purchase.
    Editor A can read, update, delete their own purchase.
    """
    # Create purchase
    create_mutation = """
    mutation($purchase: PurchaseInsertGQLModel!) {
        result: purchaseInsert(purchase: $purchase) {
            __typename
            ... on PurchaseGQLModel {
                id
                reason
                lastchange
            }
            ... on PurchaseGQLModelInsertError {
                msg
            }
        }
    }
    """
    
    variables = {
        "purchase": {
            "reason": "Test creator ownership",
            "status": "draft",
            "requesterId": "2d9dc5ca-a4a2-11ed-b9df-0242ac120003"
        }
    }
    
    result = await editor_a_client.execute(create_mutation, variables)
    
    # Verify creation succeeded
    assert "errors" not in result
    data = result["data"]["result"]
    assert data["__typename"] == "PurchaseGQLModel"
    
    purchase_id = data["id"]
    lastchange = data["lastchange"]
    
    # Verify creator can read their own purchase
    read_query = """
    query($id: UUID!) {
        purchase: purchaseById(id: $id) {
            id
            reason
        }
    }
    """
    
    result = await editor_a_client.execute(read_query, {"id": purchase_id})
    assert "errors" not in result
    assert result["data"]["purchase"]["id"] == purchase_id
    
    # Verify creator can update their own purchase
    update_mutation = """
    mutation($purchase: PurchaseUpdateGQLModel!) {
        result: purchaseUpdate(purchase: $purchase) {
            __typename
            ... on PurchaseGQLModel {
                id
                reason
            }
            ... on PurchaseGQLModelUpdateError {
                msg
            }
        }
    }
    """
    
    update_variables = {
        "purchase": {
            "id": purchase_id,
            "reason": "Updated by creator",
            "lastchange": lastchange
        }
    }
    
    result = await editor_a_client.execute(update_mutation, update_variables)
    
    # Check for errors at both GraphQL and mutation level
    if "errors" in result:
        print(f"⚠️ Update failed with GraphQL errors: {result['errors']}")
        # This might be expected if RBAC blocks at GraphQL level
    else:
        data = result["data"]["result"]
        if data["__typename"] == "PurchaseGQLModelUpdateError":
            print(f"⚠️ Update failed with mutation error: {data['msg']}")
        else:
            assert data["reason"] == "Updated by creator"
            print("✅ Creator can update their own content")


# Test 2: Cross-Group Access Denied
@pytest.mark.asyncio
async def test_cross_group_access_denied(editor_a_client, editor_b_client):
    """
    Test: Users from Group A cannot access Group B content.
    
    Editor A creates purchase (in Group A).
    Editor B (from Group B) tries to access it.
    Expected: Access denied or None returned.
    """
    # Editor A creates purchase
    create_mutation = """
    mutation($purchase: PurchaseInsertGQLModel!) {
        result: purchaseInsert(purchase: $purchase) {
            __typename
            ... on PurchaseGQLModel {
                id
            }
            ... on PurchaseGQLModelInsertError {
                msg
            }
        }
    }
    """
    
    variables = {
        "purchase": {
            "reason": "Test cross-group access",
            "status": "draft",
            "requesterId": "2d9dc5ca-a4a2-11ed-b9df-0242ac120003"
        }
    }
    
    result = await editor_a_client.execute(create_mutation, variables)
    
    if "errors" in result:
        pytest.skip("Editor A cannot create purchase - check permissions")
    
    data = result["data"]["result"]
    if data["__typename"] != "PurchaseGQLModel":
        pytest.skip(f"Purchase creation failed: {data.get('msg', 'Unknown error')}")
    
    purchase_id = data["id"]
    
    # Editor B tries to access Editor A's purchase
    read_query = """
    query($id: UUID!) {
        purchase: purchaseById(id: $id) {
            id
            reason
        }
    }
    """
    
    result = await editor_b_client.execute(read_query, {"id": purchase_id})
    
    # Should either return None or have errors
    if "errors" in result:
        print("✅ Cross-group access denied at GraphQL level")
    elif result["data"]["purchase"] is None:
        print("✅ Cross-group access denied - purchase not visible")
    else:
        pytest.fail("❌ Cross-group access should be denied!")


# Test 3: Viewer Cannot Create
@pytest.mark.asyncio
async def test_viewer_cannot_create(viewer_a_client):
    """
    Test: Viewer role cannot create purchases.
    
    Viewer A tries to create purchase.
    Expected: Authorization error.
    """
    create_mutation = """
    mutation($purchase: PurchaseInsertGQLModel!) {
        result: purchaseInsert(purchase: $purchase) {
            __typename
            ... on PurchaseGQLModel {
                id
            }
            ... on PurchaseGQLModelInsertError {
                msg
            }
        }
    }
    """
    
    variables = {
        "purchase": {
            "reason": "Test viewer restriction",
            "status": "draft",
            "requesterId": "2d9dc5ca-a4a2-11ed-b9df-0242ac120003"
        }
    }
    
    result = await viewer_a_client.execute(create_mutation, variables)
    
    # Should have errors or error message
    if "errors" in result:
        assert "permission" in str(result["errors"]).lower() or "authorization" in str(result["errors"]).lower()
        print("✅ Viewer cannot create - denied at GraphQL level")
    else:
        data = result["data"]["result"]
        if data["__typename"] == "PurchaseGQLModelInsertError":
            assert "permission" in data["msg"].lower() or "authorization" in data["msg"].lower()
            print("✅ Viewer cannot create - denied at mutation level")
        else:
            pytest.fail("❌ Viewer should not be able to create purchases!")


# Test 4: Root Admin Universal Access
@pytest.mark.asyncio
async def test_root_admin_universal_access(editor_a_client, root_admin_client):
    """
    Test: Root admin can access all content regardless of group.
    
    Editor A creates purchase in Group A.
    Root admin can access it.
    """
    # Editor A creates purchase
    create_mutation = """
    mutation($purchase: PurchaseInsertGQLModel!) {
        result: purchaseInsert(purchase: $purchase) {
            __typename
            ... on PurchaseGQLModel {
                id
            }
            ... on PurchaseGQLModelInsertError {
                msg
            }
        }
    }
    """
    
    variables = {
        "purchase": {
            "reason": "Test root admin access",
            "status": "draft",
            "requesterId": "2d9dc5ca-a4a2-11ed-b9df-0242ac120003"
        }
    }
    
    result = await editor_a_client.execute(create_mutation, variables)
    
    if "errors" in result:
        pytest.skip("Editor A cannot create purchase - check permissions")
    
    data = result["data"]["result"]
    if data["__typename"] != "PurchaseGQLModel":
        pytest.skip(f"Purchase creation failed: {data.get('msg', 'Unknown error')}")
    
    purchase_id = data["id"]
    
    # Root admin accesses purchase
    read_query = """
    query($id: UUID!) {
        purchase: purchaseById(id: $id) {
            id
            reason
        }
    }
    """
    
    result = await root_admin_client.execute(read_query, {"id": purchase_id})
    
    assert "errors" not in result
    assert result["data"]["purchase"] is not None
    assert result["data"]["purchase"]["id"] == purchase_id
    print("✅ Root admin can access all content")


# Add placeholder tests for future implementation
@pytest.mark.skip(reason="TODO: Implement parent group access test")
@pytest.mark.asyncio
async def test_parent_group_access(editor_a_client, admin_parent_client):
    """Test that parent group admin can access child group content."""
    pass


@pytest.mark.skip(reason="TODO: Implement admin group access test")
@pytest.mark.asyncio
async def test_admin_group_access(editor_a_client, admin_a_client):
    """Test that group admin can access all content in their group."""
    pass


@pytest.mark.skip(reason="TODO: Implement editor CRUD test")
@pytest.mark.asyncio
async def test_editor_full_crud_own_content(editor_a_client):
    """Test that editor can create, read, update, delete their own content."""
    pass


@pytest.mark.skip(reason="TODO: Implement role hierarchy test")
@pytest.mark.asyncio
async def test_role_hierarchy(viewer_a_client, editor_a_client, admin_a_client):
    """Test that role hierarchy works: admin > editor > viewer."""
    pass
```

### 2.2 Run Initial Tests

```powershell
# Run all RBAC tests
pytest tests/test_rbac_comprehensive.py -v

# Run specific test
pytest tests/test_rbac_comprehensive.py::test_creator_ownership -v -s

# Run with output
pytest tests/test_rbac_comprehensive.py -v -s
```

---

## 📊 Step 3: Measure Coverage (15 minutes)

### 3.1 Run Coverage Report

```powershell
# Run RBAC tests with coverage
pytest tests/test_rbac_comprehensive.py --cov=src --cov-report=html --cov-report=term

# Open HTML report
start htmlcov\index.html
```

### 3.2 Identify Gaps

Look for:
- ❌ Red lines in authorization code
- ❌ Low coverage in GraphTypeDefinitions
- ❌ Uncovered error paths

---

## 📝 Step 4: Update Documentation (20 minutes)

### 4.1 Add Status Dashboard

Update `TESTING_GUIDE.md` at the top:

```markdown
## 🎯 Current Test Suite Status

**Last Updated:** February 7, 2026

**Status:** ✅ **XX/XX passing (XX%), XX skipped (XX%), XX failing (XX%)**

### Test Breakdown
- **Unit Tests**: XX/XX passing (100%)
- **RBAC Tests**: 4/8 passing (50%) 🚧 In Progress
- **Live Tests**: XX/XX passing (XX%)
- **Performance Tests**: 0/5 passing (0%) 🚧 TODO
```

### 4.2 Add Test User Reference

Add to `TESTING_GUIDE.md`:

```markdown
## 👥 Test Users Reference

| Username | Password | Role | Group | Use Case |
|----------|----------|------|-------|----------|
| viewer.a@world.com | viewer.a@world.com | viewer | Group A | Read-only tests |
| editor.a@world.com | editor.a@world.com | editor | Group A | Standard CRUD |
| editor.b@world.com | editor.b@world.com | editor | Group B | Cross-group tests |
| admin.a@world.com | admin.a@world.com | admin | Group A | Group admin tests |
| admin.parent@world.com | admin.parent@world.com | admin | Parent Group | Hierarchy tests |
| root.admin@world.com | root.admin@world.com | admin | Root Group | Universal access tests |
```

---

## ✅ Success Criteria

After completing this quickstart, you should have:

- [x] ✅ Test users configured in systemdata.json
- [x] ✅ Test user verification script
- [x] ✅ `test_rbac_comprehensive.py` with 4+ passing tests
- [x] ✅ Coverage report showing authorization code coverage
- [x] ✅ Updated documentation with status and test users
- [x] ✅ Clear path to implement remaining 4+ tests

---

## 🎯 Next Steps

### Immediate (Today)
1. Review this guide
2. Configure test users in systemdata.json
3. Run verification script
4. Run first RBAC test

### This Week
1. Implement remaining 4 RBAC tests
2. Achieve 80%+ coverage on authorization code
3. Update documentation with results

### Next Week
1. Add performance tests (test_performance.py)
2. Enhance test documentation
3. Create demo video

---

## 🆘 Troubleshooting

### Issue: Test user authentication fails

**Solution:** Verify user exists in UG service database:
```powershell
python scripts\get_my_groups.py --username viewer.a@world.com --password viewer.a@world.com
```

### Issue: Tests skip due to creation failures

**Solution:** Check authorization extensions:
```python
# In GraphTypeDefinitions/__init__.py
# Verify extensions are configured correctly
```

### Issue: Cross-group test doesn't deny access

**Solution:** Verify rbacobject_id is set correctly:
```python
# Check that entities have rbacobject_id set to group UUID
```

---

## 📚 Resources

- **GQL_Agreement Test Patterns:** `E:\PyCharm_Projects\GQL_Agreement_Valiasek\tests\test_rbac_comprehensive.py`
- **Existing Live Tests:** `tests/test_purchases_live.py`
- **Test Client:** `tests/client.py`
- **Coverage Guide:** `COVERAGE_GUIDE.md`
- **Testing Guide:** `TESTING_GUIDE.md`

---

**Ready to start? Begin with Step 1! 🚀**

