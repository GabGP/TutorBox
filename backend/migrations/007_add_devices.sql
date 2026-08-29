-- 007_add_devices.sql
-- Device registry for physical ESP32 clickers and classroom pairing

CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    assigned_user_id INTEGER UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_devices_assigned_user ON devices(assigned_user_id);
