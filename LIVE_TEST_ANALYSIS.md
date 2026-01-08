# Live Test Analysis for GQL_Property

**Date:** January 8, 2026  
**Reference Project:** gql_evolution (Agreement service)  
**Target Project:** gql_property (Purchase/Property service)

---

## 📋 Executive Summary

Based on analysis of `gql_evolution` workspace, this document outlines:
1. ✅ **How live tests are implemented** in the reference project
2. 🎯 **Recommended test coverage** for `gql_property`
3. 🔧 **Implementation roadmap** with reusable infrastructure

---

## 🔍 Analysis of gql_evolution Test Infrastructure

### Current Test Suite

**Test Files (3 active):**
```
tests/
├── client.py                          # Universal GraphQL client (343 lines)
├── test_rbac_comprehensive.py         # RBAC authorization tests (8 passing)
├── test_federation_expanded.py        # Client behavior & integration (11 passing, 8 skipped)
└── test_federation_performance.py     # Performance benchmarks (15 passing)
```

**Status:** ✅ **34/42 passing (81%), 8 skipped (19%), 0 failing (0%)**

### Key Infrastructure Components

#### 1. **client.py - Universal Test Client** ⭐ CRITICAL COMPONENT

**Features:**
- ✅ **Multiple endpoint support**: Federation gateway, direct service, in-memory SQLite
- ✅ **Automatic JWT authentication**: Token management with caching
- ✅ **Cross-service queries**: Seamless UG + Agreement integration
- ✅ **Error handling and retries**
- ✅ **Consistent API across test types**

**Client Types:**
```python
# Apollo Federation Gateway (integration tests)
client = createFederationClient(
    username="Estera.Luckova@world.com",
    password="2222",
    endpoint="http://localhost:33000/api/gql"  # Apollo Gateway
)

# Direct service (isolated tests)
client = createLiveClient(
    username="Estera.Luckova@world.com", 
    password="2222",
    endpoint="http://localhost:8000/gql"  # Direct service
)

# In-memory SQLite (unit tests - minimal use)
client = createTestClient()
```

**Core API:**
```python
# Execute query with auto-authentication
result = await client.execute(query, variables)

# Get authenticated user info from UG service
user_info = await client.get_user_info()

# Manual token retrieval
token = await getToken(username, password)
```

#### 2. **Authentication Flow**

**OAuth 2-Step Process:**
```python
async def getToken(username, password, keyurl="http://localhost:33001/oauth/login3"):
    # Step 1: GET challenge key
    async with session.get(keyurl) as resp:
        keyJson = await resp.json()
    
    # Step 2: POST credentials + key → JWT token
    payload = {"key": keyJson["key"], "username": username, "password": password}
    async with session.post(keyurl, json=payload) as resp:
        tokenJson = await resp.json()
    
    return tokenJson.get("token", None)
```

**Token Management:**
- Cached per username to avoid redundant logins
- Automatic retry on token expiration
- Supports cookies (`authorization`) and headers (`Authorization: Bearer`)

#### 3. **Test Users (from systemdata.rnd.json)**

```python
TEST_USERS = {
    "jitka": {  # viewer, Dept A1
        "email": "Jitka.Klouckova@world.com",
        "password": "Jitka.Klouckova@world.com",  # Password = email in test system
        "role": "viewer",
        "dept": "Dept A1"
    },
    "estera": {  # editor, Dept A1
        "email": "Estera.Luckova@world.com",
        "password": "Estera.Luckova@world.com",
        "role": "editor",
        "dept": "Dept A1"
    },
    "radomil": {  # editor, Dept A2
        "email": "Radomil.Sverek@world.com",
        "password": "Radomil.Sverek@world.com",
        "role": "editor",
        "dept": "Dept A2"
    },
    "zdenka": {  # admin, Dept A1
        "email": "Zdenka.Simeckova@world.com",
        "password": "Zdenka.Simeckova@world.com",
        "role": "admin",
        "dept": "Dept A1"
    },
    "ornela": {  # admin, Faculty A
        "email": "Ornela.Kuckova@world.com",
        "password": "Ornela.Kuckova@world.com",
        "role": "admin",
        "dept": "Faculty A"
    },
    "ludvik": {  # admin, University ROOT
        "email": "Ludvik.Kilik@world.com",
        "password": "Ludvik.Kilik@world.com",
        "role": "admin",
        "dept": "University ROOT"  # Root admin - sees everything
    }
}
```

