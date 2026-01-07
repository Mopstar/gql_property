# Complete CRUD Test Queries - Creator Ownership System

**Date:** January 6, 2026  
**Purpose:** Test all CRUD operations with creator ownership and role-based permissions

---

## ⚠️ Important: Auto-Managed Fields

The following fields are **automatically managed** by the system and **cannot be set manually** in mutations:

| Field | Auto-Set On | Purpose | Managed By |
|-------|-------------|---------|------------|
| `createdby_id` | INSERT | Tracks who created the entity | User context (your user.id) |
| `rbacobject_id` | INSERT | Assigns group ownership | Auto-assignment extension (your leaf write group) |
| `changedby_id` | UPDATE | Tracks who last modified | User context (your user.id) |

**Why?** These fields are marked as `strawberry.Private` to prevent security issues. If users could set them manually, they could:
- ❌ Claim to be a different user (`createdby_id`)
- ❌ Assign content to groups where they have no permissions (`rbacobject_id`)
- ❌ Hide who actually made changes (`changedby_id`)

**The system automatically:**
- ✅ Sets `createdby_id = your user.id` (you become the owner!)
- ✅ Sets `rbacobject_id = your most specific write group` (smart auto-assignment)
- ✅ Sets `changedby_id = your user.id` on updates (audit trail)

---

## 🔐 Prerequisites

### 1. Get Your User Info and Groups

```graphql
query GetMyInfo {
  me {
    id
    fullname
    email
    roles {
      roletype {
        name  # viewer, editor, administrátor, odpovědný řešitel, etc.
      }
      group {
        id
        name
        mastergroupId  # NULL = root group
      }
    }
  }
}
```

**What to note:**
- Your `user.id` - for checking creator ownership
- Your groups and roles - for permission testing
- If `mastergroupId` is NULL + role is "administrátor" = root admin

---

## 📝 CREATE Operations (INSERT)

**Important:** The `rbacobject_id` field is **private** and cannot be set in mutations. The authorization system automatically assigns it based on your write groups. This prevents users from assigning content to groups where they don't have permissions.

### Test 1: Basic Insert with Auto-Assignment

```graphql
mutation CreatePurchaseBasic {
  purchaseInsert(purchase: {
    name: "Office Supplies - January 2026"
    status: "pending"
    path: "/purchases/2026/office"
    # rbacobject_id NOT provided - will auto-assign to your primary write group
  }) {
    ... on PurchaseGQLModel {
      id
      name
      status
      createdbyId      # Should equal your user.id
      rbacobjectId     # Auto-assigned to your primary write group
      created
      lastchange
    }
    ... on PurchaseGQLModelInsertError {
      msg
    }
  }
}
```

**Expected Result:**
- ✅ SUCCESS if you have editor/admin/leadership role
- `createdbyId` = your user.id (you become the owner!)
- `rbacobjectId` = your primary write group (auto-assigned)
- ❌ ERROR if you only have viewer/čtenář role: "User does not have editor/admin role"

---

### Test 3: Insert with Child Items (Nested Insert)

```graphql
mutation CreatePurchaseWithItems {
  purchaseInsert(purchase: {
    name: "Office Supplies Bundle"
    status: "pending"
    path: "/purchases/2026/bundle"
    items: [
      {
        name: "Printer Paper A4"
        quantity: 10
        price: 5.99
      }
      {
        name: "Ballpoint Pens"
        quantity: 50
        price: 0.50
      }
      {
        name: "Stapler"
        quantity: 3
        price: 12.99
      }
    ]
  }) {
    ... on PurchaseGQLModel {
      id
      name
      createdbyId
      rbacobjectId
      items {
        id
        name
        quantity
        price
        purchaseId  # Should match parent purchase.id
      }
    }
    ... on PurchaseGQLModelInsertError {
      msg
    }
  }
}
```

**Expected Result:**
- ✅ SUCCESS - parent and all children created
- All items inherit parent's context
- Total 3 items created with correct `purchaseId`

---

### Test 4: Insert by Different Roles (Permission Testing)

