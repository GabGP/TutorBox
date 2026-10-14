import { describe, expect, it } from 'vitest';
import { sortClickersForTeacher } from '../clickerOrder';
import type { ClickerDevice } from '../clickers.types';

/** An unassigned clicker created on 29 Aug 2026 that never connected. */
function clicker(deviceId: string, overrides: Partial<ClickerDevice> = {}): ClickerDevice {
  return {
    device_id: deviceId,
    assigned_user_id: null,
    assigned_username: null,
    created_at: '2026-08-29 14:00:00',
    secret_issued_at: null,
    ...overrides,
  };
}

function holdingStudent(deviceId: string, userId: number, username: string): ClickerDevice {
  return clicker(deviceId, { assigned_user_id: userId, assigned_username: username });
}

const idsOf = (devices: ClickerDevice[]) => devices.map((device) => device.device_id);

describe('sortClickersForTeacher', () => {
  it('puts the unassigned clickers before the assigned ones', () => {
    const sorted = sortClickersForTeacher([
      holdingStudent('ESP32-A', 1, 'ana'),
      clicker('ESP32-B'),
    ]);
    expect(idsOf(sorted)).toEqual(['ESP32-B', 'ESP32-A']);
  });

  it('orders the unassigned clickers newest first by created_at', () => {
    const sorted = sortClickersForTeacher([
      clicker('ESP32-OLD', { created_at: '2026-08-01 08:00:00' }),
      clicker('ESP32-NEW', { created_at: '2026-10-13 09:30:00' }),
      clicker('ESP32-MID', { created_at: '2026-09-02 17:45:00' }),
    ]);
    expect(idsOf(sorted)).toEqual(['ESP32-NEW', 'ESP32-MID', 'ESP32-OLD']);
  });

  it('ignores the first-contact time when it orders the unassigned clickers', () => {
    const sorted = sortClickersForTeacher([
      clicker('ESP32-OLD', { created_at: '2026-08-01 08:00:00', secret_issued_at: '2026-10-13 11:59:00' }),
      clicker('ESP32-NEW', { created_at: '2026-10-13 09:30:00', secret_issued_at: null }),
    ]);
    expect(idsOf(sorted)).toEqual(['ESP32-NEW', 'ESP32-OLD']);
  });

  it('breaks a tie in created_at by device id, in code order', () => {
    const sorted = sortClickersForTeacher([clicker('ESP32-B'), clicker('ESP32-A')]);
    expect(idsOf(sorted)).toEqual(['ESP32-A', 'ESP32-B']);
  });

  it('keeps the assigned clickers in the order they came in', () => {
    const sorted = sortClickersForTeacher([
      holdingStudent('ESP32-Z', 2, 'beto'),
      holdingStudent('ESP32-A', 1, 'ana'),
    ]);
    expect(idsOf(sorted)).toEqual(['ESP32-Z', 'ESP32-A']);
  });

  it('sorts an unreadable created_at as the oldest unassigned clicker', () => {
    const sorted = sortClickersForTeacher([
      clicker('ESP32-BAD', { created_at: 'no es fecha' }),
      clicker('ESP32-OLD', { created_at: '2026-08-01 08:00:00' }),
    ]);
    expect(idsOf(sorted)).toEqual(['ESP32-OLD', 'ESP32-BAD']);
  });

  it('gives the same order when the same clickers come back in a later reload', () => {
    const reloaded = [
      clicker('ESP32-NEW', { created_at: '2026-10-13 09:30:00' }),
      clicker('ESP32-OLD', { created_at: '2026-08-01 08:00:00' }),
      holdingStudent('ESP32-A', 1, 'ana'),
    ];
    const first = sortClickersForTeacher(reloaded);
    expect(idsOf(sortClickersForTeacher(first))).toEqual(idsOf(first));
  });

  it('returns a new array and leaves the input in the order it was given', () => {
    const input = [holdingStudent('ESP32-A', 1, 'ana'), clicker('ESP32-B')];
    const sorted = sortClickersForTeacher(input);
    expect(sorted).not.toBe(input);
    expect(idsOf(input)).toEqual(['ESP32-A', 'ESP32-B']);
  });

  it('returns an empty list for no clickers', () => {
    expect(sortClickersForTeacher([])).toEqual([]);
  });
});
