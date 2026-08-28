-- 005_add_users_deleted_at.sql
-- Soft-delete marker + original-username retention for account recovery.
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE users ADD COLUMN former_username TEXT;
