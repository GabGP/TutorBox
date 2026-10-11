-- 013_add_game_events.sql
-- Week 6 Mode 3: one row per answer tapped in a grade app (pwa/tareas), stored when the phone reaches the appliance.
-- client_event_id is generated on the phone. Its UNIQUE constraint is what makes a repeated delivery harmless.
-- No CHECK constraints on the label columns, as in 012: the vocabularies live in code and tests.

CREATE TABLE IF NOT EXISTS game_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_event_id TEXT NOT NULL UNIQUE,
    install_id TEXT NOT NULL,
    student_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    grade TEXT NOT NULL,
    lesson_id TEXT NOT NULL,
    round_index INTEGER NOT NULL CHECK(round_index >= 0),
    attempt INTEGER NOT NULL CHECK(attempt >= 1),
    is_correct INTEGER NOT NULL CHECK(is_correct IN (0, 1)),
    answer TEXT NULL,
    expected TEXT NULL,
    app_version TEXT NULL,
    occurred_at TEXT NOT NULL,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cnb_topic TEXT NULL,
    concept_topic TEXT NULL,
    concept_subconcept TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_game_events_concept ON game_events (concept_topic, concept_subconcept);
