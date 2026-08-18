-- 002_add_user_role.sql
-- Adds a role column to the users table for student/teacher/admin distinction.

ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'student';
