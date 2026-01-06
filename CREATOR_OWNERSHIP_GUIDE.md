# Creator Ownership System - Quick Guide

## 🎯 The Big Idea: "If You Created It, You Can Manage It"

### The Problem with Traditional RBAC

```
❌ Traditional System:
User creates content as "editor" → Gets editor permissions
User demoted to "viewer" → LOSES ACCESS to own work!
User in high group without role → CAN'T SEE ANYTHING!
Result: Support tickets, frustration, locked content
```

### Our Solution: Creator Ownership + Group Permissions

```
✅ Unified RBAC System:
User creates content → Becomes OWNER (permanent)
User role changes → STILL owns their content
Group admin → CAN ALSO manage group content
Root admin → Sees everything
Result: Creators own their work, admins manage hierarchically
```

---

## 🔐 Authorization Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│          USER ATTEMPTS TO ACCESS PURCHASE #123               │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  CHECK 1: Is user the creator?        │
        │  (user.id == purchase.createdby_id)   │
        └───────────────────────────────────────┘
                            │
                    ┌───────┴───────┐
                    │               │
                  YES              NO
                    │               │
                    ▼               ▼
            ┌───────────┐   ┌──────────────────────────────┐
            │  ✅ ALLOW │   │  CHECK 2: Is user root admin? │
            │  FULL     │   │  (admin in root group)        │
            │  CRUD     │   └──────────────────────────────┘
            └───────────┘               │
                                ┌───────┴───────┐
                                │               │
                              YES              NO
                                │               │
                                ▼               ▼
                        ┌───────────┐   ┌─────────────────────────────┐
                        │  ✅ ALLOW │   │  CHECK 3: Group permissions? │
                        │  ALL      │   │  (has role in entity group)  │
                        │  ENTITIES │   └─────────────────────────────┘
                        └───────────┘               │
                                            ┌───────┴───────┐
                                            │               │
                                          YES              NO
                                            │               │
                                            ▼               ▼
                                    ┌───────────┐   ┌─────────────────────────────────┐
                                    │  ✅ ALLOW │   │  CHECK 4: Group membership?      │
                                    │  Based on │   │  (member without explicit role)  │
                                    │  Role     │   └─────────────────────────────────┘
                                    └───────────┘               │
                                                        ┌───────┴───────┐
                                                        │               │
                                                      YES              NO
                                                        │               │
                                                        ▼               ▼
                                                ┌───────────┐   ┌──────────┐
                                                │  ✅ ALLOW │   │  ❌ DENY │
                                                │  VIEW     │   │          │
                                                │  ONLY     │   └──────────┘
                                                └───────────┘
```

---

## 📊 Access Matrix

| Scenario | Creator Owner? | Group Member? | Has Role? | Root Admin? | Result |
|----------|---------------|---------------|-----------|-------------|--------|
| **Oliver created it** | ✅ YES | ❌ No | ❌ No | ❌ No | ✅ **ALLOW FULL** (creator) |
| **Estera in same dept** | ❌ No | ✅ YES | ✅ YES (editor) | ❌ No | ✅ **ALLOW FULL** (group editor) |
| **Ludvík (rector)** | ❌ No | ❌ No | ✅ YES (admin) | ✅ YES | ✅ **ALLOW ALL** (root admin) |
| **Jitka (viewer, same dept)** | ❌ No | ✅ YES | ✅ YES (viewer) | ❌ No | ✅ **ALLOW VIEW** (viewer role) |
| **Radomil (member, no role)** | ❌ No | ✅ YES | ❌ NO | ❌ No | ❌ **DENY** (needs explicit role) |
| **Valentin (other dept)** | ❌ No | ❌ NO | ❌ No | ❌ No | ❌ **DENY** |

---

## 🎬 Real-World Examples

### Example 1: Creator with Role Changes

```yaml
Timeline:
  Day 1:
    - Oliver has "editor" role in Dept-A
    - Oliver creates Purchase #123
    - System sets: purchase.createdby_id = Oliver.id
    - System sets: purchase.rbacobject_id = "Dept-A"
    
  Day 30:
    - Oliver promoted to "vedoucí katedry" (department head)
    - ✅ Oliver can STILL edit Purchase #123 (creator ownership)
    - ✅ Oliver can NOW create/edit OTHER Dept-A purchases (leadership role)
    
  Day 90:
    - Oliver demoted to "viewer" (read-only)
    - ✅ Oliver can STILL edit Purchase #123 (creator ownership)
    - ❌ Oliver CANNOT create NEW purchases (viewer role)
    - ❌ Oliver CANNOT edit OTHER purchases (viewer role)
    
  Day 365:
    - Oliver transfers to Dept-B (editor role)
    - ✅ Oliver can STILL edit Purchase #123 (creator ownership survives transfer!)
    - ✅ Oliver can create purchases in Dept-B
    - ✅ Dept-A admin can ALSO edit Purchase #123 (group permissions)
