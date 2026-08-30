-- SYLTRA HEALTH — D1 schema (additive to health-api/schema.sql, which already
-- holds `registrations` and `services` for the marketing site).
--
-- This is the storage side of the contract in
-- mobile/src/services/api/contract.ts. Nothing here is applied yet.
-- Apply with:  npx wrangler d1 execute syltra-health --file=./schema.sql --remote

-- ---------------------------------------------------------------- identity

CREATE TABLE IF NOT EXISTS profiles (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  time_zone   TEXT NOT NULL DEFAULT 'Asia/Riyadh',
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ----------------------------------------------------------------- devices
-- App sessions are bound to a device rather than a password: there is no login
-- screen, and health data should not sit behind a shared credential.

CREATE TABLE IF NOT EXISTS devices (
  id          TEXT PRIMARY KEY,      -- client-generated, opaque
  profile_id  TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen   TEXT
);
CREATE INDEX IF NOT EXISTS idx_devices_profile ON devices (profile_id);

-- Fixed-window limiter for device registration.
CREATE TABLE IF NOT EXISTS rate_limits (
  key          TEXT NOT NULL,
  window_start INTEGER NOT NULL,
  count        INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (key, window_start)
);

-- ----------------------------------------------------------------- consent
-- One row per source per profile. Consent is per source and per purpose, and
-- revoking is recorded rather than deleted, so the audit stays truthful.

CREATE TABLE IF NOT EXISTS consent_sources (
  profile_id  TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  source      TEXT NOT NULL,          -- apple_health | health_connect | glucose_meter | bp_monitor | home_sensors | location
  purpose     TEXT NOT NULL,
  enabled     INTEGER NOT NULL DEFAULT 0,
  granted_at  TEXT,
  revoked_at  TEXT,
  PRIMARY KEY (profile_id, source)
);

-- ---------------------------------------------------------------- readings
-- The unified reading model: who, what, value, unit, source, when, quality.
-- A value the source does not have is simply absent — never defaulted.

CREATE TABLE IF NOT EXISTS readings (
  id          TEXT PRIMARY KEY,
  profile_id  TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  kind        TEXT NOT NULL,          -- heart_rate | sleep | steps | glucose | spo2 | weight | bp
  value       REAL NOT NULL,
  unit        TEXT,
  source      TEXT NOT NULL,
  taken_at    TEXT NOT NULL,
  quality     TEXT,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_readings_profile_time ON readings (profile_id, kind, taken_at);

-- ---------------------------------------------------------------- baseline

CREATE TABLE IF NOT EXISTS baselines (
  profile_id                 TEXT PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
  days_collected             INTEGER NOT NULL DEFAULT 0,
  days_required              INTEGER NOT NULL DEFAULT 14,
  glucose_low                REAL NOT NULL DEFAULT 70,
  glucose_high               REAL NOT NULL DEFAULT 140,
  heart_rate_low             REAL NOT NULL DEFAULT 55,
  heart_rate_high            REAL NOT NULL DEFAULT 100,
  nightly_motion_gap_minutes INTEGER NOT NULL DEFAULT 20,
  updated_at                 TEXT NOT NULL DEFAULT (datetime('now'))
);

-- -------------------------------------------------------------- home state

CREATE TABLE IF NOT EXISTS rooms (
  id          TEXT NOT NULL,
  profile_id  TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  PRIMARY KEY (profile_id, id)
);

CREATE TABLE IF NOT EXISTS room_states (
  profile_id   TEXT NOT NULL,
  room_id      TEXT NOT NULL,
  temperature  REAL,
  humidity     REAL,
  co2          REAL,
  last_motion  TEXT,
  updated_at   TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (profile_id, room_id)
);

-- ------------------------------------------------------------ trusted circle

CREATE TABLE IF NOT EXISTS trusted_people (
  id            TEXT PRIMARY KEY,
  profile_id    TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  name          TEXT NOT NULL,
  relation      TEXT NOT NULL,
  feminine      INTEGER NOT NULL DEFAULT 0,
  priority      INTEGER NOT NULL,
  has_key       INTEGER NOT NULL DEFAULT 0,
  available     INTEGER NOT NULL DEFAULT 1,
  eta_minutes   INTEGER,             -- expected arrival; null = unknown
  available_from TEXT,               -- 'HH:MM', null = always
  available_to   TEXT,
  accepted_at   TEXT,                -- the person's own consent to join the circle
  removed_at    TEXT
);
CREATE INDEX IF NOT EXISTS idx_people_profile ON trusted_people (profile_id, priority);

-- What each person may see. Default is nothing; every field is opt-in.
CREATE TABLE IF NOT EXISTS share_rules (
  person_id  TEXT NOT NULL REFERENCES trusted_people(id) ON DELETE CASCADE,
  field      TEXT NOT NULL,          -- reason | location | readings
  scope      TEXT NOT NULL,          -- event_only | never
  PRIMARY KEY (person_id, field)
);

-- ----------------------------------------------------------- response plan

CREATE TABLE IF NOT EXISTS response_plans (
  profile_id            TEXT PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
  verify_window_seconds INTEGER NOT NULL DEFAULT 120,
  updated_at            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS response_levels (
  profile_id  TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  level_id    TEXT NOT NULL,         -- daily | verify | trusted | authorized
  enabled     INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (profile_id, level_id)
);

-- ------------------------------------------------------------------ events
-- The audit trail. `event_audit` is append-only: corrections are new rows.

CREATE TABLE IF NOT EXISTS events (
  id          TEXT PRIMARY KEY,
  profile_id  TEXT NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  started_at  INTEGER NOT NULL,
  ended_at    INTEGER,
  outcome     TEXT,                  -- user_ok | user_asked_for_help | responder_accepted | responder_arrived | no_one_available
  simulated   INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_events_profile ON events (profile_id, started_at DESC);

CREATE TABLE IF NOT EXISTS event_signals (
  event_id  TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  signal_id TEXT NOT NULL,
  at        INTEGER NOT NULL,
  kind      TEXT NOT NULL,
  title     TEXT NOT NULL,
  detail    TEXT,
  weight    REAL NOT NULL,
  PRIMARY KEY (event_id, signal_id)
);

CREATE TABLE IF NOT EXISTS event_audit (
  id          TEXT PRIMARY KEY,
  event_id    TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  at          INTEGER NOT NULL,
  phase       TEXT NOT NULL,         -- signal | verify | escalate | close
  phase_label TEXT NOT NULL,
  title       TEXT NOT NULL,
  detail      TEXT
);
CREATE INDEX IF NOT EXISTS idx_audit_event ON event_audit (event_id, at);

-- Exactly what was shared, with whom, and until when.
CREATE TABLE IF NOT EXISTS event_shares (
  event_id   TEXT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
  person_id  TEXT NOT NULL,
  fields     TEXT NOT NULL,          -- JSON array
  shared_at  INTEGER NOT NULL,
  expires_at INTEGER,
  PRIMARY KEY (event_id, person_id)
);
