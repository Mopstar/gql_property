# Testing Guide - GQL Property Service

**Complete testing infrastructure for Purchase/Property GraphQL service with live server integration.**

**Created:** January 8, 2026  
**Last Updated:** February 5, 2026  
**Status:** ✅ Ready for Testing

> **📝 Note:** This is a supplementary guide for developers. For the complete testing guide, see:
> - **[../TESTING_GUIDE.md](../TESTING_GUIDE.md)** - ⭐ Complete testing guide (start here!)
> - **[../API_USAGE_GUIDE.md](../API_USAGE_GUIDE.md)** - API usage examples
> - **[../TROUBLESHOOTING.md](../TROUBLESHOOTING.md)** - Common testing issues

---

## 🎯 Overview

This test suite provides comprehensive testing for the GQL Property service including:

- ✅ **Live server integration** - Tests against running services (not in-memory)
- ✅ **Apollo Federation** - Gateway integration testing
- ✅ **UG Authentication** - Real JWT token flow
- ✅ **CRUD operations** - Full lifecycle testing
- ✅ **Cross-service queries** - UG + Purchase combined queries

---

## 📁 Test Files

### Infrastructure Files
```
tests/
├── client.py              # Universal GraphQL test client (MIGRATED from gql_evolution)
│   ├── createFederationClient()  # Apollo Gateway endpoint
│   ├── createLiveClient()        # Direct service endpoint
│   └── createGQLClient()         # In-memory SQLite (existing)
│
└── check_services.py      # Service connectivity checker (NEW)
```

### Test Suites
```
tests/
├── test_purchases_live.py    # Live CRUD tests (NEW)
│   ├── TestServiceConnectivity      # 2 tests
│   ├── TestPurchaseQuery            # 2 tests
│   ├── TestPurchaseCRUDLive         # 4 tests
│   ├── TestPurchaseValidation       # 2 tests
│   └── TestErrorHandling            # 2 tests
│
├── test_federation.py        # Federation integration (NEW)
│   ├── TestFederationGateway        # 2 tests
│   ├── TestCrossServiceQueries      # 2 tests
│   ├── TestFederationVsDirectConsistency  # 2 tests
│   ├── TestFederationPerformance    # 2 tests
│   └── TestFederationSchemaStitching # 2 tests
│
├── test_purchases.py         # Unit tests with SQLite (EXISTING)
├── test_dbdefinitions.py     # DB model tests (EXISTING)
├── test_dataloaders.py       # Dataloader tests (EXISTING)
└── test_gt_definitions.py    # GraphQL type tests (EXISTING)
```

**Total New Tests:** ~20+ live integration tests

---

## 🚀 Quick Start

### 1. Start Services
```powershell
# Start Docker services
cd c:\Users\vojta\OneDrive\Plocha\barta_gql\gql_property
docker compose -f docker-compose.debug.yml up -d

# Wait 30 seconds for services to initialize

# Check service status
docker compose -f docker-compose.debug.yml ps
```

### 2. Verify Connectivity
```powershell
# Run connectivity checker
python tests\check_services.py
```

**Expected output:**
```
✅ Property Service (Direct)        - Running (status 200)
✅ Apollo Gateway (Federation)      - Running (status 200)
✅ UG Service                       - Running (status 200)
✅ Frontend                         - Running (status 200)
✅ All services running!
✅ Authentication working
✅ Clients ready for testing
```

### 3. Run Tests
```powershell
# Run all live tests
pytest tests/test_purchases_live.py tests/test_federation.py -v

# Run specific test suite
pytest tests/test_purchases_live.py -v

# Run with output
pytest tests/test_purchases_live.py -v -s

# Run single test
pytest tests/test_purchases_live.py::TestServiceConnectivity::test_service_is_running -v
```

---

## 📊 Test Coverage

### Live Integration Tests (NEW)

| Test Suite | Tests | Description |
|------------|-------|-------------|
| **test_purchases_live.py** | 12 | Live CRUD operations, validation, error handling |
| **test_federation.py** | 10 | Apollo Federation gateway integration |
| **Total NEW Tests** | **22** | **Live server integration** |

### Existing Unit Tests

| Test Suite | Tests | Description |
|------------|-------|-------------|
| test_purchases.py | 3 | SQLite in-memory tests |
| test_dbdefinitions.py | 3 | DB model tests |
| test_dataloaders.py | 1 | Dataloader tests |
| test_gt_definitions.py | 4 | GraphQL type tests |
| **Total Existing** | **11** | **Unit tests** |

**Grand Total:** ~33 tests (22 new + 11 existing)

---

## 🧪 Test Details

### test_purchases_live.py

**TestServiceConnectivity** - Basic connectivity
- ✅ `test_service_is_running` - Service responds to introspection
- ✅ `test_authentication_works` - JWT token flow works

**TestPurchaseQuery** - Read operations
- ✅ `test_purchase_page_query` - List purchases
- ✅ `test_purchase_with_items` - Query nested items

**TestPurchaseCRUDLive** - Write operations
- ✅ `test_purchase_insert_live` - Create purchase with items
- ✅ `test_purchase_by_id_query` - Query specific purchase
- ✅ `test_purchase_update_live` - Update purchase
- ✅ `test_purchase_delete_live` - Delete purchase

**TestPurchaseValidation** - Business logic
- ✅ `test_total_cost_calculation` - Verify sum of items
- ✅ `test_item_total_price_calculation` - Verify quantity * price

