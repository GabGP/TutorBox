-- 015_add_device_secret.sql
-- Week 7: the secret an ESP32 clicker proves itself with, and the clicker a login session was issued to.
-- secret_hash is the SHA-256 of the secret, never the secret. All three columns are nullable.

ALTER TABLE devices ADD COLUMN secret_hash TEXT;
ALTER TABLE devices ADD COLUMN secret_issued_at TIMESTAMP;
ALTER TABLE sessions ADD COLUMN device_id TEXT;

CREATE INDEX IF NOT EXISTS idx_sessions_device_id ON sessions(device_id) WHERE device_id IS NOT NULL;
