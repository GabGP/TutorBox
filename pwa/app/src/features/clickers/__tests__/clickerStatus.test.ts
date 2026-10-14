import { describe, expect, it } from 'vitest';
import { NEW_CLICKER_WINDOW_MS, hasNeverConnected, isNewClicker } from '../clickerStatus';
import type { ClickerDevice } from '../clickers.types';

/** The fixed "now" for these tests: 12:00:00 UTC on 13 Oct 2026. */
const NOW_MS = Date.UTC(2026, 9, 13, 12, 0, 0);

function unassignedClicker(firstContact: string | null): ClickerDevice {
  return {
    device_id: 'ESP32-N1',
    assigned_user_id: null,
    assigned_username: null,
    created_at: '2026-10-13 11:00:00',
    secret_issued_at: firstContact,
  };
}

describe('isNewClicker', () => {
  it('uses a window of 10 minutes', () => {
    expect(NEW_CLICKER_WINDOW_MS).toBe(10 * 60 * 1000);
  });

  it('is true just under 10 minutes after the first contact', () => {
    expect(isNewClicker(unassignedClicker('2026-10-13 11:50:01'), NOW_MS)).toBe(true);
  });

  it('is false at exactly 10 minutes after the first contact', () => {
    expect(isNewClicker(unassignedClicker('2026-10-13 11:50:00'), NOW_MS)).toBe(false);
  });

  it('is false just over 10 minutes after the first contact', () => {
    expect(isNewClicker(unassignedClicker('2026-10-13 11:49:59'), NOW_MS)).toBe(false);
  });

  it('is true for a first contact a moment ago', () => {
    expect(isNewClicker(unassignedClicker('2026-10-13 11:59:30'), NOW_MS)).toBe(true);
  });

  it('is true for a first contact a few seconds ahead of this browser clock', () => {
    expect(isNewClicker(unassignedClicker('2026-10-13 12:00:05'), NOW_MS)).toBe(true);
  });

  it('is true for a first contact just under 10 minutes ahead of this browser clock', () => {
    expect(isNewClicker(unassignedClicker('2026-10-13 12:09:59'), NOW_MS)).toBe(true);
  });

  it('is false for a first contact 10 minutes or more ahead: the clocks disagree', () => {
    expect(isNewClicker(unassignedClicker('2026-10-13 12:10:00'), NOW_MS)).toBe(false);
    expect(isNewClicker(unassignedClicker('2026-10-20 12:00:00'), NOW_MS)).toBe(false);
  });

  it('is false for a clicker that holds a student, however recent its first contact', () => {
    const assigned: ClickerDevice = {
      ...unassignedClicker('2026-10-13 11:59:30'),
      assigned_user_id: 1,
      assigned_username: 'ana',
    };
    expect(isNewClicker(assigned, NOW_MS)).toBe(false);
  });

  it('is false for a clicker that never connected (null first contact)', () => {
    expect(isNewClicker(unassignedClicker(null), NOW_MS)).toBe(false);
  });

  it('is false for a clicker from a backend without secret_issued_at', () => {
    const olderBackend: ClickerDevice = {
      device_id: 'ESP32-LEGACY',
      assigned_user_id: null,
      assigned_username: null,
      created_at: '2026-10-13 11:00:00',
    };
    expect(isNewClicker(olderBackend, NOW_MS)).toBe(false);
  });

  it('is false when the first contact cannot be read', () => {
    expect(isNewClicker(unassignedClicker('no es fecha'), NOW_MS)).toBe(false);
  });
});

describe('hasNeverConnected', () => {
  it('is true for a null first contact', () => {
    expect(hasNeverConnected(unassignedClicker(null))).toBe(true);
  });

  it('is true when the backend leaves the field out', () => {
    const olderBackend: ClickerDevice = {
      device_id: 'ESP32-LEGACY',
      assigned_user_id: null,
      assigned_username: null,
      created_at: '2026-10-13 11:00:00',
    };
    expect(hasNeverConnected(olderBackend)).toBe(true);
  });

  it('is false once a first contact is recorded', () => {
    expect(hasNeverConnected(unassignedClicker('2026-10-13 11:00:00'))).toBe(false);
  });
});
