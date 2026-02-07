-- Insert Purchase Types - Hierarchical Tree Structure
-- =====================================================
--
-- This script populates the purchasetypes table with a sample hierarchy.
-- Structure:
-- ROOT
-- ├── EQUIPMENT
-- │   ├── IT_EQUIPMENT
-- │   ├── LABORATORY_EQUIPMENT
-- │   └── OFFICE_EQUIPMENT
-- ├── SUPPLIES
-- │   ├── OFFICE_SUPPLIES
-- │   └── LABORATORY_SUPPLIES
-- ├── SERVICES
-- │   ├── MAINTENANCE
-- │   └── CONSULTING
-- └── SOFTWARE
--     ├── LICENSES
--     └── SUBSCRIPTIONS

-- Root
INSERT INTO purchasetypes (id, name, name_en, code, description, parent_id, path, level, is_active, sort_order)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'ROOT', 'ROOT', 'ROOT', 'Root purchase type', NULL, '/', 0, true, 0);

-- Level 1 - Main Categories
INSERT INTO purchasetypes (id, name, name_en, code, description, parent_id, path, level, is_active, sort_order)
VALUES
  ('10000000-0000-0000-0000-000000000001', 'Vybavení', 'Equipment', 'EQUIP', 'Physical equipment and hardware', '00000000-0000-0000-0000-000000000001', '/ROOT/EQUIP/', 1, true, 1),
  ('10000000-0000-0000-0000-000000000002', 'Spotřební materiál', 'Supplies', 'SUPPLY', 'Consumable supplies and materials', '00000000-0000-0000-0000-000000000001', '/ROOT/SUPPLY/', 1, true, 2),
  ('10000000-0000-0000-0000-000000000003', 'Služby', 'Services', 'SERVICE', 'Professional services', '00000000-0000-0000-0000-000000000001', '/ROOT/SERVICE/', 1, true, 3),
  ('10000000-0000-0000-0000-000000000004', 'Software', 'Software', 'SOFTWARE', 'Software licenses and subscriptions', '00000000-0000-0000-0000-000000000001', '/ROOT/SOFTWARE/', 1, true, 4);

-- Level 2 - Equipment Subcategories
INSERT INTO purchasetypes (id, name, name_en, code, description, parent_id, path, level, is_active, sort_order)
VALUES
  ('20000000-0000-0000-0000-000000000001', 'IT vybavení', 'IT Equipment', 'IT_EQUIP', 'Computers, servers, network devices', '10000000-0000-0000-0000-000000000001', '/ROOT/EQUIP/IT_EQUIP/', 2, true, 1),
  ('20000000-0000-0000-0000-000000000002', 'Laboratorní vybavení', 'Laboratory Equipment', 'LAB_EQUIP', 'Scientific and research equipment', '10000000-0000-0000-0000-000000000001', '/ROOT/EQUIP/LAB_EQUIP/', 2, true, 2),
  ('20000000-0000-0000-0000-000000000003', 'Kancelářské vybavení', 'Office Equipment', 'OFFICE_EQUIP', 'Furniture, printers, office machines', '10000000-0000-0000-0000-000000000001', '/ROOT/EQUIP/OFFICE_EQUIP/', 2, true, 3);

-- Level 2 - Supplies Subcategories
INSERT INTO purchasetypes (id, name, name_en, code, description, parent_id, path, level, is_active, sort_order)
VALUES
  ('20000000-0000-0000-0000-000000000004', 'Kancelářské potřeby', 'Office Supplies', 'OFFICE_SUPPLY', 'Paper, stationery, consumables', '10000000-0000-0000-0000-000000000002', '/ROOT/SUPPLY/OFFICE_SUPPLY/', 2, true, 1),
  ('20000000-0000-0000-0000-000000000005', 'Laboratorní spotřební materiál', 'Laboratory Supplies', 'LAB_SUPPLY', 'Chemicals, consumables, samples', '10000000-0000-0000-0000-000000000002', '/ROOT/SUPPLY/LAB_SUPPLY/', 2, true, 2);

