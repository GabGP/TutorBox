-- 012_add_clicker_credentials.sql
-- Week 7 hardware clickers. An ESP32 enrolls itself on its first check-in with a random
-- secret it generated and keeps in flash. The appliance stores only the secret's SHA-256
-- digest, like session tokens. The last-seen columns feed the teacher's fleet view and
-- are refreshed at most every 15 s per clicker, so 30 clickers polling once a second
-- cost about two writes per second instead of thirty.
-- (No semicolons in comments: the migration runner splits statements on them.)

ALTER TABLE devices ADD COLUMN secret_hash TEXT NULL;
ALTER TABLE devices ADD COLUMN last_seen_at TIMESTAMP NULL;
ALTER TABLE devices ADD COLUMN last_rssi INTEGER NULL;
ALTER TABLE devices ADD COLUMN last_battery_mv INTEGER NULL;
ALTER TABLE devices ADD COLUMN firmware TEXT NULL