#### 4. **Test Patterns**

**A) RBAC Authorization Tests** (test_rbac_comprehensive.py)
```python
@pytest_asyncio.fixture
async def estera_client():
    """Editor in Dept A1."""
    return createLiveClient(
        username=TEST_USERS["estera"]["email"],
        password=TEST_USERS["estera"]["password"]
    )

class TestCreatorOwnership:
    @pytest.mark.asyncio
    async def test_creator_can_update_own_agreement(self, estera_client):
        # 1. Create entity as Estera
        create_result = await estera_client.execute(CREATE_MUTATION)
        agreement_id = create_result["data"]["agreementInsert"]["id"]
        
        # 2. Update as creator (should succeed)
        update_result = await estera_client.execute(UPDATE_MUTATION, {"id": agreement_id})
        assert "errors" not in update_result
        
    @pytest.mark.asyncio
    async def test_cross_department_denial(self, estera_client, radomil_client):
        # 1. Estera creates in Dept A1
        agreement_id = await create_agreement(estera_client)
        
        # 2. Radomil (Dept A2) tries to access (should fail)
        result = await radomil_client.execute(QUERY_BY_ID, {"id": agreement_id})
        assert "errors" in result or result["data"]["agreementById"] is None
```

**B) Federation Integration Tests** (test_federation_expanded.py)
```python
class TestFederationClientBehavior:
    @pytest.mark.asyncio
    async def test_client_default_endpoints(self):
        fed = createFederationClient()
        live = createLiveClient()
        
        assert fed.endpoint == "http://localhost:33000/api/gql"
        assert live.endpoint == "http://localhost:8000/gql"
    
    @pytest.mark.asyncio
    async def test_cross_service_query(self, fed_client):
        # Single query spanning UG + Agreement services
        result = await fed_client.execute("""
            query {
              me { id fullname email }
              agreementPage { id agreementType }
            }
        """)
        
        assert "errors" not in result
        assert "me" in result["data"]
        assert "agreementPage" in result["data"]
```

**C) Performance Tests** (test_federation_performance.py)
```python
class TestPerformance:
    @pytest.mark.asyncio
    async def test_query_latency(self, fed_client):
        start = time.time()
        result = await fed_client.execute(SIMPLE_QUERY)
        latency = time.time() - start
        
        assert latency < 1.0  # Under 1 second
        
    @pytest.mark.asyncio
    async def test_concurrent_queries(self, fed_client):
        tasks = [fed_client.execute(QUERY) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert all("errors" not in r for r in results)
```

#### 5. **Service Prerequisites Check** (check_services.py)

```python
async def check_service(name: str, url: str) -> bool:
    """Check if a service is accessible."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status in [200, 404]:
                    print(f"✅ {name} - Running")
                    return True
    except aiohttp.ClientConnectorError:
        print(f"❌ {name} - Not running")
        return False

# Check all required services before running tests
services = {
    "Agreement Service": "http://localhost:8000/gql",
    "Apollo Gateway": "http://localhost:33000/api/gql",
    "UG Service": "http://localhost:33001/api/gql",
    "Frontend": "http://localhost:33001",
}
```

---

## 🎯 Recommended Test Coverage for gql_property

### Current Test Status in gql_property

**Existing Tests:**
```
tests/
├── client.py              # ⚠️ MINIMAL - only in-memory SQLite client
├── shared.py              # Basic context creation
├── test_purchases.py      # 3 tests - in-memory SQLite only
├── test_dbdefinitions.py  # DB model tests
├── test_dataloaders.py    # Dataloader tests
└── test_gt_definitions.py # GraphQL type tests
```

