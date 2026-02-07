# Creator Ownership - Quick Reference Card

## 🎯 One-Sentence Summary
**"If you created it, you can always manage it"** - regardless of role changes.

---

## ✅ What This Means for You

### As a User
- ✅ Content you create is **yours forever**
- ✅ Promoted? You still own your old work
- ✅ Demoted? You still own your old work
- ✅ Transferred departments? You still own your old work
- ✅ No more "locked content" issues

### As an Admin
- ✅ Manage **all content** in your group
- ✅ Users can **also** manage their own content
- ✅ Multiple admins = no single point of failure
- ✅ Hierarchical: Manage child groups too

---

## 🔐 Authorization Rules (Pick ONE)

| Check | Condition | Result |
|-------|-----------|--------|
| 1️⃣ **Creator?** | `user.id == entity.createdby_id` | ✅ ALLOW (permanent) |
| 2️⃣ **Root Admin?** | Admin in root group (no parent) | ✅ ALLOW (all entities) |
| 3️⃣ **Group Member?** | Has required role in entity's group | ✅ ALLOW (role-based) |
| 4️⃣ **None above** | - | ❌ DENY |

---

## 🎬 Quick Examples

### Example 1: Oliver's Purchase
```yaml
Created: Oliver (editor, Dept-A) creates Purchase #123
  ↓
Later: Oliver demoted to "viewer" (read-only role)
  ↓
Result: Oliver can STILL edit Purchase #123 ✅ (creator ownership)
        Oliver CANNOT create NEW purchases ❌ (viewer role)
```

### Example 2: Admin Access
```yaml
Purchase #456: Created by Oliver, rbacobject_id = "Dept-A"

Access:
  - Oliver ✅ (creator)
  - Estera (admin, Dept-A) ✅ (group admin)
  - Ornela (admin, Faculty-A) ✅ (parent group)
  - Valentin (admin, Dept-B) ❌ (different dept)
```

### Example 3: Root Admin
```yaml
Ludvík (rektor, University root admin):
  → ✅ Sees ALL purchases in ALL departments
  → ✅ Can modify ANY entity
  → ✅ No filtering applied
```

---

## 📋 Permission Levels

| Role Category | Count | Can Read? | Can Write? | Can Delete? |
|--------------|-------|-----------|------------|-------------|
| **Viewers** | 5 | ✅ | ❌ | ❌ |
| **Editors/Leaders/Guarantors** | 15 | ✅ | ✅ | ❌ |
| **System Admins** | 5 | ✅ | ✅ | ✅ |

---

## 💻 Code Patterns

### Creating Content
```graphql
mutation {
  purchaseInsert(purchase: {
    name: "My Purchase"
    # rbacobject_id auto-assigned to your primary write group
  }) {
    ... on PurchaseGQLModel {
      id
      createdbyId  # ← Set to your user.id automatically
    }
  }
}
```

### Querying Content
```graphql
query {
  purchasePage(limit: 10) {
    id
    name
    # Returns: YOUR purchases + GROUP purchases + ROOT ADMIN sees all
  }
}
```

---

## 🔍 Troubleshooting

| Problem | Check This | Solution |
|---------|------------|----------|
| "Permission denied but I created it" | `purchaseById(id).createdbyId` vs `me.id` | Should match - check UUID format |
| "I'm admin but can't access" | `purchaseById(id).rbacobjectId` vs your groups | Must be admin in that group |
| "I see nothing" | `me { roles { group { id } } }` | Need at least one role |

---

## 📚 Documentation Links

- **Visual Guide:** [CREATOR_OWNERSHIP_GUIDE.md](CREATOR_OWNERSHIP_GUIDE.md)
- **Role Reference:** [ROLES_DOCUMENTATION.md](ROLES_DOCUMENTATION.md)
- **Implementation:** [authz_extensions.py](src/GraphTypeDefinitions/authz_extensions.py)
- **Test Queries:** [TEST_QUERIES.md](TEST_QUERIES.md)

---

## 🎓 Key Takeaway

**Traditional RBAC:**
```
User creates content → Gets permissions based on role
User's role changes → LOSES ACCESS ❌
```

**Creator Ownership RBAC:**
```
User creates content → BECOMES OWNER (permanent) ✅
User's role changes → STILL OWNS IT ✅
Group admin → CAN ALSO MANAGE IT ✅
```

**Result:** Happy users + No support tickets + Flexible permissions 🎉
