-- 012_add_turn_log_pedagogy.sql
-- Week 5 pedagogy labels on turn_logs (concept, error type, scaffolding strategy), all nullable.
-- No CHECK constraints on purpose: the vocabularies live in code and tests, so the taxonomy can grow without a migration.

ALTER TABLE turn_logs ADD COLUMN concept_topic TEXT;
ALTER TABLE turn_logs ADD COLUMN concept_subconcept TEXT;
ALTER TABLE turn_logs ADD COLUMN cnb_topic TEXT;
ALTER TABLE turn_logs ADD COLUMN error_type TEXT;
ALTER TABLE turn_logs ADD COLUMN scaffolding_strategy TEXT;

CREATE INDEX IF NOT EXISTS idx_turn_logs_concept ON turn_logs (concept_topic, concept_subconcept);