**⚠️ CRITICAL GAPS:**
- ❌ **No live server tests** - all tests use in-memory SQLite
- ❌ **No UG endpoint integration** - no real authentication tests
- ❌ **No Apollo Federation tests** - gateway not tested
- ❌ **No RBAC authorization tests** - if authorization implemented
- ❌ **No multi-user scenarios** - no cross-group access tests
- ❌ **No performance benchmarks**

### Recommended Test Suite Structure

```
tests/
├── client.py                          # ⭐ MIGRATE from gql_evolution
│   ├── getToken()                     # OAuth authentication
│   ├── GraphQLClientWrapper          # Base client class
│   ├── createFederationClient()      # Apollo gateway client
│   ├── createLiveClient()            # Direct service client
│   └── createTestClient()            # In-memory SQLite (existing)
│
├── check_services.py                  # ⭐ NEW - Service connectivity checker
│
├── test_client.py                     # ⚠️ MIGRATE - Client behavior tests
│
├── test_purchases_live.py             # ⭐ NEW - Live purchase tests
│   ├── TestPurchaseCRUD              # Create, Read, Update, Delete
│   ├── TestPurchaseValidation        # Business logic validation
│   └── TestPurchaseItems             # Nested item operations
│
├── test_federation.py                 # ⭐ NEW - Federation integration
│   ├── TestCrossServiceQueries       # UG + Purchase combined queries
│   ├── TestFederationPerformance     # Gateway performance
│   └── TestSchemaStitching           # Federation schema validation
│
├── test_authorization.py              # ⭐ NEW - If RBAC implemented
│   ├── TestCreatorOwnership          # User owns their purchases
│   ├── TestGroupPermissions          # Department-level access
│   └── TestCrossGroupAccess          # Hierarchical authorization
│
├── test_performance.py                # ⭐ NEW - Performance benchmarks
│   ├── TestQueryLatency              # Response time tests
│   ├── TestConcurrency               # Parallel query handling
│   └── TestStressScenarios           # Large dataset queries
│
├── test_purchases.py                  # ✅ KEEP - Unit tests (SQLite)
├── test_dbdefinitions.py             # ✅ KEEP - DB model tests
├── test_dataloaders.py               # ✅ KEEP - Dataloader tests
└── test_gt_definitions.py            # ✅ KEEP - GraphQL type tests
```

### Priority Test Coverage

#### 🔴 **P0 - Critical (Implement First)**

1. **Live Server Integration**
   - Migrate `client.py` from gql_evolution
   - Test against running service (not SQLite)
   - Verify UG authentication flow

2. **Basic CRUD Operations (Live)**
   - `test_purchase_insert_live` - Create purchase via API
   - `test_purchase_update_live` - Update purchase with optimistic locking
   - `test_purchase_delete_live` - Delete purchase
   - `test_purchase_query_live` - Query purchases with filters

3. **Service Health Check**
   - `check_services.py` - Verify all services running
   - Run before test suite
   - Clear error messages if services unavailable

#### 🟡 **P1 - Important (Next Phase)**

4. **Federation Testing**
   - Apollo Gateway connectivity
   - Cross-service queries (UG + Purchase)
   - Schema federation validation

5. **Authorization Testing** (if RBAC implemented)
   - User can access own purchases
   - Group-based access control
   - Cross-department access denial
   - Admin override scenarios

6. **Nested Entity Operations**
   - Purchase items CRUD
   - Batch operations
   - Transaction rollback scenarios

#### 🟢 **P2 - Nice to Have (Future)**

7. **Performance Benchmarks**
   - Query latency thresholds
   - Concurrent request handling
   - Large dataset pagination
   - N+1 query prevention verification

8. **Error Handling**
   - Invalid input validation
   - Authentication failures
   - Authorization denials
   - Optimistic locking conflicts

---

## 🔧 Implementation Roadmap

### Phase 1: Foundation (1-2 days)

