-- Migration: Add CASCADE DELETE to purchase_items foreign key
-- Date: 2026-01-07
-- Purpose: Allow automatic deletion of child items when parent purchase is deleted

-- Drop the existing constraint
ALTER TABLE purchase_items_evolution 
DROP CONSTRAINT IF EXISTS purchase_items_evolution_purchase_id_fkey;

-- Recreate with ON DELETE CASCADE
ALTER TABLE purchase_items_evolution
ADD CONSTRAINT purchase_items_evolution_purchase_id_fkey
FOREIGN KEY (purchase_id) 
REFERENCES purchases_evolution(id) 
ON DELETE CASCADE;

-- Verify the constraint was created
SELECT 
    tc.constraint_name, 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
  ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
  AND tc.table_name='purchase_items_evolution'
  AND kcu.column_name='purchase_id';
