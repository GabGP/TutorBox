-- 003_add_lookup_indexes.sql
-- Adds lookup indexes for foreign-key columns (SQLite does not auto-index them).

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_turn_logs_session_id ON turn_logs (session_id);