-- Level 2 - Services Subcategories
INSERT INTO purchasetypes (id, name, name_en, code, description, parent_id, path, level, is_active, sort_order)
VALUES
  ('20000000-0000-0000-0000-000000000006', 'Údržba', 'Maintenance', 'MAINTENANCE', 'IT and facility maintenance services', '10000000-0000-0000-0000-000000000003', '/ROOT/SERVICE/MAINTENANCE/', 2, true, 1),
  ('20000000-0000-0000-0000-000000000007', 'Poradenství', 'Consulting', 'CONSULTING', 'Professional consulting services', '10000000-0000-0000-0000-000000000003', '/ROOT/SERVICE/CONSULTING/', 2, true, 2),
  ('20000000-0000-0000-0000-000000000008', 'Školení', 'Training', 'TRAINING', 'Professional training and workshops', '10000000-0000-0000-0000-000000000003', '/ROOT/SERVICE/TRAINING/', 2, true, 3);

-- Level 2 - Software Subcategories
INSERT INTO purchasetypes (id, name, name_en, code, description, parent_id, path, level, is_active, sort_order)
VALUES
  ('20000000-0000-0000-0000-000000000009', 'Licence', 'Licenses', 'LICENSE', 'Software licenses', '10000000-0000-0000-0000-000000000004', '/ROOT/SOFTWARE/LICENSE/', 2, true, 1),
  ('20000000-0000-0000-0000-000000000010', 'Předplatné', 'Subscriptions', 'SUBSCRIPTION', 'Cloud services and subscriptions', '10000000-0000-0000-0000-000000000004', '/ROOT/SOFTWARE/SUBSCRIPTION/', 2, true, 2);

-- Level 3 - Detailed IT Equipment Types
INSERT INTO purchasetypes (id, name, name_en, code, description, parent_id, path, level, is_active, sort_order)
VALUES
  ('30000000-0000-0000-0000-000000000001', 'Počítače', 'Computers', 'COMPUTER', 'Desktop and laptop computers', '20000000-0000-0000-0000-000000000001', '/ROOT/EQUIP/IT_EQUIP/COMPUTER/', 3, true, 1),
  ('30000000-0000-0000-0000-000000000002', 'Servery', 'Servers', 'SERVER', 'Physical and virtual servers', '20000000-0000-0000-0000-000000000001', '/ROOT/EQUIP/IT_EQUIP/SERVER/', 3, true, 2),
  ('30000000-0000-0000-0000-000000000003', 'Síťová zařízení', 'Network Devices', 'NETWORK', 'Switches, routers, firewalls', '20000000-0000-0000-0000-000000000001', '/ROOT/EQUIP/IT_EQUIP/NETWORK/', 3, true, 3);

-- Level 3 - Detailed Software Types
INSERT INTO purchasetypes (id, name, name_en, code, description, parent_id, path, level, is_active, sort_order)
VALUES
  ('30000000-0000-0000-0000-000000000004', 'Kancelářský software', 'Office Software', 'OFFICE_SW', 'MS Office, LibreOffice, etc.', '20000000-0000-0000-0000-000000000009', '/ROOT/SOFTWARE/LICENSE/OFFICE_SW/', 3, true, 1),
  ('30000000-0000-0000-0000-000000000005', 'Vývojářské nástroje', 'Development Tools', 'DEV_TOOLS', 'IDEs, compilers, dev tools', '20000000-0000-0000-0000-000000000009', '/ROOT/SOFTWARE/LICENSE/DEV_TOOLS/', 3, true, 2),
  ('30000000-0000-0000-0000-000000000006', 'Cloudové služby', 'Cloud Services', 'CLOUD', 'AWS, Azure, Google Cloud', '20000000-0000-0000-0000-000000000010', '/ROOT/SOFTWARE/SUBSCRIPTION/CLOUD/', 3, true, 1),
  ('30000000-0000-0000-0000-000000000007', 'Databázové služby', 'Database Services', 'DB_SERVICE', 'Database subscriptions', '20000000-0000-0000-0000-000000000010', '/ROOT/SOFTWARE/SUBSCRIPTION/DB_SERVICE/', 3, true, 2);

-- Verify the tree structure
-- SELECT id, name, code, path, level, parent_id FROM purchasetypes ORDER BY path;

