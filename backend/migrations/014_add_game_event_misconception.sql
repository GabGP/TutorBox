-- 014_add_game_event_misconception.sql
-- Week 6: the misconception behind a wrong answer in a grade app, as the game names it. Nullable.
-- No CHECK constraint, as in migration 012: the vocabulary lives in code and tests.

ALTER TABLE game_events ADD COLUMN misconception TEXT;
