-- Phase one keeps three tables: who is talking, what was said, what was done.
-- No transcripts of audio, no raw recordings, no credentials.

CREATE TABLE IF NOT EXISTS sessions (
    session_id      UUID PRIMARY KEY,
    home_id         TEXT        NOT NULL,
    user_id         TEXT,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at        TIMESTAMPTZ,
    language        TEXT        NOT NULL DEFAULT 'ar'
);

CREATE TABLE IF NOT EXISTS conversation_turns (
    turn_id         UUID PRIMARY KEY,
    session_id      UUID        NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role            TEXT        NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT        NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tool_executions (
    execution_id    UUID PRIMARY KEY,
    session_id      UUID        NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    tool_name       TEXT        NOT NULL,
    risk_level      TEXT        NOT NULL,
    arguments       JSONB       NOT NULL,
    result          JSONB,
    error_code      TEXT,
    approval_id     UUID,
    idempotency_key TEXT,
    started_at      TIMESTAMPTZ NOT NULL,
    finished_at     TIMESTAMPTZ
);

-- The two questions somebody will actually ask this table: what did it do in
-- this session, and what did it refuse across the house.
CREATE INDEX IF NOT EXISTS tool_executions_by_session ON tool_executions (session_id, started_at DESC);
CREATE INDEX IF NOT EXISTS tool_executions_refused ON tool_executions (error_code, started_at DESC)
    WHERE error_code IS NOT NULL;

-- An execution that never finished is a bug worth finding, so the row stays.
