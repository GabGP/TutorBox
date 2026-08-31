-- 008_add_quiz_questions.sql
-- Question repository for diagnostic quiz questions and seed bank

CREATE TABLE IF NOT EXISTS quiz_questions (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    subconcept TEXT NOT NULL,
    question_text TEXT NOT NULL,
    options_json TEXT NOT NULL,
    correct_option TEXT NOT NULL CHECK(correct_option IN ('A', 'B', 'C', 'D')),
    distractors_json TEXT NOT NULL,
    sympy_verified INTEGER NOT NULL DEFAULT 0 CHECK(sympy_verified IN (0, 1)),
    source TEXT NOT NULL DEFAULT 'llm' CHECK(source IN ('llm', 'seed', 'teacher')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX IF NOT EXISTS idx_quiz_questions_topic ON quiz_questions(topic, subconcept);
CREATE INDEX IF NOT EXISTS idx_quiz_questions_created ON quiz_questions(created_at);
