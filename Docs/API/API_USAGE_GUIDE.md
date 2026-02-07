# API Usage Guide - gql_property

**Complete guide to using the GraphQL API with authentication and RBAC**

---

## Table of Contents

1. [Quick Start (5 minutes)](#1-quick-start-5-minutes)
2. [Authentication Setup](#2-authentication-setup)
3. [Understanding Auto-Managed Fields](#3-understanding-auto-managed-fields)
4. [CRUD Operations](#4-crud-operations)
5. [RBAC Authorization Examples](#5-rbac-authorization-examples)
6. [Advanced Queries & Filtering](#6-advanced-queries--filtering)
7. [Testing with Different Roles](#7-testing-with-different-roles)
8. [Federation Gateway Usage](#8-federation-gateway-usage)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Quick Start (5 minutes)

### Prerequisites

- Docker Desktop running
- Python 3.11+ with venv
- Services running (UG, Apollo Gateway, Purchase service)

### Step 1: Start Services (1 minute)

```powershell
cd E:\PyCharm_Projects\gql_property2
docker compose -f docker-compose.debug.yml up -d
```

### Step 2: Verify Services (30 seconds)

```powershell
# Check if all services are running
docker compose -f docker-compose.debug.yml ps

# Test service connectivity
curl http://localhost:33001  # Frontend
curl http://localhost:33000/api/gql  # Apollo Gateway
curl http://localhost:8001/gql  # Purchase Service
```

### Step 3: Get Authentication Token (1 minute)

**Option A: Use graphiql.html with browser**
1. Navigate to `http://localhost:33001`
2. Login with credentials
3. Copy JWT token from browser storage

**Option B: Get token via API**
```python
import httpx

async def get_token(username="john.newbie@world.com", password="john.newbie@world.com"):
    # Get challenge key
    key_resp = await httpx.get("http://localhost:33001/oauth/login")
    challenge_key = key_resp.json()["data"]
    
    # Get JWT token
    token_resp = await httpx.post(
        "http://localhost:33001/oauth/login",
        json={"username": username, "password": password, "key": challenge_key}
    )
    return token_resp.json()["data"]["token"]
```

### Step 4: First Query (1 minute)

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

**Headers:**
```
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
```

---

## 2. Authentication Setup

### Endpoints

| Service | URL | Purpose |
|---------|-----|---------|
| Purchase Service (Direct) | `http://localhost:8001/gql` | Development, full schema |
| Apollo Gateway (Federation) | `http://localhost:33000/api/gql` | Production-like, cross-service |
| Frontend (OAuth) | `http://localhost:33001` | User authentication |
| UG Service | `http://localhost:33001/api/gql` | User/Group management |

### Test Users (from systemdata.rnd.json)

| Username | Password | Role | Group |
|----------|----------|------|-------|
| john.newbie@world.com | john.newbie@world.com | editor | Department A1 |
| jane.admin@world.com | jane.admin@world.com | administrátor | Faculty A |
| admin | admin | rektor | Root (University) |

### Authentication Flow

```
1. User → Frontend /oauth/login (credentials)
2. Frontend → UG Service (validate user)
3. Frontend → User (JWT token)
4. User → Purchase Service (token in Authorization header)
5. Purchase Service → UG Service (validate token, get roles)
6. Purchase Service → User (data filtered by permissions)
```

---

## 3. Understanding Auto-Managed Fields

### ⚠️ Important: These Fields are Read-Only

The following fields are **automatically set** by the system and **cannot be specified** in mutations:

| Field | Set On | Purpose | Managed By |
|-------|--------|---------|------------|
| `createdby_id` | INSERT | Who created the entity | Your `user.id` from JWT |
| `rbacobject_id` | INSERT | Group ownership | Auto-assignment from your write groups |
| `changedby_id` | UPDATE | Who last modified | Your `user.id` from JWT |
| `created` | INSERT | Creation timestamp | Database `now()` |
| `lastchange` | INSERT/UPDATE | Last modification | Database `now()` |

### Why These Are Private

If users could set these manually, they could:
- ❌ Impersonate other users (`createdby_id`)
- ❌ Assign content to groups without permission (`rbacobject_id`)
- ❌ Hide who made changes (`changedby_id`)

### What Happens Automatically

```graphql
mutation CreatePurchase {
  purchaseInsert(purchase: {
    name: "Office Supplies"
    status: "pending"
    # DON'T specify: createdby_id, rbacobject_id, changedby_id
  }) {
    ... on PurchaseGQLModel {
      id
      name
      createdby_id     # ✅ Auto-set to YOUR user.id
      rbacobject_id    # ✅ Auto-set to your primary write group
      changedby_id     # ✅ Auto-set to YOUR user.id
      created          # ✅ Auto-set to current timestamp
    }
  }
}
```

---

## 4. CRUD Operations

### 4.1 CREATE (Insert)

#### Basic Purchase Insert

```graphql
mutation CreatePurchase {
  purchaseInsert(purchase: {
    name: "Office Supplies - January 2026"
    reason: "Quarterly supply restocking"
    description: "Paper, pens, staplers for main office"
    status: "draft"
    requested_delivery: "2026-02-15T00:00:00Z"
  }) {
    ... on PurchaseGQLModel {
      id
      name
      reason
      status
      createdby_id      # Your user.id
      rbacobject_id     # Your primary write group
      created
      lastchange
    }
    ... on InsertError {
      msg
      code  # UUID error code
    }
  }
}
```

#### Purchase with Items (Nested Insert)

```graphql
mutation CreatePurchaseWithItems {
  purchaseInsert(purchase: {
    name: "Office Supplies Bundle"
    reason: "New employee onboarding"
    status: "draft"
  }) {
    ... on PurchaseGQLModel {
      id
      name
      items {
        id
        name
        quantity
        price
      }
    }
    ... on InsertError {
      msg
      code
    }
  }
}

# Then add items separately
mutation AddItems {
  purchaseItemInsert(item: {
    purchase_id: "PURCHASE_ID_FROM_ABOVE"
    name: "Laptop"
    quantity: 1
    price: 1200.00
  }) {
    ... on PurchaseItemGQLModel {
      id
      name
      purchase_id
    }
    ... on InsertError {
      msg
    }
  }
}
```

### 4.2 READ (Query)

#### Get Purchase by ID

```graphql
query GetPurchase {
  purchase_by_id(id: "uuid-here") {
    id
    name
    reason
    description
    status
    requested_delivery
    submitted_at
    
    # Audit fields
    createdby_id
    rbacobject_id
    created
    lastchange
    
    # Relationships
    requester {
      id
      fullname
    }
    
    approver {
      id
      fullname
    }
    
    items {
      id
      name
      quantity
      price
    }
    
    masterpurchase {
      id
      name
    }
    
    subpurchases {
      id
      name
    }
  }
}
```

#### Page Query with Pagination

```graphql
query ListPurchases {
  purchase_page(skip: 0, limit: 20) {
    id
    name
    status
    requested_delivery
    createdby_id
    created
  }
}
```

#### Query Events

```graphql
query GetEvent {
  event_by_id(id: "uuid-here") {
    id
    name
    name_en
    description
    startdate
    enddate
    valid
    
    masterevent {
      id
      name
    }
    
    subevents {
      id
      name
    }
    
    user_invitations {
      id
      user {
        fullname
      }
      state
    }
  }
}
```

### 4.3 UPDATE

#### Update Purchase (with Optimistic Locking)

```graphql
mutation UpdatePurchase {
  purchase_update(purchase: {
    id: "uuid-here"
    name: "Updated Office Supplies"
    status: "submitted"
    lastchange: "2026-02-04T10:30:00Z"  # Current lastchange value!
  }) {
    ... on PurchaseGQLModel {
      id
      name
      status
      lastchange  # New timestamp
    }
    ... on UpdateError {
      msg
      code
    }
  }
}
```

**Note:** `lastchange` is required for optimistic locking. If another user modified the record, you'll get an error.

#### Update Event

```graphql
mutation UpdateEvent {
  event_update(event: {
    id: "uuid-here"
    name: "Updated Conference Title"
    startdate: "2026-03-15T09:00:00Z"
    enddate: "2026-03-17T17:00:00Z"
    lastchange: "CURRENT_LASTCHANGE_VALUE"
  }) {
    ... on EventGQLModel {
      id
      name
      startdate
      enddate
    }
    ... on UpdateError {
      msg
    }
  }
}
```

### 4.4 DELETE

#### Delete Purchase

```graphql
mutation DeletePurchase {
  purchase_delete(id: "uuid-here") {
    ... on DeleteResultGQLModel {
      id
      msg
    }
    ... on DeleteError {
      msg
      code
    }
  }
}
```

**Note:** Deleting a purchase will cascade-delete all its items if CASCADE is configured.

#### Delete Event Invitation

```graphql
mutation DeleteInvitation {
  eventinvitation_delete(id: "uuid-here") {
    ... on DeleteResultGQLModel {
      id
      msg
    }
    ... on DeleteError {
      msg
    }
  }
}
```

---

## 5. RBAC Authorization Examples

### 5.1 Creator Ownership

**Principle:** If you created it, you can always manage it (even if your role changes).

#### Test: Create → Demote Role → Still Update

```graphql
# Step 1: Create as editor
mutation {
  purchaseInsert(purchase: { name: "My Purchase" }) {
    ... on PurchaseGQLModel {
      id
      createdby_id  # Your user.id
    }
  }
}

# Step 2: Admin demotes you to viewer role
# (simulated by changing your role in UG service)

# Step 3: You can STILL update your purchase!
mutation {
  purchase_update(purchase: {
    id: "ID_FROM_STEP_1"
    name: "Updated despite being viewer"
    lastchange: "..."
  }) {
    ... on PurchaseGQLModel {
      id
      name  # ✅ SUCCESS - you're the creator!
    }
  }
}
```

### 5.2 Group Permissions

#### Viewer Can Read, Not Write

```graphql
# Login as user with "viewer" role in Department A

# ✅ Can query group's purchases
query {
  purchase_page(skip: 0, limit: 10) {
    id
    name
  }
}

# ❌ Cannot create purchase
mutation {
  purchaseInsert(purchase: { name: "Test" }) {
    ... on InsertError {
      msg  # "Permission denied - no required role for creation"
    }
  }
}
```

#### Editor Can Create & Update Group Content

```graphql
# Login as user with "editor" role in Department A

# ✅ Can create purchase
mutation {
  purchaseInsert(purchase: {
    name: "New Purchase"
  }) {
    ... on PurchaseGQLModel {
      id
      rbacobject_id  # Auto-assigned to Department A
    }
  }
}

# ✅ Can update other editors' purchases in same group
mutation {
  purchase_update(purchase: {
    id: "OTHER_EDITOR_PURCHASE_ID"
    name: "Updated by colleague"
    lastchange: "..."
  }) {
    ... on PurchaseGQLModel { id }
  }
}
```

#### Admin Can Manage All Department Content

```graphql
# Login as user with "administrátor" role in Faculty A

# ✅ Can see all purchases from Department A1, A2, A3 (child groups)
query {
  purchase_page(skip: 0, limit: 100) {
    id
    name
    rbacobject_id  # Will show A1, A2, A3
  }
}

# ✅ Can delete any department purchase
mutation {
  purchase_delete(id: "DEPT_A1_PURCHASE_ID") {
    ... on DeleteResultGQLModel { msg }
  }
}
```

### 5.3 Hierarchical Access

```graphql
# Group hierarchy example:
# University (root)
#   └─ Faculty A (administrátor = Jane)
#       ├─ Department A1 (editor = John)
#       └─ Department A2 (editor = Mary)

# Jane (Faculty A admin) can see ALL purchases from A1 and A2
query {
  purchase_page(skip: 0, limit: 100) {
    id
    name
    rbacobject_id  # Shows A1 and A2 purchases
  }
}

# John (Department A1 editor) can only see A1 purchases
query {
  purchase_page(skip: 0, limit: 100) {
    id
    name
    rbacobject_id  # Only A1 purchases
  }
}
```

### 5.4 Cross-Department Access Denied

```graphql
# Login as editor in Department A1

# ❌ Cannot see Department B1 purchases
query {
  purchase_by_id(id: "DEPT_B1_PURCHASE_ID") {
    id  # Returns NULL - cross-department denied
  }
}

# ❌ Cannot update Department B1 purchases
mutation {
  purchase_update(purchase: {
    id: "DEPT_B1_PURCHASE_ID"
    name: "Trying to hack"
    lastchange: "..."
  }) {
    ... on UpdateError {
      msg  # "Permission denied - not creator or group editor"
    }
  }
}
```

### 5.5 Root Admin Universal Access

```graphql
# Login as "rektor" (root admin)

# ✅ Can see ALL purchases across ALL departments
query {
  purchase_page(skip: 0, limit: 1000) {
    id
    name
    rbacobject_id  # All groups: A1, A2, B1, B2, C1...
  }
}

# ✅ Can update ANY purchase
mutation {
  purchase_update(purchase: {
    id: "ANY_PURCHASE_ID"
    status: "approved"
    lastchange: "..."
  }) {
    ... on PurchaseGQLModel { id }
  }
}

# ✅ Can delete ANY purchase
mutation {
  purchase_delete(id: "ANY_PURCHASE_ID") {
    ... on DeleteResultGQLModel { msg }
  }
}
```

---

## 6. Advanced Queries & Filtering

### 6.1 Filtering by Status

```graphql
query FilterByStatus {
  purchase_page(
    skip: 0
    limit: 20
    # Note: Advanced filters (_eq, _in) not yet implemented
    # Currently only exact match filtering available
  ) {
    id
    name
    status
  }
}
```

### 6.2 Relationship Queries

```graphql
query PurchaseWithRelationships {
  purchase_by_id(id: "uuid-here") {
    id
    name
    
    # User relationships (federated from UG service)
    requester {
      id
      fullname
      email
    }
    
    approver {
      id
      fullname
    }
    
    createdby {
      id
      fullname
    }
    
    changedby {
      id
      fullname
    }
    
    # Child items
    items {
      id
      name
      quantity
      price
    }
    
    # Hierarchical relationships
    masterpurchase {
      id
      name
    }
    
    subpurchases {
      id
      name
      status
    }
  }
}
```

### 6.3 Nested Event Queries

```graphql
query EventHierarchy {
  event_by_id(id: "uuid-here") {
    id
    name
    
    masterevent {
      id
      name
      
      masterevent {
        id
        name
        # Can nest further
      }
    }
    
    subevents {
      id
      name
      
      subevents {
        id
        name
      }
    }
    
    user_invitations {
      id
      user {
        fullname
      }
      event {
        name
      }
    }
  }
}
```

---

## 7. Testing with Different Roles

### 7.1 Test User Roles

Create test scenarios for each role type:

| Role | Can Create | Can Read Own | Can Read Group | Can Update Own | Can Update Group | Can Delete Own | Can Delete Group |
|------|-----------|--------------|----------------|----------------|------------------|----------------|------------------|
| **viewer** | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **editor** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **administrátor** | ✅ | ✅ | ✅ (hierarchical) | ✅ | ✅ (hierarchical) | ✅ | ✅ (hierarchical) |
| **rektor** (root) | ✅ | ✅ | ✅ (all) | ✅ | ✅ (all) | ✅ | ✅ (all) |

### 7.2 Test Scenarios

#### Scenario 1: Viewer Restrictions

```python
# tests/test_rbac_viewer.py
async def test_viewer_can_read_not_write():
    client = createLiveClient(
        username="viewer@example.com",
        password="password"
    )
    
    # ✅ Can query
    result = await client.execute("""
        query { purchase_page(limit: 5) { id name } }
    """)
    assert "errors" not in result
    
    # ❌ Cannot create
    result = await client.execute("""
        mutation {
            purchaseInsert(purchase: { name: "Test" }) {
                ... on InsertError { msg }
            }
        }
    """)
    assert "Permission denied" in result['data']['purchaseInsert']['msg']
```

#### Scenario 2: Creator Retention

```python
async def test_creator_retains_access_after_demotion():
    # Create as editor
    editor_client = createLiveClient("editor@example.com", "password")
    result = await editor_client.execute("""
        mutation {
            purchaseInsert(purchase: { name: "Test" }) {
                ... on PurchaseGQLModel { id lastchange }
            }
        }
    """)
    purchase_id = result['data']['purchaseInsert']['id']
    
    # Admin demotes user to viewer
    # (manual step or API call to UG service)
    
    # User can STILL update their purchase!
    viewer_client = createLiveClient("editor@example.com", "password")  # Same user, now viewer
    result = await viewer_client.execute(f"""
        mutation {{
            purchase_update(purchase: {{
                id: "{purchase_id}"
                name: "Updated"
                lastchange: "..."
            }}) {{
                ... on PurchaseGQLModel {{ id }}
            }}
        }}
    """)
    assert "errors" not in result  # ✅ Still works!
```

---

## 8. Federation Gateway Usage

### Why Use Federation Gateway?

- Combine queries across services (UG + Purchase in one request)
- Production-like environment testing
- Verify cross-service reference resolution

### Federation-Only Query Example

```graphql
# This ONLY works through Apollo Gateway (http://localhost:33000/api/gql)
# It combines Purchase service + UG service in one query

query CombinedQuery {
  # From Purchase service
  purchase_page(limit: 5) {
    id
    name
    status
    createdby_id
    
    # This resolver fetches from UG service!
    requester {
      id
      fullname
      email
      
      # User's roles from UG service
      roles {
        group {
          id
          name
        }
        roletype {
          name
        }
      }
    }
  }
  
  # From UG service
  me {
    id
    fullname
    
    # Can reference back to Purchase service
    # (if User type has field resolver)
  }
}
```

### Testing Federation

```python
# tests/test_federation.py
from tests.client import createFederationClient

async def test_federation_cross_service_query():
    client = createFederationClient(
        username="john.newbie@world.com",
        password="john.newbie@world.com"
    )
    
    result = await client.execute("""
        query {
            me {
                id
                fullname
            }
            purchase_page(limit: 3) {
                id
                name
                requester {
                    fullname
                }
            }
        }
    """)
    
    assert "errors" not in result
    assert result['data']['me'] is not None
    assert len(result['data']['purchase_page']) > 0
```

---

## 9. Troubleshooting

### Issue 1: "User not authenticated"

**Symptoms:**
```json
{
  "errors": [{
    "message": "User not authenticated",
    "extensions": { "code": "e1a2b3c4-5d6e-7f8g-9h0i-1j2k3l4m5n6o" }
  }]
}
```

**Solutions:**
1. Check Authorization header: `Authorization: Bearer YOUR_JWT_TOKEN`
2. Verify token is valid: `curl http://localhost:33001/oauth/userinfo -H "Authorization: Bearer TOKEN"`
3. Token may be expired - get new token
4. Check UG service is running: `curl http://localhost:33001`

### Issue 2: Empty Roles Array

**Symptoms:**
```json
{
  "data": {
    "me": {
      "fullname": "John Doe",
      "roles": []
    }
  }
}
```

**Solutions:**
1. Check user has roles assigned in UG service:
```graphql
query {
  user_by_id(id: "YOUR_USER_ID") {
    membership {
      group { name }
      roleType { name }
    }
  }
}
```
2. Verify UG service is running: `docker compose ps gql_ug`
3. Check demo data loaded: `DEMODATA=True` in environment
4. Restart services: `docker compose down && docker compose up -d`

### Issue 3: "Permission denied"

**Symptoms:**
```json
{
  "data": {
    "purchaseInsert": {
      "msg": "Permission denied - no required role for creation"
    }
  }
}
```

**Solutions:**
1. Check your roles: `query { me { roles { roletype { name } } } }`
2. Verify you have at least one of: editor, administrátor, vedoucí katedry, děkan, prorektor, rektor
3. If viewer/čtenář role → cannot create, only read
4. Contact admin to assign appropriate role

### Issue 4: "Stale data" / Optimistic Locking

**Symptoms:**
```json
{
  "data": {
    "purchase_update": {
      "msg": "Stale data - entity was modified by another user",
      "code": "c7d8e9f0-a1b2-4c5d-8e9f-0a1b2c3d4e5f"
    }
  }
}
```

**Solutions:**
1. Re-query to get current `lastchange` value:
```graphql
query { purchase_by_id(id: "...") { id lastchange } }
```
2. Use fresh `lastchange` in update mutation
3. This prevents lost updates in concurrent modifications

### Issue 5: Cross-Department Access Denied

**Symptoms:**
```graphql
query {
  purchase_by_id(id: "OTHER_DEPT_ID") {
    id  # Returns NULL
  }
}
```

**Solutions:**
1. This is EXPECTED behavior - cross-department access denied by design
2. Only purchase creator OR group members can access
3. To access: Be root admin, or have role in that group
4. Check purchase's `rbacobject_id` matches your accessible groups

### Issue 6: Services Not Running

```powershell
# Check service status
docker compose -f docker-compose.debug.yml ps

# Restart services
docker compose -f docker-compose.debug.yml down
docker compose -f docker-compose.debug.yml up -d

# View logs
docker compose -f docker-compose.debug.yml logs -f gql_ug
docker compose -f docker-compose.debug.yml logs -f apollo
```

---

## Quick Reference

### Useful Queries

```graphql
# Who am I?
query { me { id fullname email roles { group { name } roletype { name } } } }

# My purchases
query { purchase_page(limit: 20) { id name createdby_id } }

# Single purchase
query { purchase_by_id(id: "uuid") { id name items { name } } }

# All events
query { event_page(limit: 20) { id name startdate } }
```

### Error Code Quick Lookup

| Code Prefix | Category | Example |
|-------------|----------|---------|
| AUTH-001 | Authentication | Not authenticated |
| AUTH-002 | Authorization | No required role |
| AUTH-003 | Authorization | Not creator or editor |
| INSERT-001 | Database | Insert failed |
| UPDATE-001 | Database | Update failed / not found |
| UPDATE-005 | Concurrency | Stale data (optimistic locking) |
| DELETE-001 | Database | Delete failed |

Full error dictionary: [ERROR_HANDLING.md](ERROR_HANDLING.md)

---

**For more information:**
- Authorization model: [CREATOR_OWNERSHIP_GUIDE.md](CREATOR_OWNERSHIP_GUIDE.md)
- Error codes: [ERROR_CODES.md](ERROR_CODES.md)
- Project history: [ProjectTimeline.md](ProjectTimeline.md)

*Last Updated: 2026-02-04*