**Step 1: Copy Test Infrastructure**
```powershell
# Copy client.py from gql_evolution
Copy-Item "c:\Users\vojta\gql_evolution\tests\client.py" `
          "c:\Users\vojta\OneDrive\Plocha\barta_gql\gql_property\tests\client.py" -Force

# Copy check_services.py
Copy-Item "c:\Users\vojta\gql_evolution\tests\check_services.py" `
          "c:\Users\vojta\OneDrive\Plocha\barta_gql\gql_property\tests\check_services.py" -Force
```

**Step 2: Update Endpoints**
```python
# In client.py, update default endpoints:
def createFederationClient(..., endpoint="http://localhost:33000/api/gql"):  # ✅ Same
def createLiveClient(..., endpoint="http://localhost:8000/gql"):  # ⚠️ Update if different port
```

**Step 3: Verify Service Connectivity**
```powershell
# Start services
docker compose -f docker-compose.debug.yml up -d

# Check connectivity
python tests/check_services.py
```

**Expected Output:**
```
✅ Agreement Service (Direct)      - Running (status 200)
✅ Apollo Gateway (Federation)     - Running (status 200)
✅ UG Service                      - Running (status 200)
✅ Frontend                        - Running (status 200)
✅ All services running!
```

### Phase 2: Basic Live Tests (2-3 days)

**Create test_purchases_live.py:**
```python
"""
Live Purchase Tests - Testing against running service
"""
import pytest
import pytest_asyncio
from tests.client import createLiveClient

@pytest_asyncio.fixture
async def live_client():
    """Create client connected to live service."""
    return createLiveClient(
        username="john.newbie@world.com",
        password="john.newbie@world.com"
    )

class TestPurchaseCRUDLive:
    """Test purchase CRUD operations against live server."""
    
    @pytest.mark.asyncio
    async def test_purchase_insert_live(self, live_client):
        """Test creating a purchase via live API."""
        mutation = """
        mutation($purchase: PurchaseInsertGQLModel!) {
            result: purchaseInsert(purchase: $purchase) {
                __typename
                ... on PurchaseGQLModel {
                    id
                    status
                    totalCost
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
                "reason": "Test purchase",
                "status": "submitted",
                "requesterId": "2d9dc5ca-a4a2-11ed-b9df-0242ac120003",
                "subinfo": [
                    {"name": "Test Item", "quantity": 1, "price": 100.0}
                ]
            }
        }
        
        result = await live_client.execute(mutation, variables)
        
        # Check for GraphQL errors
        if "errors" in result:
            pytest.fail(f"GraphQL errors: {result['errors']}")
        
        # Check mutation result
        data = result["data"]["result"]
        if data["__typename"] != "PurchaseGQLModel":
            pytest.fail(f"Insert failed: {data.get('msg', 'Unknown error')}")
        
        # Verify data
        assert data["id"] is not None
        assert data["status"] == "submitted"
        assert data["totalCost"] == 100.0
        
        return data["id"], data["lastchange"]
    
    @pytest.mark.asyncio
    async def test_purchase_query_live(self, live_client):
        """Test querying purchases from live server."""
        query = """
        query {
            purchases: purchasePage(skip: 0, limit: 10) {
                id
                status
                totalCost
                items {
                    name
                    quantity
                    price
                }
            }
        }
        """
        
        result = await live_client.execute(query)
        
        assert "errors" not in result
        assert "data" in result
        assert isinstance(result["data"]["purchases"], list)
    
    @pytest.mark.asyncio
    async def test_purchase_update_live(self, live_client):
        """Test updating a purchase via live API."""
        # First create a purchase
        purchase_id, lastchange = await self.test_purchase_insert_live(live_client)
        
        # Now update it
        mutation = """
        mutation($purchase: PurchaseUpdateGQLModel!) {
            result: purchaseUpdate(purchase: $purchase) {
                __typename
                ... on PurchaseGQLModel {
                    id
                    status
                    lastchange
                }
                ... on PurchaseGQLModelUpdateError {
                    msg
                }
            }
        }
        """
        
        variables = {
            "purchase": {
                "id": purchase_id,
                "lastchange": lastchange,
                "status": "approved"
            }
        }
        
        result = await live_client.execute(mutation, variables)
        
        assert "errors" not in result
        data = result["data"]["result"]
        assert data["__typename"] == "PurchaseGQLModel"
        assert data["status"] == "approved"
```

