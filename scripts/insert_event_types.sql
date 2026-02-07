-- Insert Event Types - Hierarchical Tree Structure
-- ==================================================
--
-- This script populates the eventtypes table with a sample hierarchy.
-- Structure:
-- ROOT
-- ├── ACADEMIC
-- │   ├── CONFERENCE
-- │   ├── SEMINAR
-- │   ├── WORKSHOP
-- │   └── LECTURE
-- ├── ADMINISTRATIVE
-- │   ├── MEETING
-- │   ├── REVIEW
-- │   └── PLANNING
-- ├── SOCIAL
-- │   ├── NETWORKING_EVENT
-- │   ├── CELEBRATION
-- │   └── TEAM_BUILDING
-- └── TRAINING
--     ├── PROFESSIONAL_DEVELOPMENT
--     ├── TECHNICAL_TRAINING
--     └── COMPLIANCE_TRAINING

-- Root
INSERT INTO eventtypes (id, name, name_en, code, description, parent_id, path, level, is_active, sort_order, default_duration_minutes)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'ROOT', 'ROOT', 'ROOT', 'Root event type', NULL, '/', 0, true, 0, NULL);

-- Level 1 - Main Categories
INSERT INTO eventtypes (id, name, name_en, code, description, parent_id, path, level, is_active, sort_order, default_duration_minutes)
VALUES
  ('10000000-0000-0000-0000-000000000001', 'Akademické', 'Academic', 'ACADEMIC', 'Academic and educational events', '00000000-0000-0000-0000-000000000001', '/ROOT/ACADEMIC/', 1, true, 1, 120),
  ('10000000-0000-0000-0000-000000000002', 'Administrativní', 'Administrative', 'ADMIN', 'Administrative and management events', '00000000-0000-0000-0000-000000000001', '/ROOT/ADMIN/', 1, true, 2, 60),
  ('10000000-0000-0000-0000-000000000003', 'Společenské', 'Social', 'SOCIAL', 'Social and networking events', '00000000-0000-0000-0000-000000000001', '/ROOT/SOCIAL/', 1, true, 3, 120),
  ('10000000-0000-0000-0000-000000000004', 'Školení', 'Training', 'TRAINING', 'Training and professional development', '00000000-0000-0000-0000-000000000001', '/ROOT/TRAINING/', 1, true, 4, 180);

-- Level 2 - Academic Subcategories
INSERT INTO eventtypes (id, name, name_en, code, description, parent_id, path, level, is_active, sort_order, default_duration_minutes)
VALUES
  ('20000000-0000-0000-0000-000000000001', 'Konference', 'Conference', 'CONF', 'Academic and professional conferences', '10000000-0000-0000-0000-000000000001', '/ROOT/ACADEMIC/CONF/', 2, true, 1, 480),
  ('20000000-0000-0000-0000-000000000002', 'Seminář', 'Seminar', 'SEMINAR', 'Research and educational seminars', '10000000-0000-0000-0000-000000000001', '/ROOT/ACADEMIC/SEMINAR/', 2, true, 2, 120),
  ('20000000-0000-0000-0000-000000000003', 'Workshop', 'Workshop', 'WORKSHOP', 'Hands-on workshops', '10000000-0000-0000-0000-000000000001', '/ROOT/ACADEMIC/WORKSHOP/', 2, true, 3, 240),
  ('20000000-0000-0000-0000-000000000004', 'Přednáška', 'Lecture', 'LECTURE', 'Public and guest lectures', '10000000-0000-0000-0000-000000000001', '/ROOT/ACADEMIC/LECTURE/', 2, true, 4, 90);

-- Level 2 - Administrative Subcategories
INSERT INTO eventtypes (id, name, name_en, code, description, parent_id, path, level, is_active, sort_order, default_duration_minutes)
VALUES
  ('20000000-0000-0000-0000-000000000005', 'Schůzka', 'Meeting', 'MEETING', 'Meetings and discussions', '10000000-0000-0000-0000-000000000002', '/ROOT/ADMIN/MEETING/', 2, true, 1, 60),
  ('20000000-0000-0000-0000-000000000006', 'Hodnocení', 'Review', 'REVIEW', 'Performance and project reviews', '10000000-0000-0000-0000-000000000002', '/ROOT/ADMIN/REVIEW/', 2, true, 2, 90),
  ('20000000-0000-0000-0000-000000000007', 'Plánování', 'Planning', 'PLANNING', 'Strategic and operational planning', '10000000-0000-0000-0000-000000000002', '/ROOT/ADMIN/PLANNING/', 2, true, 3, 120);

-- Level 2 - Social Subcategories
INSERT INTO eventtypes (id, name, name_en, code, description, parent_id, path, level, is_active, sort_order, default_duration_minutes)
VALUES
  ('20000000-0000-0000-0000-000000000008', 'Networkingová akce', 'Networking Event', 'NETWORKING', 'Professional networking events', '10000000-0000-0000-0000-000000000003', '/ROOT/SOCIAL/NETWORKING/', 2, true, 1, 120),
  ('20000000-0000-0000-0000-000000000009', 'Oslava', 'Celebration', 'CELEBRATION', 'Celebrations and ceremonies', '10000000-0000-0000-0000-000000000003', '/ROOT/SOCIAL/CELEBRATION/', 2, true, 2, 180),
  ('20000000-0000-0000-0000-000000000010', 'Teambuilding', 'Team Building', 'TEAMBUILDING', 'Team building activities', '10000000-0000-0000-0000-000000000003', '/ROOT/SOCIAL/TEAMBUILDING/', 2, true, 3, 240);

