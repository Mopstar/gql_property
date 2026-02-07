# Complete Testing Guide

**Last Updated:** February 7, 2026  
**Purpose:** Unified guide for all testing approaches in gql_property

---

## 🎯 Current Test Suite Status

**Status:** 🚧 **Phase 2 In Progress - RBAC Testing Implementation**

### Test Breakdown

| Category | Tests | Status | Coverage |
|----------|-------|--------|----------|
| **Unit Tests** | 15+ files | ✅ Passing | Good |
| **Live Tests** | 3 files | ✅ Passing | Good |
| **RBAC Tests** | 5 tests (4 skipped) | 🚧 In Progress | Expanding |
| **Performance Tests** | 1 test | 🆕 New | Basic |

### Recent Additions (Feb 7, 2026)
- ✅ Created `test_rbac_comprehensive.py` with creator ownership tests
- ✅ Added `scripts/verify_test_users.py` for user verification
- ✅ Implemented 5 RBAC test scenarios (4 require multi-user setup)
- 🚧 TODO: Add more test users for cross-group testing

### Test Users Reference

| Username | Password | Role | Use Case |
|----------|----------|------|----------|
| john.newbie@world.com | john.newbie@world.com | editor | Standard CRUD operations |

**Note:** More test users needed for comprehensive RBAC testing. See [RBAC_TESTING_QUICKSTART.md](RBAC_TESTING_QUICKSTART.md) for setup guide.

---

## 📋 Table of Contents

