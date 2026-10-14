import { parseClickerTimestamp } from './clickerFormat';
import type { ClickerDevice } from './clickers.types';

/** An unassigned clicker stays marked Nuevo for this long after its first contact. */
export const NEW_CLICKER_WINDOW_MS = 10 * 60 * 1000;

/**
 * True when the clicker was added by hand and has never connected: the
 * server has no first-contact time for it yet (secret_issued_at is null or absent).
 */
export function hasNeverConnected(device: ClickerDevice): boolean {
  return device.secret_issued_at == null;
}

/**
 * True for an unassigned clicker whose first contact was less than
 * NEW_CLICKER_WINDOW_MS before `nowMs`. The caller passes the clock in, so the
 * edges can be tested. The first contact is stamped by the appliance's clock and
 * `nowMs` comes from this browser's, so a first contact up to one window ahead
 * still counts as new. Further ahead than that, the two clocks disagree and the
 * chip is not shown, so a wrong clock cannot mark a clicker as new for days.
 * An unreadable timestamp is never new.
 *
 * @param {ClickerDevice} device - The clicker to check.
 * @param {number} nowMs - The current time, in epoch milliseconds.
 * @returns {boolean} Whether the clicker shows the Nuevo chip.
 */
export function isNewClicker(device: ClickerDevice, nowMs: number): boolean {
  const firstContact = device.secret_issued_at;
  if (device.assigned_user_id !== null || firstContact == null) return false;
  const sinceFirstContactMs = nowMs - parseClickerTimestamp(firstContact);
  return Math.abs(sinceFirstContactMs) < NEW_CLICKER_WINDOW_MS;
}