```

### Example 2: Multiple Admins Managing Same Content

```yaml
Purchase #456:
  createdby_id: Oliver.id
  rbacobject_id: "Dept-A"

Access Control:
  Oliver (creator):
    - ✅ Can read, update, delete Purchase #456
    - Reason: Creator ownership
    
  Estera (admin, Dept-A):
    - ✅ Can read, update, delete Purchase #456
    - Reason: Group admin permissions
    
  Zdenka (admin, Dept-A):
    - ✅ Can read, update, delete Purchase #456
    - Reason: Group admin permissions
    
  Ornela (admin, Faculty-A, parent of Dept-A):
    - ✅ Can read, update, delete Purchase #456
    - Reason: Hierarchical permissions (parent group)
    
  Valentin (admin, Dept-B):
    - ❌ Cannot access Purchase #456
    - Reason: Different department, not creator
```

### Example 3: Root Admin Universal Access

```yaml
Ludvík (rektor):
  role: "administrátor"
  group: University (no parent = root group)
  
Can access:
  - ✅ ALL Dept-A purchases
  - ✅ ALL Dept-B purchases
  - ✅ ALL Faculty-A purchases
  - ✅ ALL Faculty-B purchases
  - ✅ Everything in the system
  
No filtering applied!
```

---

## 💻 Code Examples

### Creating Content (Auto-Assignment)

```graphql
mutation {
  purchaseInsert(purchase: {
    name: "Office Supplies"
    status: "pending"
    # rbacobject_id NOT provided
  }) {
    ... on PurchaseGQLModel {
      id
      createdbyId  # ← Automatically set to your user.id
      rbacobjectId # ← Automatically set to your primary write group
    }
  }
}
```

**What happens:**
1. System checks your roles: Oliver has "editor" in Dept-A
2. Auto-assigns: `rbacobject_id = "Dept-A"`
3. Auto-assigns: `createdby_id = Oliver.id`
4. Oliver now owns this purchase forever!

### Querying with Permissions

```graphql
query {
  purchasePage(limit: 10) {
    id
    name
    createdbyId
    rbacobjectId
  }
}
```

**Filtering logic:**
```python
results = []
for purchase in all_purchases:
    # Check creator ownership
    if purchase.createdby_id == current_user.id:
        results.append(purchase)  # ✅ Your own content
        continue
    
    # Check group permissions
    if purchase.rbacobject_id in user_accessible_groups:
        results.append(purchase)  # ✅ Group content
        continue
    
    # Check root admin
    if user_is_root_admin:
        results.append(purchase)  # ✅ Root sees all
        continue

return results  # Only purchases you can access
```

---

## 🛠️ Implementation Details

### Database Schema Requirements

Every entity MUST have these audit fields:

```python
class PurchaseModel(BaseModel):
    id: Mapped[uuid.UUID] = ...
    name: Mapped[str] = ...
    
    # ⚠️ REQUIRED for creator ownership
    createdby_id: Mapped[uuid.UUID] = ...  # Who created this?
    
    # ⚠️ REQUIRED for group permissions
    rbacobject_id: Mapped[uuid.UUID | None] = ...  # Which group owns this?
    
    # Audit timestamps
    created: Mapped[datetime.datetime] = ...
    lastchange: Mapped[datetime.datetime] = ...