**Run Tests:**
```powershell
# Run live tests
pytest tests/test_purchases_live.py -v

# With output
pytest tests/test_purchases_live.py -v -s
```

### Phase 3: Federation Tests (1-2 days)

**Create test_federation.py:**
```python
"""
Apollo Federation Integration Tests
"""
import pytest
import pytest_asyncio
from tests.client import createFederationClient, createLiveClient

@pytest_asyncio.fixture
async def fed_client():
    """Federation client (Apollo Gateway)."""
    return createFederationClient(
        username="john.newbie@world.com",
        password="john.newbie@world.com"
    )

@pytest_asyncio.fixture
async def live_client():
    """Direct service client."""
    return createLiveClient(
        username="john.newbie@world.com",
        password="john.newbie@world.com"
    )

class TestFederationIntegration:
    """Test Apollo Federation gateway functionality."""
    
    @pytest.mark.asyncio
    async def test_cross_service_query(self, fed_client):
        """Test query spanning UG + Purchase services."""
        query = """
        query {
            me {
                id
                fullname
                email
            }
            purchases: purchasePage(limit: 5) {
                id
                status
                totalCost
            }
        }
        """
        
        result = await fed_client.execute(query)
        
        assert "errors" not in result
        assert "me" in result["data"]
        assert "purchases" in result["data"]
        assert result["data"]["me"]["email"] == "john.newbie@world.com"
    
    @pytest.mark.asyncio
    async def test_federation_vs_live_consistency(self, fed_client, live_client):
        """Verify federation returns same data as direct service."""
        query = """
        query {
            purchases: purchasePage(limit: 5) {
                id
                status
            }
        }
        """
        
        fed_result = await fed_client.execute(query)
        live_result = await live_client.execute(query)
        
        assert len(fed_result["data"]["purchases"]) == len(live_result["data"]["purchases"])
```

### Phase 4: Authorization Tests (If RBAC Implemented)

**Only implement if gql_property uses RBAC/group-based authorization!**

```python
"""
RBAC Authorization Tests - Purchase Service
"""
import pytest
import pytest_asyncio
from tests.client import createLiveClient

# Test users with different roles
TEST_USERS = {
    "editor": {
        "email": "editor@world.com",
        "password": "2222",
        "role": "editor",
        "dept": "Dept A1"
    },
    "viewer": {
        "email": "viewer@world.com", 
        "password": "2222",
        "role": "viewer",
        "dept": "Dept A1"
    },
    "other_dept": {
        "email": "other@world.com",
        "password": "2222",
        "role": "editor",
        "dept": "Dept A2"
    }
}

@pytest_asyncio.fixture
async def editor_client():
    return createLiveClient(
        username=TEST_USERS["editor"]["email"],
        password=TEST_USERS["editor"]["password"]
    )

@pytest_asyncio.fixture
async def viewer_client():
    return createLiveClient(
        username=TEST_USERS["viewer"]["email"],
        password=TEST_USERS["viewer"]["password"]
    )

class TestCreatorOwnership:
    """Test creator ownership - users own their purchases."""
    
    @pytest.mark.asyncio
    async def test_creator_can_update_own_purchase(self, editor_client):
        # User creates purchase
        purchase_id = await create_purchase(editor_client)
        
        # User can update their own purchase
        result = await update_purchase(editor_client, purchase_id)
        assert "errors" not in result
    
    @pytest.mark.asyncio
    async def test_viewer_cannot_create_purchase(self, viewer_client):
        # Viewer tries to create purchase (should fail)
        result = await create_purchase(viewer_client)
        
        # Check authorization failure
        assert "errors" in result or "msg" in result["data"]["purchaseInsert"]
```

