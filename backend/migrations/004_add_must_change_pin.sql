-- 004_add_must_change_pin.sql
-- Flags accounts that must rotate their PIN on next login (staff-initiated resets).
ALTER TABLE users ADD COLUMN must_change_pin INTEGER NOT NULL DEFAULT 0;
