import { parseClickerTimestamp } from './clickerFormat';
import type { ClickerDevice } from './clickers.types';

/** Creation time in epoch milliseconds. An unreadable stamp sorts as the oldest. */
function createdAtMs(device: ClickerDevice): number {
  const epochMs = parseClickerTimestamp(device.created_at);
  return Number.isNaN(epochMs) ? Number.NEGATIVE_INFINITY : epochMs;
}

/** Plain code-unit order on the device id, the same order the server sorts by. */
function compareDeviceIds(first: ClickerDevice, second: ClickerDevice): number {
  if (first.device_id === second.device_id) return 0;
  return first.device_id < second.device_id ? -1 : 1;
}

/** Newest first by creation time; equal times fall back to the device id. */
function compareNewestFirst(first: ClickerDevice, second: ClickerDevice): number {
  const firstMs = createdAtMs(first);
  const secondMs = createdAtMs(second);
  if (firstMs !== secondMs) return firstMs < secondMs ? 1 : -1;
  return compareDeviceIds(first, second);
}

/**
 * The teacher's order for the clicker list. Returns a new array; the input is
 * not changed.
 * 1. Unassigned clickers first, newest first by created_at (device id breaks a tie).
 * 2. Assigned clickers next, in the order they came in (the server sends them
 *    sorted by device id, so that order does not change between reloads).
 * The same list always gives the same order, so rows do not move between reloads.
 *
 * @param {ClickerDevice[]} devices - The clickers as the server sent them.
 * @returns {ClickerDevice[]} The clickers in display order.
 */
export function sortClickersForTeacher(devices: ClickerDevice[]): ClickerDevice[] {
  const unassigned = devices
    .filter((device) => device.assigned_user_id === null)
    .sort(compareNewestFirst);
  const assigned = devices.filter((device) => device.assigned_user_id !== null);
  return [...unassigned, ...assigned];
}