**As Viewer (Should FAIL):**
```graphql
# Login as user with only "viewer" or "čtenář" role
mutation CreateAsViewer {
  purchaseInsert(purchase: {
    name: "This should fail"
    status: "pending"
  }) {
    ... on PurchaseGQLModel { id }
    ... on PurchaseGQLModelInsertError {
      msg  # Expected: "User does not have editor/admin role"
    }
  }
}
```

**As Editor (Should SUCCEED):**
```graphql
# Login as user with "editor" role
mutation CreateAsEditor {
  purchaseInsert(purchase: {
    name: "Editor created purchase"
    status: "pending"
  }) {
    ... on PurchaseGQLModel {
      id
      createdbyId  # Your user.id
    }
  }
}
```

**As Leadership (Should SUCCEED):**
```graphql
# Login as user with "děkan", "rektor", "vedoucí katedry" role
mutation CreateAsLeader {
  purchaseInsert(purchase: {
    name: "Leadership purchase"
    status: "approved"
  }) {
    ... on PurchaseGQLModel {
      id
      createdbyId  # Your user.id
    }
  }
}
```

---

## 👁️ READ Operations (QUERY)

### Test 5: Query By ID (Creator Access)

```graphql
query GetPurchaseById {
  purchaseById(id: "PASTE_PURCHASE_ID_HERE") {
    id
    name
    status
    path
    createdbyId
    rbacobjectId
    created
    lastchange
    items {
      id
      name
      quantity
      price
    }
  }
}
```