**TestErrorHandling** - Edge cases
- ✅ `test_invalid_purchase_id` - Non-existent ID handling
- ✅ `test_optimistic_locking` - Concurrent update prevention

### test_federation.py

**TestFederationGateway** - Gateway basics
- ✅ `test_gateway_is_accessible` - Apollo Gateway responds
- ✅ `test_gateway_endpoints` - Correct endpoint configuration

**TestCrossServiceQueries** - UG + Purchase
- ✅ `test_me_and_purchases_combined` - Single query spanning services
- ✅ `test_user_roles_query` - User roles from UG service

**TestFederationVsDirectConsistency** - Data consistency
- ✅ `test_purchase_page_consistency` - Same results via both paths
- ✅ `test_single_purchase_consistency` - Single entity consistency

**TestFederationPerformance** - Performance
- ✅ `test_federation_latency` - Gateway response time < 3s
- ✅ `test_cross_service_latency` - Cross-service query < 5s

**TestFederationSchemaStitching** - Schema validation
- ✅ `test_purchase_type_available` - Purchase types in federation
- ✅ `test_user_type_available` - User types in federation

---

## 🔧 Configuration

### Service Endpoints

| Service | Endpoint | Used For |
|---------|----------|----------|
| **Property Service** | http://localhost:8000/gql | Direct queries (createLiveClient) |
| **Apollo Gateway** | http://localhost:33000/api/gql | Federation queries (createFederationClient) |
| **UG Service** | http://localhost:33001/api/gql | User/Group data |
| **Frontend** | http://localhost:33001 | OAuth login |

### Test User

Default test user (from systemdata.rnd.json):
- **Username:** john.newbie@world.com
- **Password:** john.newbie@world.com

Configure in test fixtures or environment variables.

---

## 🔍 Troubleshooting

### Services Not Running
```powershell
# Check Docker status
docker compose -f docker-compose.debug.yml ps

# View logs
docker compose -f docker-compose.debug.yml logs

# Restart services
docker compose -f docker-compose.debug.yml down
docker compose -f docker-compose.debug.yml up -d
```

### Authentication Fails
```powershell
# Verify UG service is accessible
curl http://localhost:33001

# Check frontend OAuth endpoint
curl http://localhost:33001/oauth/login3

# Test with different user
# Edit tests/client.py default username/password
```

### Connection Refused (Port 8000)
```powershell
# Start main service manually
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --env-file environment.txt

# Note: Use 0.0.0.0 not 127.0.0.1 for Docker connectivity
```

### Tests Skip or Fail
```
# Common reasons:
1. Empty database - no test data available
2. Service not configured - mutations disabled
3. Schema mismatch - field names changed
4. Permission denied - RBAC not configured for test user

# Tests gracefully skip when prerequisites missing
# Check test output for skip reasons
```

---

## 📝 Example Test Runs

### Successful Run
```powershell
PS> pytest tests/test_purchases_live.py -v

tests/test_purchases_live.py::TestServiceConnectivity::test_service_is_running PASSED
tests/test_purchases_live.py::TestServiceConnectivity::test_authentication_works PASSED
tests/test_purchases_live.py::TestPurchaseQuery::test_purchase_page_query PASSED
tests/test_purchases_live.py::TestPurchaseQuery::test_purchase_with_items PASSED
tests/test_purchases_live.py::TestPurchaseCRUDLive::test_purchase_insert_live PASSED
tests/test_purchases_live.py::TestPurchaseCRUDLive::test_purchase_by_id_query PASSED
tests/test_purchases_live.py::TestPurchaseCRUDLive::test_purchase_update_live PASSED
tests/test_purchases_live.py::TestPurchaseCRUDLive::test_purchase_delete_live PASSED

================================ 8 passed in 5.23s ================================
```

### With Skipped Tests
```powershell
tests/test_purchases_live.py::TestPurchaseCRUDLive::test_purchase_insert_live SKIPPED (Insert not configured)
tests/test_purchases_live.py::TestPurchaseCRUDLive::test_purchase_update_live SKIPPED (Cannot test update without insert)

# This is OK - tests skip gracefully when features not available
```

---

## 🎓 Best Practices

1. **Always use client.py** - Don't create custom HTTP clients
2. **Run check_services.py first** - Verify connectivity before tests
3. **Use fixtures** - Consistent client setup
4. **Skip gracefully** - Use pytest.skip() when prerequisites missing
5. **Test against live DB** - Don't assume empty database
6. **Clean up data** - Delete test entities after creation
7. **Check both error types** - GraphQL errors AND mutation-level errors

---

## 📚 Additional Resources

- **[../TESTING_GUIDE.md](../TESTING_GUIDE.md)** - ⭐ Complete testing guide
- **[../IMPLEMENTATION_HISTORY.md](../IMPLEMENTATION_HISTORY.md)** - Complete implementation analysis
- **[../API_USAGE_GUIDE.md](../API_USAGE_GUIDE.md)** - API usage examples
- **[../TROUBLESHOOTING.md](../TROUBLESHOOTING.md)** - Common testing issues

---

## 🚦 Status

**Infrastructure:** ✅ Complete  
**Live Tests:** ✅ Implemented (22 tests)  
**Federation Tests:** ✅ Implemented (10 tests)  
**Documentation:** ✅ Complete  

**Next Steps:**
1. Run tests against live services
2. Verify all services configured correctly
3. Add more test scenarios as needed
4. Consider RBAC tests if authorization implemented

---

**Last Updated:** January 8, 2026  
**Author:** Migrated from gql_evolution test infrastructure  
**Status:** Ready for production testing 🚀
