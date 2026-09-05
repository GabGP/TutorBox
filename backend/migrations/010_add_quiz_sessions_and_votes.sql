-- 010_add_quiz_sessions_and_votes.sql
-- Classroom quiz sessions, question rounds, and student vote persistence

CREATE TABLE IF NOT EXISTS quiz_sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    topic TEXT NOT NULL,
    teacher_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'lobby' CHECK(status IN ('lobby', 'active', 'completed', 'abandoned')),
    question_count INTEGER NOT NULL DEFAULT 0,
    current_round_index INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    ended_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS quiz_session_rounds (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
    question_id TEXT NULL REFERENCES quiz_questions(id) ON DELETE SET NULL,
    round_index INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'open', 'closed', 'revealed')),
    opened_at TIMESTAMP NULL,
    closed_at TIMESTAMP NULL,
    duration_seconds INTEGER NOT NULL DEFAULT 30
);

CREATE TABLE IF NOT EXISTS quiz_session_votes (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
    round_id TEXT NOT NULL REFERENCES quiz_session_rounds(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    transport_type TEXT NOT NULL DEFAULT 'web' CHECK(transport_type IN ('web', 'hardware', 'mock')),
    device_id TEXT NULL,
    selected_option TEXT NOT NULL CHECK(selected_option IN ('A', 'B', 'C', 'D')),
    is_correct INTEGER NOT NULL CHECK(is_correct IN (0, 1)),
    misconception TEXT NULL,
    response_time_ms REAL NULL CHECK(response_time_ms IS NULL OR response_time_ms >= 0.0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(round_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_quiz_sessions_status ON quiz_sessions(status);
CREATE INDEX IF NOT EXISTS idx_quiz_rounds_session ON quiz_session_rounds(session_id, round_index);
CREATE INDEX IF NOT EXISTS idx_quiz_votes_round ON quiz_session_votes(round_id);
CREATE INDEX IF NOT EXISTS idx_quiz_votes_student ON quiz_session_votes(student_id);
CREATE INDEX IF NOT EXISTS idx_quiz_votes_analytics ON quiz_session_votes(is_correct, misconception);