### Phase 5: Performance Tests (Optional)

```python
"""
Performance Benchmarks
"""
import pytest
import pytest_asyncio
import time
import asyncio
from tests.client import createFederationClient

@pytest_asyncio.fixture
async def fed_client():
    return createFederationClient()

class TestPerformance:
    @pytest.mark.asyncio
    async def test_query_latency_threshold(self, fed_client):
        """Verify query completes within acceptable time."""
        query = """
        query {
            purchasePage(limit: 50) {
                id
                status
                totalCost
            }
        }
        """
        
        start = time.time()
        result = await fed_client.execute(query)
        latency = time.time() - start
        
        assert "errors" not in result
        assert latency < 2.0, f"Query took {latency:.2f}s (threshold: 2s)"
    
    @pytest.mark.asyncio
    async def test_concurrent_queries(self, fed_client):
        """Test handling 10 concurrent queries."""
        query = """query { purchasePage(limit: 10) { id } }"""
        
        tasks = [fed_client.execute(query) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert all("errors" not in r for r in results)
```

---

## 📊 Test Coverage Comparison

| Test Category | gql_evolution | gql_property (Current) | gql_property (Recommended) |
|---------------|---------------|------------------------|----------------------------|
| **Live Server Tests** | ✅ 34 tests | ❌ 0 tests | 🎯 15-20 tests |
| **Federation Tests** | ✅ 11 tests | ❌ 0 tests | 🎯 5-8 tests |
| **RBAC/Auth Tests** | ✅ 8 tests | ❌ 0 tests | 🎯 5-10 tests (if RBAC) |
| **Performance Tests** | ✅ 15 tests | ❌ 0 tests | 🎯 5-8 tests |
| **Unit Tests (SQLite)** | ✅ Minimal | ✅ 7 tests | ✅ Keep existing |
| **Total Live Tests** | ✅ 34 | ❌ 0 | 🎯 **30-46 tests** |

---

## 🚀 Quick Start for gql_property

### 1. Verify Services Running
```powershell
# Start Docker services
docker compose -f docker-compose.debug.yml up -d

# Check status
docker compose -f docker-compose.debug.yml ps
```

### 2. Copy Test Infrastructure
```powershell
# Copy client.py (universal test client)
Copy-Item "c:\Users\vojta\gql_evolution\tests\client.py" `
          "c:\Users\vojta\OneDrive\Plocha\barta_gql\gql_property\tests\" -Force

# Copy check_services.py (health checker)
Copy-Item "c:\Users\vojta\gql_evolution\tests\check_services.py" `
          "c:\Users\vojta\OneDrive\Plocha\barta_gql\gql_property\tests\" -Force
```

### 3. Update Environment Config
```python
# In tests/client.py, verify/update endpoints:
# - Federation: http://localhost:33000/api/gql (should be same)
# - Live service: http://localhost:8000/gql (verify port)
# - OAuth: http://localhost:33001/oauth/login3 (should be same)
```

### 4. Test Service Connectivity
```powershell
cd c:\Users\vojta\OneDrive\Plocha\barta_gql\gql_property
python tests\check_services.py
```

### 5. Create First Live Test
```powershell
# Create test_purchases_live.py (use template from Phase 2 above)
# Run test
pytest tests/test_purchases_live.py -v
```

---

## 🔍 Key Differences: gql_evolution vs gql_property

### Service Configuration

| Aspect | gql_evolution | gql_property |
|--------|---------------|--------------|
| **Service Name** | evolution | property |
| **Main Port** | 8000 | 8000 (verify!) |
| **Apollo Config** | `{"name": "evolution", "url": "..."}` | `{"name": "property", "url": "..."}` |
| **Proxy Target** | http://host.docker.internal:8000 | http://host.docker.internal:8001 ⚠️ |
| **Domain Model** | Agreements, Payments, Contacts | Purchases, Items |
| **RBAC** | ✅ Unified RBAC (creator + group) | ❓ Unknown - verify! |

### Test Data Users

