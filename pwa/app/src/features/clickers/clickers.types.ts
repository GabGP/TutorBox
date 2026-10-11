/**
 * One physical ESP32 clicker as listed by `GET /staff/devices`.
 * Timestamps are UTC without a zone marker ("2026-08-29 14:00:00").
 */
export interface ClickerDevice {
  device_id: string;
  assigned_user_id: number | null;
  assigned_username: string | null;
  created_at: string;
  /**
   * Null = never set up over Bluetooth. Absent from backends that predate the
   * field: the screen treats absent and null the same way.
   */
  secret_issued_at?: string | null;
}

/** Response of `POST /staff/devices/{device_id}/assign`. */
export interface ClickerAssignment {
  device_id: string;
  assigned_user_id: number;
  assigned_username: string;
}
