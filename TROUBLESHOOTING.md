# Troubleshooting Guide

**Last Updated:** February 5, 2026  
**Purpose:** Common issues and solutions for gql_property

---

## Table of Contents

1. [Empty Roles Array](#empty-roles-array)
2. [Foreign Key Cascade Delete](#foreign-key-cascade-delete)
3. [Annotations AttributeError](#annotations-attributeerror)
4. [Service Connectivity](#service-connectivity)
5. [Authentication Issues](#authentication-issues)
6. [Permission Denied Errors](#permission-denied-errors)

---

## Empty Roles Array

### Problem
When querying `me { roles }`, the response shows empty roles array:
```json
{
  "data": {
    "me": {
      "fullname": "Ludvík Kilik",
      "id": "a0506cc4-5d53-4fdb-a989-c06a97e527fd",
      "roles": []
    }
  }
}
```

### Root Cause
The **User-Group (UG) service** is not returning roles. This can happen for several reasons.

### Solutions

#### 1. Check UG Service Is Running

**Verify service:**
```powershell
# Test if UG service responds
curl http://localhost:33001/api/gql -Method POST -Body '{"query":"{ __schema { types { name } } }"}' -ContentType "application/json"
```

**Start UG service:**
```powershell
# Using Docker Compose
docker-compose -f docker-compose.debug.yml up -d frontend

# Check logs
docker-compose -f docker-compose.debug.yml logs frontend
```

#### 2. Verify Data Loading

The UG service has its own PostgreSQL database that needs the roles data from `systemdata.rnd.json`.

**Check Docker logs:**
```powershell
docker-compose logs frontend
```

**Look for:**
- `"initializing system structures"`
- `"all done"`

**Verify mount:**
Check that `systemdata.rnd.json` is correctly mounted in `docker-compose.debug.yml`.

#### 3. Use Correct Query Field

Some implementations use `rolesOn` instead of `roles`.

**Solution:** Ensure using `roles` field:
```graphql
query {
  me {
    roles {  # ← Use 'roles', not 'rolesOn'
      group { id name mastergroupId }
      roletype { id name }
    }
  }
}
```

#### 4. Check Authentication Token

**Verify token:**
- Decode JWT at https://jwt.io
- Check expiration date
- Verify user ID matches expected user

#### 5. Mock Roles for Development

If you don't need the full UG service, modify `main.py` to use mock roles:

```python
# In get_context() function, after line 227:
if roles_count == 0:
    logging.warning(f"User {me.get('fullname')} has NO roles assigned!")
    # TEMPORARY: Add mock roles for testing
    if me.get('email') == 'Ludvik.Kilik@world.com':
        me['roles'] = [
            {
                'group': {
                    'id': 'd75d64a4-bf5f-43c5-9c14-8fda7aff6c09',
                    'name': 'Univerzita',
                    'mastergroupId': None
                },
                'roletype': {
                    'id': 'ced46aa4-3217-4fc1-b79d-f6be7d21c6b6',
                    'name': 'administrátor'
                }
            }
        ]
```

---

## Foreign Key Cascade Delete

### Problem

When deleting a purchase with child items, you get this error:
```
foreign key constraint "purchase_items_evolution_purchase_id_fkey" violated
Key (id)=(xxx) is still referenced from table "purchase_items_evolution"
```

### Root Cause

The database foreign key constraint was created WITHOUT `ON DELETE CASCADE`, so the database prevents deleting parent records when children exist.

The SQLAlchemy model has `cascade="all, delete-orphan"` configured, but this only works if the database constraint also allows it.

### Solution 1: Manual Deletion (Current Workaround)

Delete child items first, then delete the parent purchase:

```graphql
# Step 1: Delete all child items
mutation DeleteItems {
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
    lastchange: "PURCHASE_LASTCHANGE"
  })
}
```

### Solution 2: Fix Database Constraint (Recommended)

Add `ON DELETE CASCADE` to the foreign key constraint:

#### Step 1: Create Migration SQL

Create file `migrations/002_fix_cascade_delete.sql`:

```sql
-- Drop the existing constraint
ALTER TABLE purchase_items_evolution 
DROP CONSTRAINT IF EXISTS purchase_items_evolution_purchase_id_fkey;

-- Recreate with ON DELETE CASCADE
ALTER TABLE purchase_items_evolution
ADD CONSTRAINT purchase_items_evolution_purchase_id_fkey
FOREIGN KEY (purchase_id) 
REFERENCES purchases_evolution(id) 
ON DELETE CASCADE;
```

#### Step 2: Apply Migration

```powershell
# Using psql
psql -U your_username -d your_database -f migrations/002_fix_cascade_delete.sql

# Or using Docker
docker exec -i postgres_container psql -U username -d database < migrations/002_fix_cascade_delete.sql
```

#### Step 3: Update SQLAlchemy Model (Optional)

In `src/DBDefinitions/purchasemodel.py`, make cascade explicit:

```python
purchase_id: Mapped[IDType] = mapped_column(
    ForeignKey("purchases_evolution.id", ondelete="CASCADE"),
    index=True, 
    nullable=True, 
    default=None
)
```

#### Step 4: Verify

```graphql
# This should now work without manually deleting items
mutation DeletePurchaseWithItems {
  purchaseDelete(purchase: {
    id: "PURCHASE_WITH_ITEMS_ID"
    lastchange: "CURRENT_LASTCHANGE"
  })
}
```

**Expected:** Returns `null` (success), and all child items are automatically deleted.

---

## Annotations AttributeError

### Problem

When running the project, you encounter:
```
AttributeError: object has no attribute '__annotations__'
```

This typically occurs when calling create purchase mutations.

### Root Cause

This error occurs due to how Python handles class attributes and the interaction between:
1. Strawberry GraphQL decorators (`@strawberry.input`)
2. Mixin classes (`TreeInputStructureMixin`, `InputModelMixin`)
3. Python dataclass annotations

The mixins access the `__annotations__` attribute during initialization, but in some Python environments, this attribute may not be properly initialized.

### Solution

Explicitly initialize `__annotations__` as an empty dict at the beginning of input classes:

#### Files to Modify

**1. `src/GraphTypeDefinitions/PurchaseGQLModel.py`**
```python
@strawberry.input
class PurchaseInsertGQLModel(InputModelMixin, TreeInputStructureMixin):
    __annotations__ = {}  # ← Add this line
    
    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).purchases
    
    # ...rest of fields...
```

**2. `src/GraphTypeDefinitions/PurchaseItemGQLModel.py`**
```python
@strawberry.input
class PurchaseItemInsertGQLModel(InputModelMixin):
    __annotations__ = {}  # ← Add this line
    
    @classmethod
    def getLoader(cls, info: strawberry.types.Info):
        return getLoadersFromInfo(info).purchaseitems
    
    # ...rest of fields...
```

**3. `src/GraphTypeDefinitions/EventGQLModel.py`**
```python
@strawberry.input
class EventInsertGQLModel(InputModelMixin, TreeInputStructureMixin):
    __annotations__ = {}  # ← Add this line
    
    # ...rest of code...

@strawberry.input
class EventPlanInsertGQLModel(InputModelMixin):
    __annotations__ = {}  # ← Add this line
    
    # ...rest of code...
```

### Why This Works

By explicitly declaring `__annotations__ = {}`:
1. The class has the attribute when mixin's `__init__` is called
2. The Strawberry decorator still functions correctly
3. Works across different Python versions (3.9-3.13)

### Testing the Fix

```powershell
python -c "from src.GraphTypeDefinitions.PurchaseGQLModel import PurchaseInsertGQLModel; print('Has annotations:', hasattr(PurchaseInsertGQLModel, '__annotations__'))"
```

**Expected output:** `Has annotations: True`

---

## Service Connectivity

### Problem

Services not responding or connection refused errors.

### Solutions

#### 1. Check Docker Services

```powershell
# Check status
docker compose -f docker-compose.debug.yml ps

# Check logs
docker compose -f docker-compose.debug.yml logs [service-name]

# Restart all services
docker compose -f docker-compose.debug.yml down
docker compose -f docker-compose.debug.yml up -d
```

#### 2. Verify Ports

Ensure these ports are available:

| Service | Port | URL |
|---------|------|-----|
| Main Service | 8000 | http://localhost:8000/gql |
| Apollo Gateway | 33000 | http://localhost:33000/api/gql |
| UG Service | 33001 | http://localhost:33001/api/gql |
| Frontend | 3000 | http://localhost:3000 |
| PostgreSQL | 5432 | Internal |

```powershell
# Check if ports are in use
netstat -ano | findstr "8000"
netstat -ano | findstr "33000"
netstat -ano | findstr "33001"
```

#### 3. Run Connectivity Check

```powershell
python tests\check_services.py
```

#### 4. Check Environment Variables

Verify `environment.txt`:
```
POSTGRES_URL=postgresql+asyncpg://postgres:example@postgres_gql:5432/data
UG_ENDPOINT=http://gql_ug:8000/api/gql
```

---

## Authentication Issues

### Problem: Invalid Token

```json
{
  "errors": [{
    "message": "User not authenticated"
  }]
}
```

### Solutions

#### 1. Get Fresh Token

```python
import httpx
import asyncio

async def get_token():
    # Step 1: Get challenge key
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://localhost:33001/oauth/login")
        challenge_key = resp.json()["data"]
        
        # Step 2: Get JWT token
        resp = await client.post(
            "http://localhost:33001/oauth/login",
            json={
                "username": "Estera.Luckova@world.com",
                "password": "2222",
                "key": challenge_key
            }
        )
        return resp.json()["data"]["token"]

token = asyncio.run(get_token())
print(f"Token: {token}")
```

#### 2. Verify Token Format

Headers should be:
```
Authorization: Bearer YOUR_JWT_TOKEN_HERE
Content-Type: application/json
```

**Not:**
- `Authorization: YOUR_TOKEN` ❌
- `Bearer YOUR_TOKEN` ❌

#### 3. Check Token Expiration

Decode token at https://jwt.io and check `exp` field.

---

## Permission Denied Errors

### Error: "User does not have editor/admin role"

**UUID:** `f42da7e9-0b8b-4229-bc4b-c0dc73d55c3e`

### Cause

You're trying to CREATE but only have viewer role.

### Solution

1. Check your roles:
```graphql
query {
  me {
    roles {
      roletype { name }
      group { name }
    }
  }
}
```

2. Contact admin to assign editor/admin role, OR
3. Use a test user with editor role (e.g., `Oliver.Opletal@world.com`)

### Error: "Permission denied. You must be the creator or have role"

### Cause

You're trying to UPDATE/DELETE someone else's entity without proper group role.

### Solution

**Option 1:** Modify only your own created content

**Option 2:** Get editor/admin role in the entity's group:
```graphql
query CheckEntityGroup {
  purchaseById(id: "ENTITY_ID") {
    rbacobject { id name }
  }
}
```

Then request admin to add you to that group with editor/admin role.

**Option 3:** Use root admin account (e.g., `Ludvik.Kilik@world.com`)

---

## Additional Resources

- **[ERROR_CODES.md](ERROR_CODES.md)** - Complete error code dictionary
- **[API_USAGE_GUIDE.md](API_USAGE_GUIDE.md)** - API usage guide
- **[CREATOR_OWNERSHIP_GUIDE.md](CREATOR_OWNERSHIP_GUIDE.md)** - Authorization model
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing guide

For issues not covered here, check:
- Docker logs: `docker compose -f docker-compose.debug.yml logs`
- Application logs: Check console output
- Database logs: `docker compose logs postgres_gql`