**gql_evolution uses:**
- Realistic test users from systemdata.rnd.json
- Multiple departments/faculties
- Different role levels (viewer, editor, admin)

**gql_property should verify:**
- Does systemdata.rnd.json exist?
- Are test users configured?
- What roles/groups are available?

---

## 📋 Implementation Checklist

### Phase 1: Infrastructure ✅
- [ ] Copy `client.py` to gql_property/tests/
- [ ] Copy `check_services.py` to gql_property/tests/
- [ ] Update endpoint URLs in client.py (if needed)
- [ ] Verify services are running
- [ ] Test authentication flow
- [ ] Confirm test users exist in systemdata.rnd.json

### Phase 2: Basic Live Tests 🎯
- [ ] Create `test_purchases_live.py`
- [ ] Implement `test_purchase_insert_live`
- [ ] Implement `test_purchase_query_live`
- [ ] Implement `test_purchase_update_live`
- [ ] Implement `test_purchase_delete_live`
- [ ] Test nested items operations
- [ ] Verify optimistic locking

### Phase 3: Federation Tests 🔗
- [ ] Create `test_federation.py`
- [ ] Test Apollo Gateway connectivity
- [ ] Test cross-service queries (UG + Purchase)
- [ ] Compare federation vs direct results
- [ ] Test federation performance

### Phase 4: Authorization Tests (If RBAC) 🔒
- [ ] Verify RBAC is implemented
- [ ] Create `test_authorization.py`
- [ ] Test creator ownership
- [ ] Test group permissions
- [ ] Test cross-group access denial
- [ ] Test admin override

### Phase 5: Performance Tests 📊
- [ ] Create `test_performance.py`
- [ ] Benchmark query latency
- [ ] Test concurrent requests
- [ ] Test large dataset queries
- [ ] Test N+1 query prevention

### Documentation 📚
- [ ] Update tests/README.md
- [ ] Document test users
- [ ] Document test execution
- [ ] Add troubleshooting guide

---

## 🎓 Best Practices (from gql_evolution)

1. **Always use client.py** - Never write custom HTTP clients
2. **Test with multiple users** - Validate RBAC with different roles
3. **Check both error types** - GraphQL errors AND mutation-level errors
4. **Use fixtures for clients** - Consistent setup across tests
5. **Skip tests gracefully** - If prerequisite data missing, skip with message
6. **Clean up test data** - Use fixtures for lifecycle management
7. **Performance aware** - Tests should complete in <1 minute
8. **Live database robust** - Don't assume specific IDs exist

---

## 📚 Additional Resources

### From gql_evolution
- [tests/README.md](file:///c:/Users/vojta/gql_evolution/tests/README.md) - Complete test documentation
- [docs/testing/DEMO_TESTING_GUIDE.md](file:///c:/Users/vojta/gql_evolution/docs/testing/DEMO_TESTING_GUIDE.md) - Step-by-step testing guide
- [docs/testing/RBAC_TEST_QUERIES.md](file:///c:/Users/vojta/gql_evolution/docs/testing/RBAC_TEST_QUERIES.md) - Authorization test scenarios
- [docs/architecture/UNIFIED_RBAC_SYSTEM.md](file:///c:/Users/vojta/gql_evolution/docs/architecture/UNIFIED_RBAC_SYSTEM.md) - RBAC architecture

### For gql_property
- Verify if RBAC is implemented
- Check systemdata.rnd.json for test users
- Review docker-compose.debug.yml for service configuration
- Confirm Apollo Federation configuration

---

**Status:** Ready for Implementation  
**Estimated Effort:** 5-7 days for full live test suite  
**Next Step:** Phase 1 - Copy test infrastructure and verify services

---

## 💡 Quick Wins

**Start with these 3 tests to prove infrastructure works:**

1. **test_service_connectivity** - Verify all services running
2. **test_authentication** - Get JWT token from UG service
3. **test_simple_query** - Query purchases from live server

**Expected Time:** 2-3 hours to have these working

Once these pass, you have confidence to build out full test suite! 🚀
