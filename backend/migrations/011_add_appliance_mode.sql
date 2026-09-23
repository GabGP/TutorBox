-- 011_add_appliance_mode.sql
-- Classroom-wide active mode picked by the teacher (the appliance has no keyboard).
-- Single row (id = 1) so the choice survives a power cycle.

CREATE TABLE IF NOT EXISTS appliance_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    mode TEXT NOT NULL DEFAULT 'quiz' CHECK (mode IN ('quiz', 'tutor', 'apps')),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER NULL REFERENCES users(id) ON DELETE SET NULL
);

INSERT OR IGNORE INTO appliance_state (id, mode) VALUES (1, 'quiz');