```

### Extension Configuration

```python
from .authz_extensions import (
    create_insert_permissions,
    create_update_permissions,
    create_delete_permissions,
    ROLES_WRITE,
    ROLES_DELETE
)

@strawberry.field(
    extensions=create_update_permissions(
        UpdateError[PurchaseGQLModel],
        PurchaseGQLModel,
        required_roles=ROLES_WRITE  # editor, admins, leadership
    )
)
async def purchase_update(self, info, purchase):
    return await Update[PurchaseGQLModel].DoItSafeWay(info=info, entity=purchase)
```

**Extension pipeline executes:**
1. ✅ Load existing entity from DB
2. ✅ Extract `rbacobject_id` from entity
3. ✅ Load user roles from UG service
4. ✅ **Check creator: Is user.id == entity.createdby_id?** ← Creator ownership
5. ✅ Check root admin: Admin in root group?
6. ✅ Check group: User has required role in entity's group?
7. ✅ Filter internal kwargs before calling resolver

---

## 📚 Testing Scenarios

### Test 1: Creator Updates Own Content After Demotion

```graphql
# Login as Oliver (viewer role - lowest permission)
# But Oliver created Purchase #123 earlier when he was editor

mutation {
  purchaseUpdate(purchase: {
    id: "123"
    name: "Updated Name"
  }) {
    ... on PurchaseGQLModel {
      id
      name
    }
    ... on PurchaseGQLModelUpdateError {
      msg  # Should NOT appear - creator can update!
    }
  }
}
```

**Expected:** ✅ SUCCESS (creator ownership overrides viewer role)

### Test 2: Admin Manages Other User's Content

```graphql
# Login as Estera (admin, Dept-A)
# Update Purchase #123 created by Oliver

mutation {
  purchaseUpdate(purchase: {
    id: "123"
    name: "Admin Updated"
  }) {
    ... on PurchaseGQLModel {
      id
      name
    }
  }
}
```

**Expected:** ✅ SUCCESS (group admin permissions)

### Test 3: Cross-Department Access Denied

```graphql
# Login as Valentin (admin, Dept-B)
# Try to access Purchase #123 (rbacobject_id = Dept-A)

query {
  purchaseById(id: "123") {
    id
    name
  }
}
```

**Expected:** ❌ NULL (no access - different department, not creator)

---

## 🔍 Troubleshooting

### "Permission denied" but I created this!

**Check:**
1. Is `createdby_id` set correctly?
   ```graphql
   query {
     purchaseById(id: "123") {
       createdbyId
     }
   }
   ```

2. Is your user.id matching?
   ```graphql
   query {
     me { id }
   }
   ```

### "I'm admin but can't access this"

**Check:**
1. What's the entity's group?
   ```graphql
   query {
     purchaseById(id: "123") {
       rbacobjectId
     }
   }
   ```

2. Are you admin in that group?
   ```graphql
   query {
     me {
       roles {
         roletype { name }
         group { id name }
       }
     }
   }
   ```

3. Is it hierarchical? Check parent groups.

---

## 🎓 Key Takeaways

1. **Creator ownership is permanent** - survives role changes, transfers, demotions
2. **Group admins have parallel access** - multiple users can manage same entity
3. **Explicit roles required** - users need assigned roles (viewer/editor/admin) for group access
4. **Root admins bypass everything** - universal access for top leadership
5. **Hierarchy matters** - parent group admins manage child content (one-way)
6. **Auto-assignment helps** - system picks appropriate group automatically

**Philosophy:** Users should never lose access to their own work. Group access requires explicit role assignment to ensure proper security boundaries!

---

## 📖 See Also

- [ROLES_DOCUMENTATION.md](ROLES_DOCUMENTATION.md) - Complete role definitions
- [authz_extensions.py](src/GraphTypeDefinitions/authz_extensions.py) - Implementation code
- [TEST_QUERIES.md](TEST_QUERIES.md) - GraphQL test queries
- [GQL_Agreement Reference](https://github.com/SickSkater/GQL_Agreement_Valiasek) - Original implementation