1. [Current Test Status](#current-test-suite-status) ⭐ NEW
2. [Quick Test Setup (5 minutes)](#quick-test-setup)
3. [Test Infrastructure](#test-infrastructure)
4. [Sample Test Queries](#sample-test-queries)
5. [Complete CRUD Tests](#complete-crud-tests)
6. [Live Test Analysis](#live-test-analysis)
7. [RBAC Testing](#rbac-testing) ⭐ NEW

---

## Quick Test Setup

**5-Minute Setup for Live Testing**

### 1. Start Services (1 minute)
```powershell
cd E:\PyCharm_Projects\gql_property
docker compose -f docker-compose.debug.yml up -d
```

### 2. Verify Connectivity (30 seconds)
```powershell
python tests\check_services.py
```

**Expected:**
```
✅ Property Service (Direct)    - Running
✅ Apollo Gateway (Federation)  - Running
✅ UG Service                   - Running
✅ Frontend                     - Running
✅ All services running!
```

### 3. Create First Live Test (2 minutes)

**Create `tests/test_purchases_live.py`:**
```python
import pytest
import pytest_asyncio
from tests.client import createLiveClient

@pytest_asyncio.fixture
async def client():
    return createLiveClient(
        username="john.newbie@world.com",
        password="john.newbie@world.com"
    )

@pytest.mark.asyncio
async def test_purchase_query(client):
    """Test querying purchases from live server."""
    query = """
    query {
        purchases: purchasePage(limit: 5) {
            id
            name
            status
        }
    }
    """
    
    result = await client.execute(query)
    
    assert "errors" not in result
    assert "data" in result
    print(f"✅ Found {len(result['data']['purchases'])} purchases")
```

### 4. Run Test (30 seconds)
```powershell
pytest tests/test_purchases_live.py -v -s
```

---

## Test Infrastructure

### Test Files Overview

```
tests/
├── client.py                    # Universal GraphQL client
├── check_services.py            # Service connectivity checker
├── test_purchases_live.py       # Live CRUD tests
├── test_federation.py           # Federation integration
├── test_purchases.py            # Unit tests (SQLite)
├── test_dbdefinitions.py        # DB model tests
├── test_dataloaders.py          # Dataloader tests
└── test_gt_definitions.py       # GraphQL type tests
```

### Client Types

#### Federation Client (Integration Tests)
```python
from tests.client import createFederationClient

client = createFederationClient(
    username="user@world.com",
    password="password",
    endpoint="http://localhost:33000/api/gql"  # Apollo Gateway
)
```

#### Direct Service Client (Isolated Tests)
```python
from tests.client import createLiveClient

client = createLiveClient(
    username="user@world.com", 
    password="password",
    endpoint="http://localhost:8000/gql"  # Direct service
)
```

#### In-Memory Client (Unit Tests)
```python
from tests.client import createTestClient

client = createTestClient()  # SQLite in-memory
```

### Test Users (from systemdata.rnd.json)

| Username | Password | Primary Group | Roles |
|----------|----------|---------------|-------|
| john.newbie@world.com | john.newbie@world.com | Group-1 | viewer |
| Estera.Luckova@world.com | 2222 | Dept-A | editor, admin |
| Ludvik.Kilik@world.com | ludvik | University (root) | rektor, admin |
| Oliver.Opletal@world.com | oliver | Dept-A | editor |

---

## Sample Test Queries

### Endpoints

**Direct Service (Development):**
- Endpoint: `http://localhost:8000/gql`
- Playground: `http://localhost:8000/ui`
- Use for: Testing purchase mutations, full schema access

**Federation Gateway (Production-like):**
- Endpoint: `http://localhost:33000/api/gql`
- Use for: Testing cross-service queries after federation setup

### Basic Queries

#### Check Current User
```graphql
query WhoAmI {
  me {
    id
    fullname
    email
    roles {
      group { id name }
      roletype { name }
    }
  }
}
```

#### List Purchases
```graphql
query ListPurchases {
  purchasePage(skip: 0, limit: 20) {
    id
    name
    status
    createdby { id fullname }
    rbacobjectId
  }
}
```

#### Create Purchase
```graphql
mutation CreatePurchase {
  purchaseInsert(purchase: {
    name: "Office Supplies"
    description: "Monthly office supplies"
    status: "draft"
  }) {
    ... on PurchaseGQLModel {
      id
      name
      status
      createdbyId
      rbacobjectId
      created
      lastchange
    }
    ... on PurchaseGQLModelInsertError {
      msg
      code
      location
    }
  }
}
```

**Save the `id` and `lastchange` from response for update/delete operations!**

---

## Complete CRUD Tests

### ⚠️ Important: Auto-Managed Fields

The following fields are **automatically managed** by the system:

| Field | Auto-Set On | Purpose |
|-------|-------------|---------|
| `createdby_id` | INSERT | Tracks who created (you become owner!) |
| `rbacobject_id` | INSERT | Group ownership (auto-assigned) |
| `changedby_id` | UPDATE | Tracks who last modified |

**These fields are marked as `strawberry.Private` and cannot be set manually in mutations.**

### CREATE Operations

#### Basic Insert
```graphql
mutation CreatePurchaseBasic {
  purchaseInsert(purchase: {
    name: "Office Supplies - January 2026"
    status: "pending"
    path: "/purchases/2026/office"
    # rbacobject_id auto-assigned to your primary write group
  }) {
    ... on PurchaseGQLModel {
      id
      name
      status
      createdbyId      # Your user.id
      rbacobjectId     # Auto-assigned
      created
      lastchange
    }
    ... on PurchaseGQLModelInsertError {
      msg
      code
    }
  }
}
```

**Expected Result:**
- ✅ SUCCESS if you have editor/admin role
- `createdbyId` = your user.id (you become owner!)
- `rbacobjectId` = your primary write group (auto-assigned)
- ❌ ERROR if viewer role: "User does not have editor/admin role"

#### Insert with Child Items
```graphql
mutation CreatePurchaseWithItems {
  purchaseInsert(purchase: {
    name: "Computer Equipment"
    status: "pending"
    items: [
      { name: "Dell Monitor 27\"", quantity: 2, price: 350.00 }
      { name: "Logitech Keyboard", quantity: 2, price: 89.99 }
    ]
  }) {
    ... on PurchaseGQLModel {
      id
      items {
        id
        name
        quantity
        price
      }
    }
  }
}
```

### READ Operations

#### Query by ID
```graphql
query GetPurchaseById {
  purchaseById(id: "YOUR_PURCHASE_ID") {
    id
    name
    status
    createdby { fullname }
    rbacobject { id name }
  }
}
```

**Expected Result:**
- ✅ SUCCESS if you're creator OR have role in entity's group
- ❌ NULL if no permission (filtered out)

#### Query Page with Filtering
```graphql
query GetPurchasesFiltered {
  purchasePage(
    limit: 20
    skip: 0
    where: { status: { _eq: "pending" } }
    orderby: [{ created: DESC }]
  ) {
    id
    name
    status
    created
  }
}
```

**Result:** Only returns purchases you have permission to see.

### UPDATE Operations

#### Update Purchase
```graphql
mutation UpdatePurchase {
  purchaseUpdate(purchase: {
    id: "YOUR_PURCHASE_ID"
    lastchange: "CURRENT_LASTCHANGE"
    name: "Updated Name"
    status: "approved"
  }) {
    ... on PurchaseGQLModel {
      id
      name
      status
      lastchange  # New timestamp
      changedbyId # Your user.id
    }
    ... on PurchaseGQLModelUpdateError {
      msg
      code
    }
  }
}
```

**Expected Result:**
- ✅ SUCCESS if you're creator OR have editor/admin role in group
- ❌ ERROR if viewer role: "Permission denied"
- ❌ ERROR if wrong lastchange: "Optimistic locking failure"

### DELETE Operations

#### Delete Purchase (with items)
```graphql
# Step 1: Delete all child items first (if cascade not enabled)
mutation DeletePurchaseItems {
  item1: purchaseItemDelete(purchaseItem: {
    id: "ITEM_1_ID"
    lastchange: "ITEM_1_LASTCHANGE"
  })
  item2: purchaseItemDelete(purchaseItem: {
    id: "ITEM_2_ID"
    lastchange: "ITEM_2_LASTCHANGE"
  })
}

# Step 2: Delete parent purchase
mutation DeletePurchase {
  purchaseDelete(purchase: {
    id: "PURCHASE_ID"
    lastchange: "CURRENT_LASTCHANGE"
  }) {
    ... on PurchaseGQLModelDeleteError {
      msg
      code
    }
  }
}
```

**Expected Result:**
- ✅ SUCCESS (returns `null`) if you're creator OR admin in group
- ❌ ERROR if viewer/editor role: "Permission denied"
- ❌ ERROR if items exist: "Foreign key constraint violated" (delete items first)

---

## Live Test Analysis

### Test Coverage Recommendations

Based on analysis of gql_evolution (reference project):

#### 1. Service Connectivity Tests
```python
@pytest.mark.asyncio
async def test_direct_service_running():
    """Verify direct service responds."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/gql",
            json={"query": "{ __schema { types { name } } }"}
        )
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_federation_gateway_running():
    """Verify Apollo Gateway responds."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:33000/api/gql",
            json={"query": "{ __schema { types { name } } }"}
        )
        assert response.status_code == 200
```

#### 2. RBAC Authorization Tests
```python
@pytest.mark.asyncio
async def test_creator_can_always_update_own_purchase():
    """Test creator ownership - permanent access."""
    # Create as user A
    client_a = createLiveClient("Oliver.Opletal@world.com", "oliver")
    create_result = await client_a.execute(CREATE_MUTATION)
    purchase_id = create_result["data"]["purchaseInsert"]["id"]
    
    # Update as user A (should succeed)
    update_result = await client_a.execute(UPDATE_MUTATION, {"id": purchase_id})
    assert "errors" not in update_result

@pytest.mark.asyncio
async def test_group_admin_can_modify_group_purchase():
    """Test group permissions."""
    # Create as user A (editor)
    client_a = createLiveClient("Oliver.Opletal@world.com", "oliver")
    create_result = await client_a.execute(CREATE_MUTATION)
    purchase_id = create_result["data"]["purchaseInsert"]["id"]
    
    # Update as user B (admin in same group)
    client_b = createLiveClient("Estera.Luckova@world.com", "2222")
    update_result = await client_b.execute(UPDATE_MUTATION, {"id": purchase_id})
    assert "errors" not in update_result

@pytest.mark.asyncio
async def test_viewer_cannot_create():
    """Test role restrictions."""
    client = createLiveClient("john.newbie@world.com", "john.newbie@world.com")
    result = await client.execute(CREATE_MUTATION)
    
    assert "errors" in result or result["data"]["purchaseInsert"]["msg"] is not None
```

#### 3. Cross-Service Integration Tests
```python
@pytest.mark.asyncio
async def test_query_with_user_resolution():
    """Test UG + Purchase service integration."""
    client = createFederationClient("Estera.Luckova@world.com", "2222")
    
    query = """
    query {
      purchasePage(limit: 5) {
        id
        name
        createdby {  # Resolved via UG service
          id
          fullname
          email
        }
      }
    }
    """
    
    result = await client.execute(query)
    assert "errors" not in result
    for purchase in result["data"]["purchasePage"]:
        assert purchase["createdby"]["fullname"] is not None
```

#### 4. Performance Tests
```python
@pytest.mark.asyncio
async def test_dataloader_prevents_n_plus_1():
    """Test DataLoader batching efficiency."""
    client = createLiveClient("Estera.Luckova@world.com", "2222")
    
    query = """
    query {
      purchasePage(limit: 50) {
        id
        createdby { fullname }  # Should batch load via DataLoader
        rbacobject { name }     # Should batch load via DataLoader
        items { name }          # Should batch load via DataLoader
      }
    }
    """
    
    import time
    start = time.time()
    result = await client.execute(query)
    duration = time.time() - start
    
    assert "errors" not in result
    assert duration < 2.0  # Should complete in <2 seconds with batching
```

### Running Complete Test Suite

```powershell
# Run all tests
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run only RBAC tests
pytest tests/test_rbac_comprehensive.py -v

# Run excluding skipped tests
pytest tests/test_rbac_comprehensive.py -v -m "not skip"

# Run with output (shows print statements)
pytest tests/test_rbac_comprehensive.py -v -s
```

---

## 🔒 RBAC Testing

**Added:** February 7, 2026

### Overview

RBAC (Role-Based Access Control) testing ensures that authorization rules are correctly enforced across different user roles and groups.

### Test File: `test_rbac_comprehensive.py`

**Current Status:** 5 tests implemented (1 passing, 4 pending multi-user setup)

### Implemented Tests

#### 1. Creator Ownership (✅ Working)
Tests that users can create, read, update, and delete their own content:

```python
@pytest.mark.asyncio
async def test_creator_can_create_purchase(john_client):
    """Test that users can create purchases."""
    # User creates purchase
    # User becomes the creator
    # Purchase is successfully created
```

**Run:**
```powershell
pytest tests/test_rbac_comprehensive.py::TestCreatorOwnership -v
```

#### 2. Cross-Group Access (🚧 Requires Multi-User Setup)
Tests that users from different groups cannot access each other's content:

```python
@pytest.mark.skip(reason="Requires multiple test users")
async def test_cross_group_access_denied():
    # Editor A creates purchase in Group A
    # Editor B (from Group B) tries to access it
    # Access is denied
```

**Prerequisites:**
- Two test users in different groups
- See [RBAC_TESTING_QUICKSTART.md](RBAC_TESTING_QUICKSTART.md) for setup

#### 3. Viewer Restrictions (🚧 Requires Viewer User)
Tests that viewers can read but not modify:

```python
@pytest.mark.skip(reason="Requires viewer test user")
async def test_viewer_cannot_create():
    # Viewer tries to create purchase
    # Creation is denied with authorization error
```

**Prerequisites:**
- Test user with viewer role
- See [RBAC_TESTING_QUICKSTART.md](RBAC_TESTING_QUICKSTART.md) for setup

### Quick Start: RBAC Testing

1. **Verify Current Users:**
   ```powershell
   python scripts\verify_test_users.py
   ```

2. **Run Implemented Tests:**
   ```powershell
   pytest tests/test_rbac_comprehensive.py::TestCreatorOwnership -v
   ```

3. **Add More Test Users:**
   - Configure in UG service (see RBAC_TESTING_QUICKSTART.md)
   - Update TEST_USERS in test_rbac_comprehensive.py
   - Remove @pytest.mark.skip decorators

4. **Run All RBAC Tests:**
   ```powershell
   pytest tests/test_rbac_comprehensive.py -v
   ```

### Performance Testing

Basic performance test included:

```python
@pytest.mark.asyncio
async def test_query_latency(john_client):
    """Test that queries complete within acceptable latency (<1s)."""
    # Measures query execution time
    # Asserts completion < 1 second
```

**Run:**
```powershell
pytest tests/test_rbac_comprehensive.py::TestPerformanceBasics -v
```

### Next Steps

1. **Add More Test Users** (see RBAC_TESTING_QUICKSTART.md):
   - viewer.a@world.com (viewer, Group A)
   - editor.b@world.com (editor, Group B)
   - admin.a@world.com (admin, Group A)
   - root.admin@world.com (admin, Root Group)

2. **Implement Pending Tests:**
   - Cross-group access denial
   - Viewer role restrictions
   - Root admin universal access
   - Parent group inheritance

3. **Measure Coverage:**
   ```powershell
   pytest tests/test_rbac_comprehensive.py --cov=src.GraphTypeDefinitions --cov-report=html
   ```

4. **Target:** 90%+ coverage on authorization code

---

## 📚 Additional Resources

### Documentation
- **[TESTING_DOCUMENTATION_INDEX.md](TESTING_DOCUMENTATION_INDEX.md)** - Central navigation for all testing docs
- **[RBAC_TESTING_QUICKSTART.md](RBAC_TESTING_QUICKSTART.md)** - Step-by-step RBAC implementation guide
- **[TESTING_AND_COVERAGE_ANALYSIS.md](TESTING_AND_COVERAGE_ANALYSIS.md)** - Complete analysis & comparison
- **[COVERAGE_GUIDE.md](COVERAGE_GUIDE.md)** - Code coverage setup and usage

### Quick Commands
```powershell
# Start services
docker compose -f docker-compose.debug.yml up -d

# Verify connectivity
python tests\check_services.py

# Verify test users
python scripts\verify_test_users.py

# Run all tests
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
start htmlcov\index.html

# Run RBAC tests only
pytest tests/test_rbac_comprehensive.py -v
```

---

**Last Updated:** February 7, 2026  
**Next:** Complete multi-user setup for comprehensive RBAC testing
pytest tests/ -v

# Run only live tests
pytest tests/test_purchases_live.py tests/test_federation.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test
pytest tests/test_purchases_live.py::test_creator_can_update -v -s
```

---

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues:
- Services not running
- Empty roles array
- Database constraint errors
- Federation setup issues

---

## Additional Resources

- **[API_USAGE_GUIDE.md](API_USAGE_GUIDE.md)** - Complete API usage guide
- **[CREATOR_OWNERSHIP_GUIDE.md](CREATOR_OWNERSHIP_GUIDE.md)** - Authorization model
- **[ERROR_CODES.md](ERROR_CODES.md)** - Error codes dictionary
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