-- Level 2 - Training Subcategories
INSERT INTO eventtypes (id, name, name_en, code, description, parent_id, path, level, is_active, sort_order, default_duration_minutes)
VALUES
  ('20000000-0000-0000-0000-000000000011', 'Profesní rozvoj', 'Professional Development', 'PROF_DEV', 'Skills and leadership training', '10000000-0000-0000-0000-000000000004', '/ROOT/TRAINING/PROF_DEV/', 2, true, 1, 240),
  ('20000000-0000-0000-0000-000000000012', 'Technické školení', 'Technical Training', 'TECH_TRAIN', 'Software and equipment training', '10000000-0000-0000-0000-000000000004', '/ROOT/TRAINING/TECH_TRAIN/', 2, true, 2, 180),
  ('20000000-0000-0000-0000-000000000013', 'Compliance školení', 'Compliance Training', 'COMPLIANCE', 'Safety and ethics training', '10000000-0000-0000-0000-000000000004', '/ROOT/TRAINING/COMPLIANCE/', 2, true, 3, 120);

-- Level 3 - Detailed Conference Types
INSERT INTO eventtypes (id, name, name_en, code, description, parent_id, path, level, is_active, sort_order, default_duration_minutes)
VALUES
  ('30000000-0000-0000-0000-000000000001', 'Mezinárodní konference', 'International Conference', 'INTL_CONF', 'International conferences', '20000000-0000-0000-0000-000000000001', '/ROOT/ACADEMIC/CONF/INTL_CONF/', 3, true, 1, 1440),
  ('30000000-0000-0000-0000-000000000002', 'Národní konference', 'National Conference', 'NAT_CONF', 'National conferences', '20000000-0000-0000-0000-000000000001', '/ROOT/ACADEMIC/CONF/NAT_CONF/', 3, true, 2, 960),
  ('30000000-0000-0000-0000-000000000003', 'Regionální konference', 'Regional Conference', 'REG_CONF', 'Regional conferences', '20000000-0000-0000-0000-000000000001', '/ROOT/ACADEMIC/CONF/REG_CONF/', 3, true, 3, 480);

-- Level 3 - Detailed Meeting Types
INSERT INTO eventtypes (id, name, name_en, code, description, parent_id, path, level, is_active, sort_order, default_duration_minutes)
VALUES
  ('30000000-0000-0000-0000-000000000004', 'Schůzka rady', 'Board Meeting', 'BOARD_MTG', 'Board and committee meetings', '20000000-0000-0000-0000-000000000005', '/ROOT/ADMIN/MEETING/BOARD_MTG/', 3, true, 1, 120),
  ('30000000-0000-0000-0000-000000000005', 'Katedrová schůzka', 'Department Meeting', 'DEPT_MTG', 'Department meetings', '20000000-0000-0000-0000-000000000005', '/ROOT/ADMIN/MEETING/DEPT_MTG/', 3, true, 2, 90),
  ('30000000-0000-0000-0000-000000000006', 'Týmová schůzka', 'Team Meeting', 'TEAM_MTG', 'Team meetings', '20000000-0000-0000-0000-000000000005', '/ROOT/ADMIN/MEETING/TEAM_MTG/', 3, true, 3, 60),
  ('30000000-0000-0000-0000-000000000007', 'Projektová schůzka', 'Project Meeting', 'PROJ_MTG', 'Project status meetings', '20000000-0000-0000-0000-000000000005', '/ROOT/ADMIN/MEETING/PROJ_MTG/', 3, true, 4, 60);

-- Level 3 - Detailed Review Types
INSERT INTO eventtypes (id, name, name_en, code, description, parent_id, path, level, is_active, sort_order, default_duration_minutes)
VALUES
  ('30000000-0000-0000-0000-000000000008', 'Roční hodnocení', 'Annual Review', 'ANNUAL_REV', 'Annual performance reviews', '20000000-0000-0000-0000-000000000006', '/ROOT/ADMIN/REVIEW/ANNUAL_REV/', 3, true, 1, 120),
  ('30000000-0000-0000-0000-000000000009', 'Čtvrtletní hodnocení', 'Quarterly Review', 'QUARTER_REV', 'Quarterly reviews', '20000000-0000-0000-0000-000000000006', '/ROOT/ADMIN/REVIEW/QUARTER_REV/', 3, true, 2, 90),
  ('30000000-0000-0000-0000-000000000010', 'Projektové hodnocení', 'Project Review', 'PROJ_REV', 'Project milestone reviews', '20000000-0000-0000-0000-000000000006', '/ROOT/ADMIN/REVIEW/PROJ_REV/', 3, true, 3, 90);

-- Verify the tree structure
-- SELECT id, name, code, path, level, parent_id, default_duration_minutes FROM eventtypes ORDER BY path;

