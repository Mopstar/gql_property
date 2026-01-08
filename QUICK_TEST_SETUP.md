# Quick Test Setup Guide - gql_property

**5-Minute Setup for Live Testing**

---

## 🚀 Quick Start

### 1. Copy Test Infrastructure (30 seconds)
```powershell
# Copy universal test client
Copy-Item "c:\Users\vojta\gql_evolution\tests\client.py" `
          "c:\Users\vojta\OneDrive\Plocha\barta_gql\gql_property\tests\client.py" -Force

# Copy service checker
Copy-Item "c:\Users\vojta\gql_evolution\tests\check_services.py" `
          "c:\Users\vojta\OneDrive\Plocha\barta_gql\gql_property\tests\check_services.py" -Force
```

### 2. Start Services (1 minute)
```powershell
cd c:\Users\vojta\OneDrive\Plocha\barta_gql\gql_property
docker compose -f docker-compose.debug.yml up -d
```

### 3. Verify Connectivity (30 seconds)
```powershell
python tests\check_services.py
```

**Expected:**
```
✅ Agreement Service (Direct)      - Running
✅ Apollo Gateway (Federation)     - Running
✅ UG Service                      - Running
✅ Frontend                        - Running
✅ All services running!
```

### 4. Create First Live Test (2 minutes)

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
            status
            totalCost
        }
    }
    """
    
    result = await client.execute(query)
    
    assert "errors" not in result
    assert "data" in result
    print(f"✅ Found {len(result['data']['purchases'])} purchases")
```

### 5. Run Test (30 seconds)
```powershell
pytest tests/test_purchases_live.py -v -s
```

---

## ✅ Success Criteria

Your setup is working if:
- ✅ All 4 services show "Running" in check_services.py
- ✅ Test gets JWT token from UG service
- ✅ Test returns purchase data (or empty list if no data)
- ❌ No connection errors

---

## 🔧 Troubleshooting

### Services Not Running
```powershell
# Check Docker status
docker compose -f docker-compose.debug.yml ps

# Restart services
docker compose -f docker-compose.debug.yml down
docker compose -f docker-compose.debug.yml up -d
```

### Authentication Failed
- Verify UG service is running: http://localhost:33001
- Check test user exists in systemdata.rnd.json
- Try different user: "admin" / "admin"

### Connection Refused on Port 8000
- Check if main service is running
- Verify docker-compose.debug.yml configuration
- May need to start service manually:
```powershell
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --env-file environment.txt
```

---

## 📚 Next Steps

Once basic test works:
1. ✅ Add purchase insert test
2. ✅ Add purchase update test
3. ✅ Add federation test
4. ✅ Add authorization tests (if RBAC implemented)

See [LIVE_TEST_ANALYSIS.md](LIVE_TEST_ANALYSIS.md) for complete implementation guide.

---

**Time Investment:** 5 minutes to first working test  
**Reward:** Real integration testing with UG service + Apollo Federation! 🎉
