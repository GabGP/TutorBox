/**
 * Presence contract of `GET /api/v1/presence/class` (staff only) and the
 * heartbeat that feeds it. The server decides every status; the screen shows
 * them as they arrive and never recomputes a threshold.
 */

/** `online` = heard from recently, `dropped` = was heard and went silent, `absent` = never heard. */
export type PresenceStatus = 'online' | 'dropped' | 'absent';

/** Radio quality of a clicker, decided by the server. */
export type SignalStrength = 'good' | 'fair' | 'weak';

/** One way a student is connected: the phone, or the clicker. */
export interface PresenceChannel {
  status: PresenceStatus;
  /** Null when `absent`. */
  seconds_ago: number | null;
}

/** An assigned ESP32 clicker as the server sees it. */
export interface ClickerPresence extends PresenceChannel {
  device_id: string;
  /** Null when the clicker reports no signal (even when online). */
  signal: SignalStrength | null;
  rssi: number | null;
  /** Null when the clicker reports no battery level (even when online). */
  battery_pct: number | null;
}

/** One student row of the class list. */
export interface StudentPresence {
  user_id: number;
  username: string;
  status: PresenceStatus;
  phone: PresenceChannel;
  /** Null when the student has no clicker assigned. */
  clicker: ClickerPresence | null;
}

/** Response of `GET /api/v1/presence/class`. */
export interface ClassPresence {
  online: number;
  total: number;
  /** Already sorted by username by the server; the screen keeps that order. */
  students: StudentPresence[];
  /** Clicker ids with no student assigned. */
  unassigned_clickers: string[];
}