**Test Scenarios:**
- ✅ Query YOUR purchase (you created it) → SUCCESS (creator ownership)
- ✅ Query purchase in YOUR group (group permissions) → SUCCESS
- ✅ Query ANY purchase as root admin → SUCCESS (universal access)
- ❌ Query purchase from OTHER group (you're not creator) → NULL

---

### Test 6: Page Query with Creator Filtering

```graphql
query ListMyPurchases {
  purchasePage(skip: 0, limit: 20) {
    id
    name
    status
    createdbyId
    rbacobjectId
    created
  }
}
```

**Expected Result:**
- Returns purchases where:
  - `createdbyId` = your user.id (YOUR purchases) OR
  - `rbacobjectId` in your accessible groups (GROUP purchases) OR
  - You're root admin (ALL purchases)
- Automatically filtered based on your permissions!

---

### Test 7: Check Who Can See What

**Step 1: Create test purchase (as User A):**
```graphql
mutation UserACreatesPurchase {
  purchaseInsert(purchase: {
    name: "User A Purchase"
    status: "pending"
  }) {
    ... on PurchaseGQLModel {
      id  # Save this ID
      createdbyId
      rbacobjectId
    }
  }
}
```

**Step 2: Try to access as User B (same group, admin):**
```graphql
# Login as User B (admin in same group)
query UserBAccessesUserAPurchase {
  purchaseById(id: "ID_FROM_STEP_1") {
    id
    name
    createdbyId  # Shows User A's ID
  }
}
```
**Expected:** ✅ SUCCESS (group admin can see it)

**Step 3: Try to access as User C (different group):**
```graphql
# Login as User C (admin in different group)
query UserCAccessesUserAPurchase {
  purchaseById(id: "ID_FROM_STEP_1") {
    id
    name
  }
}
```
**Expected:** ❌ NULL (cross-department denied)

---

## ✏️ UPDATE Operations

### Test 8: Update Own Content (Creator Ownership)

**Setup:** First create a purchase, then try to update it after role change

**Step 1: Create as editor:**
```graphql
# Login as user with "editor" role
mutation CreateForUpdateTest {
  purchaseInsert(purchase: {
    name: "Original Name"
    status: "pending"
  }) {
    ... on PurchaseGQLModel {
      name
      status
      id           # Save this
      lastchange   # Save this for optimistic locking
      createdbyId  # Your user.id
    }
  }
}
```

**Step 2: Update (even if demoted to viewer):**
```graphql
# Even if you now only have "viewer" role
mutation UpdateOwnPurchase {
  purchaseUpdate(purchase: {
    id: "ID_FROM_STEP_1"
    name: "Updated Name - I still own this!"
    lastchange: "LASTCHANGE_FROM_STEP_1"  # For optimistic locking
  }) {
    ... on PurchaseGQLModel {
      id
      name          # Should show "Updated Name..."
      lastchange    # New timestamp
    }
    ... on PurchaseGQLModelUpdateError {
      msg
    }
  }
}
```

**Expected Result:**
- ✅ SUCCESS even as "viewer" - you're the creator!
- `name` updated successfully
- New `lastchange` timestamp

---

### Test 9: Admin Updates Other User's Content

```graphql
# Login as admin in same group
mutation AdminUpdatesUserContent {
  purchaseUpdate(purchase: {
    id: "SOME_USER_PURCHASE_ID"
    name: "Admin modified this"
    status: "approved"
    lastchange: "CURRENT_LASTCHANGE_VALUE"
  }) {
    ... on PurchaseGQLModel {
      id
      name
      createdbyId  # Still shows original creator
    }
    ... on PurchaseGQLModelUpdateError {
      msg
    }
  }
}
```

**Expected Result:**
- ✅ SUCCESS if you're admin in the same group
- Content modified but `createdbyId` unchanged (original creator preserved)

---

### Test 10: Cross-Department Update (Should FAIL)

```graphql
# Login as admin in Dept-A
# Try to update purchase from Dept-B
mutation CrossDeptUpdate {
  purchaseUpdate(purchase: {
    id: "DEPT_B_PURCHASE_ID"
    name: "Trying to update other dept"
    lastchange: "CURRENT_LASTCHANGE"
  }) {
    ... on PurchaseGQLModel { id }
    ... on PurchaseGQLModelUpdateError {
      msg  # Expected: "Permission denied. You must be the creator or have editor role..."
    }
  }
}
```

**Expected Result:**
- ❌ ERROR unless you're the creator or root admin
- Different department = no access

---

### Test 11: Optimistic Locking Test

```graphql
mutation UpdateWithWrongTimestamp {
  purchaseUpdate(purchase: {
    id: "SOME_PURCHASE_ID"
    name: "This will fail"
    lastchange: "2020-01-01T00:00:00.000Z"  # Old/wrong timestamp
  }) {
    ... on PurchaseGQLModel { id }
    ... on PurchaseGQLModelUpdateError {
      msg  # Expected: "Someone changed entity"
    }
  }
}
```

**Expected Result:**
- ❌ ERROR - optimistic lock prevents stale updates
- Message indicates concurrent modification

---

### Test 12: Update Child Items

```graphql
mutation UpdatePurchaseItem {
  purchaseItemUpdate(item: {
    id: "ITEM_ID"
    name: "Updated Item Name"
    quantity: 20
    price: 6.99
    lastchange: "CURRENT_ITEM_LASTCHANGE"
  }) {
    ... on PurchaseItemGQLModel {
      id
      name
      quantity
      price
    }
    ... on PurchaseItemGQLModelUpdateError {
      msg
    }
  }
}
```

**Expected Result:**
- ✅ SUCCESS if you can update parent purchase
- Child authorization inherits from parent

---

## 🗑️ DELETE Operations

⚠️ **Database Configuration:** After applying the CASCADE DELETE migration, child items are automatically deleted when you delete a parent purchase. If you haven't applied the migration yet, you must manually delete items first (see [FIX_CASCADE_DELETE.md](FIX_CASCADE_DELETE.md)).

### Test 13: Delete Own Content (Creator)

**With CASCADE DELETE (After Migration):**
```graphql
mutation DeleteOwnPurchase {
  purchaseDelete(purchase: {
    id: "YOUR_PURCHASE_ID"
    lastchange: "CURRENT_LASTCHANGE"
  }) {
    # Returns null on success, or error object on failure
    # Child items automatically deleted!
    ... on PurchaseGQLModelDeleteError {
      msg
    }
  }
}
```

**Without CASCADE DELETE (Before Migration):**

<details>
<summary>Click to expand manual deletion workflow</summary>

**Step 1: Check if purchase has items:**
```graphql
query CheckPurchaseItems {
  purchaseById(id: "YOUR_PURCHASE_ID") {
    id
    items {
      id
      name
    }
  }
}
```

**Step 2: Delete all items first (if any):**
```graphql
mutation DeletePurchaseItem {
  purchaseItemDelete(item: {
    id: "ITEM_ID"
    lastchange: "ITEM_LASTCHANGE"
  }) {
    ... on PurchaseItemGQLModelDeleteError {
      msg
    }
  }
}
```
**Repeat for each item** in the purchase.

**Step 3: Delete the purchase:**
```graphql
mutation DeleteOwnPurchase {
  purchaseDelete(purchase: {
    id: "YOUR_PURCHASE_ID"
    lastchange: "CURRENT_LASTCHANGE"
  }) {
    ... on PurchaseGQLModelDeleteError {
      msg
    }
  }
}
```

</details>

**Expected Result:**
- ✅ SUCCESS if you're creator (permanent ownership)
- ✅ SUCCESS if you're admin/administrátor/top leadership
- Returns `null` on success (no data returned)
- With CASCADE: Child items automatically deleted
- Without CASCADE: Error if items exist
- ❌ ERROR if you're only editor (delete requires admin role)

---

### Test 14: Admin Deletes User Content

```graphql
# Login as user with "administrátor" role
mutation AdminDeletesUserContent {
  purchaseDelete(purchase: {
    id: "OTHER_USER_PURCHASE_ID"
    lastchange: "CURRENT_LASTCHANGE"
  }) {
    # Returns null on success, or error object on failure
    ... on PurchaseGQLModelDeleteError {
      msg
    }
  }
}
```

**Expected Result:**
- ✅ SUCCESS if you have admin role (administrátor, admin, rektor, děkan)
- ❌ ERROR if you only have editor role: "Permission denied. You must be the creator or have administrátor role..."

---

### Test 15: Editor Cannot Delete (Even Own Content)

```graphql
# Login as user with only "editor" role
mutation EditorTriesToDelete {
  purchaseDelete(purchase: {
    id: "OWN_PURCHASE_ID"  # Even your own purchase!
    lastchange: "CURRENT_LASTCHANGE"
  }) {
    # Returns null on success, or error object on failure
    ... on PurchaseGQLModelDeleteError {
      msg  # Expected: "Permission denied. You must have administrátor role..."
    }
  }
}
```

**Expected Result:**
- ❌ ERROR - editor can create/update but NOT delete
- Delete requires admin role (5 roles only)

---

## 🎭 Multi-User Scenarios

### Scenario A: Creator with Role Change Timeline

**Day 1 - Create as Editor:**
```graphql
# Login as Oliver (editor)
mutation Day1_Create {
  purchaseInsert(purchase: {
    name: "Oliver's Purchase"
    status: "pending"
  }) {
    ... on PurchaseGQLModel {
      id  # Save as OLIVER_PURCHASE_ID
      createdbyId
    }
  }
}
```

**Day 30 - Update after promotion to Department Head:**
```graphql
# Oliver now has "vedoucí katedry" role
mutation Day30_UpdateAsLeader {
  purchaseUpdate(purchase: {
    id: "OLIVER_PURCHASE_ID"
    status: "approved"
    lastchange: "..."
  }) {
    ... on PurchaseGQLModel {
      id
      status  # Updated to "approved"
    }
  }
}
```
**Result:** ✅ SUCCESS (creator ownership + leadership role)

**Day 90 - Update after demotion to Viewer:**
```graphql
# Oliver now only has "viewer" role (read-only)
mutation Day90_UpdateAsViewer {
  purchaseUpdate(purchase: {
    id: "OLIVER_PURCHASE_ID"
    name: "Still mine!"
    lastchange: "..."
  }) {
    ... on PurchaseGQLModel {
      id
      name  # Updated successfully!
    }
  }
}
```
**Result:** ✅ SUCCESS (creator ownership overrides viewer role!)

**Day 90 - Try to create NEW purchase as Viewer:**
```graphql
mutation Day90_CreateAsViewer {
  purchaseInsert(purchase: {
    name: "New purchase as viewer"
  }) {
    ... on PurchaseGQLModelInsertError {
      msg  # "User does not have editor/admin role"
    }
  }
}
```
**Result:** ❌ FAIL (viewer role cannot create)

---

### Scenario B: Department Admin vs Creator

**Setup:**
```graphql
# User A (editor, Dept-A) creates purchase
mutation UserA_Creates {
  purchaseInsert(purchase: {
    name: "User A's purchase"
  }) {
    ... on PurchaseGQLModel {
      id  # SHARED_PURCHASE_ID
      rbacobjectId  # Dept-A
    }
  }
}
```

**Both can update:**
```graphql
# User A (creator) updates
mutation UserA_Updates {
  purchaseUpdate(purchase: {
    id: "SHARED_PURCHASE_ID"
    name: "User A modified"
    lastchange: "..."
  }) {
    ... on PurchaseGQLModel { name }
  }
}

# User B (admin, Dept-A) ALSO updates
mutation UserB_Updates {
  purchaseUpdate(purchase: {
    id: "SHARED_PURCHASE_ID"
    name: "Admin B modified"
    lastchange: "..."
  }) {
    ... on PurchaseGQLModel { name }
  }
}
```
**Result:** ✅ BOTH succeed (creator ownership + group admin permissions)

---

### Scenario C: Cross-Department Transfer

**Setup:**
```graphql
# Oliver (editor, Dept-A) creates purchase
mutation OliverInDeptA {
  purchaseInsert(purchase: {
    name: "Created in Dept-A"
  }) {
    ... on PurchaseGQLModel {
      id  # TRANSFER_PURCHASE_ID
      rbacobjectId  # Dept-A
    }
  }
}
```

**After transfer to Dept-B:**
```graphql
# Oliver now has roles in Dept-B (no longer in Dept-A)
mutation OliverInDeptB_UpdatesOldPurchase {
  purchaseUpdate(purchase: {
    id: "TRANSFER_PURCHASE_ID"  # Still in Dept-A!
    name: "Updated from Dept-B"
    lastchange: "..."
  }) {
    ... on PurchaseGQLModel {
      id
      name
    }
  }
}
```
**Result:** ✅ SUCCESS (creator ownership survives department transfer!)

**Meanwhile Dept-A admin can also manage:**
```graphql
# Admin in Dept-A updates same purchase
mutation DeptA_Admin_Updates {
  purchaseUpdate(purchase: {
    id: "TRANSFER_PURCHASE_ID"
    name: "Dept-A admin update"
    lastchange: "..."
  }) {
    ... on PurchaseGQLModel { name }
  }
}
```
**Result:** ✅ SUCCESS (group permissions still apply)

---

## 🔍 Root Admin Testing

### Test 16: Root Admin Sees Everything

```graphql
# Login as user with "administrátor" role in root group (mastergroupId = NULL)
query RootAdmin_SeeAll {
  purchasePage(skip: 0, limit: 100) {
    id
    name
    rbacobjectId  # Will show purchases from ALL departments
    createdbyId   # Different users across organization
  }
}
```

**Expected Result:**
- ✅ Returns ALL purchases from ALL departments
- No filtering applied
- Can see everyone's content

---

### Test 17: Root Admin Modifies Any Content

```graphql
# Login as root admin (e.g., rektor)
mutation RootAdmin_UpdateAnything {
  purchaseUpdate(purchase: {
    id: "ANY_PURCHASE_FROM_ANY_DEPT"
    name: "Rector modified this"
    lastchange: "..."
  }) {
    ... on PurchaseGQLModel {
      id
      name
    }
  }
}
```

**Expected Result:**
- ✅ SUCCESS regardless of which department
- ✅ SUCCESS regardless of who created it
- Universal access

---

## 📊 Verification Queries

### Check Authorization State

```graphql
query VerifyAuthState {
  me {
    id
    fullname
    roles {
      roletype { name }
      group {
        id
        name
        mastergroupId
      }
    }
  }
  
  # Get a purchase you created
  purchaseById(id: "YOUR_PURCHASE_ID") {
    id
    name
    createdbyId      # Should match me.id
    rbacobjectId     # Should be in one of your groups
  }
}
```

**Verify:**
- [ ] Your user.id matches purchase.createdbyId
- [ ] Purchase rbacobjectId is in your accessible groups
- [ ] If mastergroupId is NULL + role is "administrátor" = you're root admin

---

## 🧪 Complete Test Suite

Run these tests in order to verify all functionality:

```graphql
# === SETUP ===
query Test0_GetUserInfo {
  me { id fullname roles { roletype { name } group { id name } } }
}

# === CREATE TESTS ===
mutation Test1_CreateBasic {
  purchaseInsert(purchase: { name: "Test 1", status: "pending" }) {
    ... on PurchaseGQLModel { id createdbyId rbacobjectId }
    ... on PurchaseGQLModelInsertError { msg }
  }
}

mutation Test2_CreateWithItems {
  purchaseInsert(purchase: {
    name: "Test 2"
    items: [{ name: "Item 1", quantity: 1, price: 10 }]
  }) {
    ... on PurchaseGQLModel { id items { id name } }
  }
}

# === READ TESTS ===
query Test3_QueryOwn {
  purchaseById(id: "TEST1_ID") { id name createdbyId }
}

query Test4_QueryPage {
  purchasePage(limit: 5) { id name createdbyId rbacobjectId }
}

# === UPDATE TESTS ===
mutation Test5_UpdateOwn {
  purchaseUpdate(purchase: {
    id: "TEST1_ID"
    name: "Updated"
    lastchange: "CURRENT_TIMESTAMP"
  }) {
    ... on PurchaseGQLModel { id name }
    ... on PurchaseGQLModelUpdateError { msg }
  }
}

# === DELETE TESTS ===
mutation Test6_DeleteOwn {
  purchaseDelete(purchase: {
    id: "TEST1_ID"
    lastchange: "CURRENT_TIMESTAMP"
  }) {
    # Returns null on success, or error object on failure
    ... on PurchaseGQLModelDeleteError { msg }
  }
}
```

---

## 📋 Expected Results Summary

| Test | As Viewer | As Editor | As Admin | As Root Admin |
|------|-----------|-----------|----------|---------------|
| **Create** | ❌ | ✅ | ✅ | ✅ |
| **Read Own** | ✅ | ✅ | ✅ | ✅ |
| **Read Group** | ✅ | ✅ | ✅ | ✅ |
| **Read Other** | ❌ | ❌ | ❌ | ✅ |
| **Update Own** | ✅ (creator!) | ✅ | ✅ | ✅ |
| **Update Group** | ❌ | ✅ | ✅ | ✅ |
| **Update Other** | ❌ | ❌ | ❌ | ✅ |
| **Delete Own** | ❌ | ❌ | ✅ | ✅ |
| **Delete Group** | ❌ | ❌ | ✅ | ✅ |
| **Delete Other** | ❌ | ❌ | ❌ | ✅ |

**Key Insight:** Creator ownership gives permanent CRUD access (except delete requires admin role)

---

## 🎯 Quick Test Checklist

- [ ] Create purchase as editor → becomes owner
- [ ] Creator demoted to viewer → can still update own purchase
- [ ] Creator cannot create NEW purchase as viewer
- [ ] Admin can update other user's purchase in same group
- [ ] Admin CANNOT update purchase from different group
- [ ] Root admin can update ANY purchase
- [ ] Only admin roles can delete (not editor)
- [ ] Page query returns only accessible purchases
- [ ] Optimistic locking prevents stale updates
- [ ] rbacobject_id auto-assigned on insert

---

## 📚 Related Documentation

- [CREATOR_OWNERSHIP_GUIDE.md](CREATOR_OWNERSHIP_GUIDE.md) - Visual guide
- [ROLES_DOCUMENTATION.md](ROLES_DOCUMENTATION.md) - Role reference
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - One-page guide
- [authz_extensions.py](src/GraphTypeDefinitions/authz_extensions.py) - Implementation

---

**Happy Testing! 🚀**
