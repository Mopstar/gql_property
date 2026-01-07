# Quick Start Guide: Implementing Auth from gql_evolution

## 🚀 Fast Track Implementation

This guide provides **copy-paste ready** code snippets to quickly implement the authentication system from gql_evolution into gql_property.

---

## Step 1: Update BaseModel (5 minutes)

**File:** `src/DBDefinitions/BaseModel.py`

**Find this:**
```python
class BaseModel(MappedAsDataclass, DeclarativeBase):
    id: Mapped[IDType] = UUIDColumn()
```

**Replace with:**
```python
import datetime
import sqlalchemy

class BaseModel(MappedAsDataclass, DeclarativeBase):
    """Base model with audit fields and RBAC support."""
    
    id: Mapped[IDType] = UUIDColumn()
    
    # Audit timestamps
    created: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        server_default=sqlalchemy.sql.func.now(),
        comment="timestamp of creation"
    )
    
    lastchange: Mapped[datetime.datetime] = mapped_column(
        default=None,
        nullable=True,
        server_default=sqlalchemy.sql.func.now(),
        onupdate=sqlalchemy.sql.func.now(),
        comment="timestamp of last modification"
    )
    
    # User tracking (references external UG service)
    createdby_id: Mapped[IDType] = UUIDFKey(
        comment="user who created this entity"
    )
    
    changedby_id: Mapped[IDType] = UUIDFKey(
        comment="user who last modified this entity"
    )
    
    # RBAC integration
    rbacobject_id: Mapped[IDType] = UUIDFKey(
        comment="group/rbac object for permissions"
    )
```

---

## Step 2: Add httpx Dependency (1 minute)

**File:** `requirements.txt`

**Add this line:**
```txt
httpx>=0.24.0
```

**Then run:**
```bash
pip install httpx
```

---

## Step 3: Update get_context() in main.py (10 minutes)

**File:** `main.py`

**Find the `get_context()` function and replace it with:**

```python
async def get_context(request: Request):
    """Build GraphQL context with UG service integration."""
    import httpx
    
    asyncSessionMaker = await RunOnceAndReturnSessionMaker()
    
    from src.Dataloaders import createLoadersContext
    context = createLoadersContext(asyncSessionMaker)
    
    result = {**context}
    result["request"] = request
    
    # Extract JWT from Authorization header or cookies
    auth_header = None
    try:
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    except Exception:
        auth_header = None
    
    if auth_header:
        result.setdefault('auth_header', auth_header)
    else:
        # Try common cookie names
        try:
            cookies = getattr(request, 'cookies', {}) or {}
            for ck in ('access_token', 'accessToken', 'token', 'AUTH_TOKEN'):
                if ck in cookies and cookies.get(ck):
                    token_val = cookies.get(ck)
                    if not token_val.lower().startswith('bearer '):
                        token_val = 'Bearer ' + token_val
                    result.setdefault('auth_header', token_val)
                    break
        except Exception:
            pass
    
    # Create UG client helper
    async def _ug_client(query, variables=None):
        """Query external User-Group service."""
        try:
            headers = {"Content-Type": "application/json"}
            if result.get('auth_header'):
                headers['Authorization'] = result.get('auth_header')
            
            endpoint = os.getenv('GQLUG_ENDPOINT_URL')
            if not endpoint:
                logging.warning('GQLUG_ENDPOINT_URL not configured')
                return {"errors": ["UG service not configured"]}
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    endpoint, 
                    json={"query": query, "variables": variables or {}}, 
                    headers=headers
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logging.debug(f"UG client failed: {e}")
            return {"errors": [str(e)]}
    
    result['ug_client'] = _ug_client
    
    # Resolve current user with roles
    try:
        me_resp = await _ug_client('''query { 
            me { 
                id 
                fullname 
                email 
                roles {
                    group { id name mastergroupId }
                    roletype { id name }
                }
            } 
        }''')
        me = None
        if isinstance(me_resp, dict):
            me = me_resp.get('data', {}).get('me')
        if me:
            result.setdefault('user', me)
    except Exception as e:
        logging.debug(f"Failed to resolve user: {e}")
    
    return result
```

---

## Step 4: Update environment.txt (2 minutes)

**File:** `environment.txt`

**Add these lines:**
```env
# External User-Group Service
GQLUG_ENDPOINT_URL=http://localhost:33001/api/gql
JWTPUBLICKEYURL=http://localhost:33001/oauth/publickey
JWTRESOLVEUSERPATHURL=http://localhost:33001/oauth/userinfo

# Demo Mode (set to False in production)
DEMO=True
DEMOUSER={"id": "2d9dc5ca-a4a2-11ed-b9df-0242ac120003", "fullname": "Demo User", "email": "demo@test.com", "roles": []}
```

---

## Step 5: Copy unified_rbac_extensions.py (5 minutes)

**Create:** `src/GraphTypeDefinitions/unified_rbac_extensions.py`

