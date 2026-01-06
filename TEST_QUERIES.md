# GraphQL Authorization Test Queries

**Endpoint:** `http://localhost:8000/gql`  
**Playground:** `http://localhost:8000/ui`

---

## Query 1: Check Current User

```graphql
query WhoAmI {
  me {
    id
    fullname
    email
  }
}
```

---

## Query 2: Create Purchase (User A)

```graphql
mutation CreatePurchaseUserA {
  purchaseInsert(purchase: {
    reason: "Purchase by User A"
    description: "Testing creator ownership"
    status: "draft"
  }) {
    ... on PurchaseGQLModel {
      id
      reason
      status
      createdby { id }
      rbacobjectId
      created
      lastchange
    }
    ... on PurchaseGQLModelInsertError {
      msg
    }
  }
}
```

**Save the `id` and `lastchange` from response!**

---

## Query 3: List All Accessible Purchases

```graphql
query ListPurchases {
  purchasePage(skip: 0, limit: 20) {
    id
    reason
    description
    status
    createdby { id }
    rbacobjectId
    created
  }
}
```

---

## Query 4: Get Purchase by ID

```graphql
query GetPurchaseById {
  purchaseById(id: "PASTE_PURCHASE_ID_HERE") {
    id
    reason
    description
    status
    createdby { id }
    rbacobjectId
    created
    lastchange
  }
}
```

---

## Query 5: Update Own Purchase (Should Succeed)

```graphql
mutation UpdateOwnPurchase {
  purchaseUpdate(purchase: {
    id: "PASTE_YOUR_PURCHASE_ID"
    reason: "Updated by owner"
    status: "submitted"
    lastchange: "PASTE_LASTCHANGE_HERE"
  }) {
    ... on PurchaseGQLModel {
      id
      reason
      status
      lastchange
    }
    ... on PurchaseGQLModelUpdateError {
      msg
    }
  }
}
```

---

## Query 6: Try Update Other's Purchase (Should Fail)

```graphql
mutation UpdateOthersPurchase {
  purchaseUpdate(purchase: {
    id: "PASTE_OTHERS_PURCHASE_ID"
    reason: "Unauthorized update attempt"
    status: "approved"
    lastchange: "PASTE_THEIR_LASTCHANGE"
  }) {
    ... on PurchaseGQLModel {
      id
      reason
    }
    ... on PurchaseGQLModelUpdateError {
      msg
    }
  }
}
```

**Expected:** Authorization error - user is not creator and has no group permissions

---

## Query 7: Delete Purchase (Admin Only)

```graphql
mutation DeletePurchase {
  purchaseDelete(purchase: {
    id: "PASTE_PURCHASE_ID"
    lastchange: "PASTE_LASTCHANGE"
  }) {
    ... on PurchaseGQLModel {
      id
      msg
    }
    ... on PurchaseGQLModelDeleteError {
      msg
    }
  }
}
```

**Expected:** Succeeds only if user is creator OR has administrator role

---

## Query 8: Create Event (Alternative Entity)

```graphql
mutation CreateEvent {
  eventInsert(event: {
    name: "Test Event"
    startdate: "2026-02-01T10:00:00"
    enddate: "2026-02-01T12:00:00"
  }) {
    ... on EventGQLModel {
      id
      name
      startdate
      createdby { id }
      rbacobjectId
      lastchange
    }
    ... on EventGQLModelInsertError {
      msg
    }
  }
}
```

---

## Query 9: Update Event

```graphql
mutation UpdateEvent {
  eventUpdate(event: {
    id: "PASTE_EVENT_ID"
    name: "Updated Event Name"
    lastchange: "PASTE_LASTCHANGE"
  }) {
    ... on EventGQLModel {
      id
      name
      lastchange
    }
    ... on EventGQLModelUpdateError {
      msg
    }
  }
}
```

---

## Query 10: List Events

```graphql
query ListEvents {
  eventPage(skip: 0, limit: 10) {
    id
    name
    startdate
    enddate
    createdby { id }
    rbacobjectId
  }
}
```

---

## Testing Workflow

### Test 1: Creator Ownership
1. **User A** runs Query 2 (create purchase) → saves ID
2. **User A** runs Query 5 (update own) → ✅ succeeds
3. **User B** runs Query 6 (update A's purchase) → ❌ fails

### Test 2: Group Permissions
1. **User A** (in Group X) creates purchase
2. **User B** (in Group X with editor role) runs Query 6 → ✅ succeeds
3. **User C** (in Group Y) runs Query 6 → ❌ fails

### Test 3: Admin Privileges
1. **User A** creates purchase
2. **Admin User** runs Query 5 (update) → ✅ succeeds if admin in parent group
3. **Admin User** runs Query 7 (delete) → ✅ succeeds

### Test 4: Page Filtering
1. Create purchases with multiple users
2. Each user runs Query 3 → sees only their purchases + group-accessible ones
3. Admin user runs Query 3 → sees all purchases

---

## Expected Results Matrix

| Action | Creator | Same Group Editor | Different Group User | Admin (Parent Group) |
|--------|---------|-------------------|---------------------|---------------------|
| Create | ✅ | ✅ | ✅ | ✅ |
| Read Own | ✅ | ✅ | ✅ | ✅ |
| Update Own | ✅ | ✅ | ✅ | ✅ |
| Delete Own | ✅ | ❌ (needs admin) | ✅ | ✅ |
| Read Other's | ✅ (if creator) | ✅ | ❌ | ✅ |
| Update Other's | ✅ (if creator) | ✅ | ❌ | ✅ |
| Delete Other's | ✅ (if creator) | ❌ | ❌ | ✅ |

---

## Authentication Headers

Add to HTTP Headers in GraphQL Playground:

```json
{
  "Authorization": "Bearer YOUR_JWT_TOKEN"
}
```

Get JWT token from frontend: `http://localhost:33001`

---

## Troubleshooting

### Query returns `null` instead of data
- Check JWT token is valid
- Verify user is authenticated
- Check authorization logs

### "Insufficient permissions" error
- User is not creator
- User has no role in entity's group
- Check `rbacobject_id` and user's group memberships

### "Someone changed entity" error
- `lastchange` timestamp mismatch
- Use current `lastchange` value from latest query

---

## Quick Copy Template

```graphql
# 1. Create
mutation { purchaseInsert(purchase: {reason: "Test", status: "draft"}) { ... on PurchaseGQLModel { id lastchange } ... on PurchaseGQLModelInsertError { msg } } }

# 2. List
query { purchasePage(skip: 0, limit: 10) { id reason createdby { id } } }

# 3. Update (replace ID and lastchange)
mutation { purchaseUpdate(purchase: {id: "ID", reason: "Updated", lastchange: "TIMESTAMP"}) { ... on PurchaseGQLModel { id } ... on PurchaseGQLModelUpdateError { msg } } }
```
