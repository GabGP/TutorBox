-- 009_add_quiz_generation_logs.sql
-- Dedicated telemetry trail for SLM quiz generation attempts, latency, and rejection feedback.

CREATE TABLE IF NOT EXISTS quiz_generation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NULL REFERENCES quiz_questions(id) ON DELETE SET NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    topic TEXT NOT NULL,
    subconcept TEXT NULL,
    model_name TEXT NOT NULL,
    attempts INTEGER NOT NULL CHECK(attempts >= 1),
    duration_ms REAL NOT NULL CHECK(duration_ms >= 0.0),
    success INTEGER NOT NULL CHECK(success IN (0, 1)),
    rejection_history_json TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quiz_gen_logs_user ON quiz_generation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_quiz_gen_logs_topic ON quiz_generation_logs(topic, subconcept);
CREATE INDEX IF NOT EXISTS idx_quiz_gen_logs_created ON quiz_generation_logs(created_at);