**Copy the entire file from:**
```
c:\Users\vojta\gql_evolution\src\GraphTypeDefinitions\unified_rbac_extensions.py
```

**Command:**
```bash
# From gql_property directory
copy "C:\Users\vojta\gql_evolution\src\GraphTypeDefinitions\unified_rbac_extensions.py" "src\GraphTypeDefinitions\unified_rbac_extensions.py"
```

---

## Step 6: Update Schema Extensions (3 minutes)

**File:** `src/GraphTypeDefinitions/__init__.py`

**Find the schema definition and update extensions:**

```python
schema = strawberry.federation.Schema(
    query=Query,
    mutation=Mutation,
    types=(UserGQLModel, BaseGQLModel),
    scalar_overrides={datetime.timedelta: timedelta._scalar_definition},
    extensions=[],
    schema_directives=[Relation]
)

# Add these extensions
from uoishelpers.schema import WhoAmIExtension, ProfilingExtension, PrometheusExtension
from uoishelpers.gqlpermissions.RolePermissionSchemaExtension import RolePermissionSchemaExtension

schema.extensions.append(WhoAmIExtension)
schema.extensions.append(ProfilingExtension)
schema.extensions.append(PrometheusExtension(prefix="GQL_Property"))
schema.extensions.append(RolePermissionSchemaExtension)
```

---

## Step 7: Update Purchase Mutations (10 minutes)

**File:** `src/GraphTypeDefinitions/PurchaseGQLModel.py`

**Add import at top:**
```python
from .unified_rbac_extensions import (
    create_unified_rbac_insert_extensions,
    create_unified_rbac_update_extensions,
    create_unified_rbac_delete_extensions,
    filter_by_unified_permissions,
    ROLES_WRITE,
    ROLES_DELETE,
    ROLES_READ
)
```

**Update purchase_insert:**

**Before:**
```python
@strawberry.field(
    description="Insert new purchase",
    permission_classes=[SimpleInsertPermission[PurchaseGQLModel]]
)
async def purchase_insert(self, info, purchase):
    return await Insert[PurchaseGQLModel].DoItSafeWay(info=info, entity=purchase)
```

**After:**
```python
@strawberry.field(
    description="Create purchase - user becomes creator",
    extensions=create_unified_rbac_insert_extensions(
        InsertError[PurchaseGQLModel],
        PurchaseGQLModel,
        required_roles=ROLES_WRITE
    )
)
async def purchase_insert(self, info, purchase):
    return await Insert[PurchaseGQLModel].DoItSafeWay(info=info, entity=purchase)
```

**Add update mutation if not exists:**
```python
@strawberry.field(
    description="Update purchase - creator or group admin",
    extensions=create_unified_rbac_update_extensions(
        UpdateError[PurchaseGQLModel],
        PurchaseGQLModel,
        required_roles=ROLES_WRITE
    )
)
async def purchase_update(self, info, purchase):
    return await Update[PurchaseGQLModel].DoItSafeWay(info=info, entity=purchase)
```

**Add delete mutation if not exists:**
```python
@strawberry.field(
    description="Delete purchase - creator or group admin",
    extensions=create_unified_rbac_delete_extensions(
        DeleteError[PurchaseGQLModel],
        PurchaseGQLModel,
        required_roles=ROLES_DELETE
    )
)
async def purchase_delete(self, info, purchase):
    return await Delete[PurchaseGQLModel].DoItSafeWay(info=info, entity=purchase)
```

**Update purchase_page query:**

**Before:**
```python
@strawberry.field(permission_classes=[OnlyForAuthentized])
async def purchase_page(self, info, skip: int = 0, limit: int = 10):
    resolver = PageResolver[PurchaseGQLModel](whereType=None)
    return await resolver(self, info, skip=skip, limit=limit)
```

**After:**
```python
@strawberry.field(permission_classes=[OnlyForAuthentized])
async def purchase_page(self, info, skip: int = 0, limit: int = 10):
    resolver = PageResolver[PurchaseGQLModel](whereType=None)
    all_results = await resolver(self, info, skip=skip, limit=limit)
    # Filter by unified permissions (creator OR group role)
    filtered_results = await filter_by_unified_permissions(
        info, all_results, required_roles=ROLES_READ
    )
    return filtered_results
```

---

## Step 8: Update Event Mutations (10 minutes)

**File:** `src/GraphTypeDefinitions/EventGQLModel.py`

**Add same imports as Purchase:**
```python
from .unified_rbac_extensions import (
    create_unified_rbac_insert_extensions,
    create_unified_rbac_update_extensions,
    create_unified_rbac_delete_extensions,
    filter_by_unified_permissions,
    ROLES_WRITE,
    ROLES_DELETE,
    ROLES_READ
)
```

**Update event_insert, event_update, event_delete using same pattern as Purchase**

**Update event_page query with filtering**

---

## Step 9: Reset Database (2 minutes)

**The database schema has changed! You need to recreate tables.**

**Option A: Drop and recreate (destroys data):**
```bash
# Set in environment.txt
DEMO=True  # This will drop and recreate tables
```

