# Fix Foreign Key Constraint for Cascade Delete

## Problem

When deleting a purchase with child items, you get this error:
```
foreign key constraint "purchase_items_evolution_purchase_id_fkey" violated
Key (id)=(xxx) is still referenced from table "purchase_items_evolution"
```

## Root Cause

The database foreign key constraint was created WITHOUT `ON DELETE CASCADE`, so the database prevents deleting parent records when children exist.

The SQLAlchemy model has `cascade="all, delete-orphan"` configured, but this only works if the database constraint also allows it.

## Solution Options

### Option 1: Manual Deletion (Current Workaround)

Delete child items first, then delete the parent purchase. See updated [TEST_QUERIES_COMPLETE.md](TEST_QUERIES_COMPLETE.md) for the workflow.

### Option 2: Fix Database Constraint (Recommended)

Add `ON DELETE CASCADE` to the foreign key constraint so deleting a purchase automatically deletes its items.

#### Step 1: Create Migration SQL

Create a file `fix_cascade_delete.sql`:

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

Run the SQL against your database:

```powershell
# Using psql (PostgreSQL command line)
psql -U your_username -d your_database -f fix_cascade_delete.sql

# Or using Docker if your DB is in a container
docker exec -i your_postgres_container psql -U username -d database < fix_cascade_delete.sql
```

#### Step 3: Update SQLAlchemy Model (Optional Clarity)

In [purchasemodel.py](src/DBDefinitions/purchasemodel.py#L126), you can make the cascade explicit:

```python
purchase_id: Mapped[IDType] = mapped_column(
    ForeignKey("purchases_evolution.id", ondelete="CASCADE"),
    index=True, 
    nullable=True, 
    default=None
)
```

This documents the behavior in code, though the real enforcement is in the database.

#### Step 4: Verify

After applying the migration:

```graphql
# This should now work without manually deleting items first
mutation DeletePurchaseWithItems {
  purchaseDelete(purchase: {
    id: "PURCHASE_WITH_ITEMS_ID"
    lastchange: "CURRENT_LASTCHANGE"
  }) {
    ... on PurchaseGQLModelDeleteError {
      msg
    }
  }
}
```

**Expected:** Returns `null` (success), and all child items are automatically deleted.

## Recommendation

Use **Option 2** if you control the database schema. This matches the intended behavior from `cascade="all, delete-orphan"` in the SQLAlchemy model and provides better UX (no multi-step deletion required).

---

**Current Status:** Documentation updated to show manual deletion workflow (Option 1). Apply Option 2 when you can modify the database.
