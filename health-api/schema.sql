-- SYLTRA HEALTH API — D1 schema
CREATE TABLE IF NOT EXISTS registrations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT,
  user_type TEXT,
  interest TEXT,
  message TEXT,
  status TEXT NOT NULL DEFAULT 'new',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_reg_created ON registrations (created_at);

CREATE TABLE IF NOT EXISTS services (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name_en TEXT NOT NULL,
  name_ar TEXT NOT NULL,
  path TEXT NOT NULL UNIQUE,
  active INTEGER NOT NULL DEFAULT 1,
  sort INTEGER NOT NULL DEFAULT 0
);

INSERT OR IGNORE INTO services (name_en, name_ar, path, active, sort) VALUES
  ('Everyday Wellness', 'الصحة اليومية', '/individuals', 1, 1),
  ('Older Adults', 'كبار السن', '/older-adults', 1, 2),
  ('Blood Pressure', 'ضغط الدم', '/chronic-conditions/blood-pressure', 1, 3),
  ('Diabetes', 'السكري', '/chronic-conditions/diabetes', 1, 4),
  ('Sleep & Recovery', 'النوم والتعافي', '/sleep-recovery', 1, 5),
  ('Home Wellness', 'صحة المنزل', '/home-wellness', 1, 6),
  ('For Care Providers', 'لمقدمي الرعاية', '/care-providers', 0, 7);