**Option B: Manual migration:**
```sql
-- Add new columns to existing tables
ALTER TABLE purchases ADD COLUMN created TIMESTAMP DEFAULT NOW();
ALTER TABLE purchases ADD COLUMN lastchange TIMESTAMP DEFAULT NOW();
ALTER TABLE purchases ADD COLUMN createdby_id UUID;
ALTER TABLE purchases ADD COLUMN changedby_id UUID;
ALTER TABLE purchases ADD COLUMN rbacobject_id UUID;

ALTER TABLE events ADD COLUMN created TIMESTAMP DEFAULT NOW();
ALTER TABLE events ADD COLUMN lastchange TIMESTAMP DEFAULT NOW();
ALTER TABLE events ADD COLUMN createdby_id UUID;
ALTER TABLE events ADD COLUMN changedby_id UUID;
ALTER TABLE events ADD COLUMN rbacobject_id UUID;

-- Repeat for all tables...
```

---

## Step 10: Test Basic Functionality (5 minutes)

**Start the server:**
```bash
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --env-file environment.txt --reload
```

**Test query:**
```graphql
query {
  purchasePage(skip: 0, limit: 10) {
    id
    reason
    created
    rbacobjectId
  }
}
```

**Test mutation:**
```graphql
mutation {
  purchaseInsert(purchase: {
    reason: "Test purchase"
    description: "Created with auth"
    # rbacobjectId auto-assigned from user's group!
  }) {
    ... on PurchaseGQLModel {
      id
      reason
      createdbyId  # Should be your user ID
      rbacobjectId  # Auto-assigned
    }
    ... on PurchaseGQLModelInsertError {
      msg
    }
  }
}
```

---

## Step 11: Add Docker Services (Optional, 15 minutes)

**File:** `docker-compose.debug.yml`

**Add UG service and dependencies:**
```yaml
services:
  gql_ug:
    image: hrbolek/gql_ug:latest
    ports:
      - "33012:8000"
    environment:
      - POSTGRES_HOST=postgres_gql:5432
      - DEMO=True
    depends_on:
      - postgres_gql

  postgres_gql:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: example
      POSTGRES_DB: data
    ports:
      - "5434:5432"
    volumes:
      - postgres_gql_data:/var/lib/postgresql/data

  frontend:
    image: hrbolek/gql_frontend:latest
    ports:
      - "33001:8080"
    environment:
      - GQL_PROXY=http://apollo:8000/api/gql

  apollo:
    build: ./proxy
    ports:
      - "33000:8000"
    environment:
      - GQL_ENDPOINT_PROPERTY=http://host.docker.internal:8000/gql
      - GQL_ENDPOINT_UG=http://gql_ug:8000/gql

volumes:
  postgres_gql_data:
```

**Start services:**
```bash
docker-compose -f docker-compose.debug.yml up -d
```

---

## 🎯 Verification Checklist

After completing all steps, verify:

- [ ] Server starts without errors
- [ ] Can query purchases/events
- [ ] `created` field populated automatically
- [ ] `createdby_id` set to your user ID on insert
- [ ] `rbacobject_id` auto-assigned on insert
- [ ] Can update your own entities
- [ ] Cannot update other users' entities
- [ ] Page queries only show accessible entities
- [ ] Error messages are clear

---

## 🐛 Troubleshooting

### "GQLUG_ENDPOINT_URL not configured"
**Solution:** Add to `environment.txt`:
```env
GQLUG_ENDPOINT_URL=http://localhost:33001/api/gql
```

### "User not authenticated"
**Solution:** Ensure `get_context()` resolves user correctly. Check logs for UG service errors.

### "Cannot auto-assign rbacobject_id"
**Solution:** User needs at least one group with editor/admin role in UG service.

### Column does not exist errors
**Solution:** Reset database with `DEMO=True` or run manual migration SQL.

### Import errors for unified_rbac_extensions
**Solution:** Ensure file copied correctly to `src/GraphTypeDefinitions/`

---

## 📚 Next Steps

Once basic auth works:

1. **Add tests** - Copy patterns from `gql_evolution/tests/test_rbac_queries.py`
2. **Update all entities** - Apply same pattern to Event, EventInvitation
3. **Document your setup** - Update README with auth instructions
4. **Production config** - Set `DEMO=False`, configure real UG service URL
5. **Monitor performance** - Check PrometheusExtension metrics

---

## 🆘 Need Help?

**Reference files in gql_evolution:**
- `.github/copilot-instructions.md` - Complete development guide
- `docs/architecture/UNIFIED_RBAC_SYSTEM.md` - Authorization details
- `docs/testing/DEMO_TESTING_GUIDE.md` - Test examples
- `src/GraphTypeDefinitions/AgreementGQLModel.py` - Full implementation example

**Estimated total time:** 1-2 hours for basic setup, 1-2 days for full implementation across all entities.

---

**Last Updated:** January 6, 2026
**Status:** Ready to implement
