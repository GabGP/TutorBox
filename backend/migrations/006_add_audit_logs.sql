-- 006_add_audit_logs.sql
-- Append-only trail for privileged/account actions.
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_user_id INTEGER,
    action TEXT NOT NULL,
    target_user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON audit_logs (actor_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_target ON audit_logs (target_user_id);
