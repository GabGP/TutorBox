import { describe, expect, it } from 'vitest';
import type { StudentPresence } from '../presence.types';
import {
  formatSecondsAgo,
  lowBatteryLabel,
  mostRecentDropSeconds,
  presenceSummaryLabel,
  signalLabel,
  studentStatusLabel,
} from '../presenceLabels';

/** A student with a phone and no clicker, unless the test adds one. */
function studentWith(overrides: Partial<StudentPresence>): StudentPresence {
  return {
    user_id: 1,
    username: 'ana',
    status: 'online',
    phone: { status: 'online', seconds_ago: 2 },
    clicker: null,
    ...overrides,
  };
}

const CLICKER_AT = (status: 'online' | 'dropped' | 'absent', seconds: number | null) => ({
  device_id: 'ESP32-A4CF12',
  status,
  seconds_ago: seconds,
  signal: null,
  rssi: null,
  battery_pct: null,
});

describe('formatSecondsAgo', () => {
  it('uses seconds under a minute and whole minutes from there', () => {
    expect(formatSecondsAgo(0)).toBe('hace 0 s');
    expect(formatSecondsAgo(12)).toBe('hace 12 s');
    expect(formatSecondsAgo(59)).toBe('hace 59 s');
    expect(formatSecondsAgo(60)).toBe('hace 1 min');
    expect(formatSecondsAgo(125)).toBe('hace 2 min');
  });
});

describe('presenceSummaryLabel', () => {
  it('shows the connected count alone when nobody dropped', () => {
    expect(presenceSummaryLabel(18, 24, 0)).toBe('18 de 24 conectados');
  });

  it('adds the dropped count in the singular and the plural', () => {
    expect(presenceSummaryLabel(18, 24, 1)).toBe('18 de 24 conectados · 1 se cayó');
    expect(presenceSummaryLabel(18, 24, 2)).toBe('18 de 24 conectados · 2 se cayeron');
  });
});

describe('studentStatusLabel', () => {
  it('says Conectado when the server marks the student online', () => {
    expect(studentStatusLabel(studentWith({ status: 'online' }))).toBe('Conectado');
  });

  it('says No ha entrado when the student never came in', () => {
    const absent = studentWith({
      status: 'absent',
      phone: { status: 'absent', seconds_ago: null },
    });
    expect(studentStatusLabel(absent)).toBe('No ha entrado');
  });

  it('says how long ago the phone dropped', () => {
    const dropped = studentWith({
      status: 'dropped',
      phone: { status: 'dropped', seconds_ago: 12 },
    });
    expect(studentStatusLabel(dropped)).toBe('Se cayó hace 12 s');
  });

  it('uses the more recent drop when both the phone and the clicker dropped', () => {
    const bothDropped = studentWith({
      status: 'dropped',
      phone: { status: 'dropped', seconds_ago: 300 },
      clicker: CLICKER_AT('dropped', 40),
    });
    expect(studentStatusLabel(bothDropped)).toBe('Se cayó hace 40 s');
  });

  it('ignores a clicker that is still online when the phone dropped', () => {
    const phoneDropped = studentWith({
      status: 'dropped',
      phone: { status: 'dropped', seconds_ago: 300 },
      clicker: CLICKER_AT('online', 3),
    });
    expect(studentStatusLabel(phoneDropped)).toBe('Se cayó hace 5 min');
  });

  it('says Se cayó without an age when the server gave none', () => {
    const noAge = studentWith({
      status: 'dropped',
      phone: { status: 'absent', seconds_ago: null },
    });
    expect(mostRecentDropSeconds(noAge)).toBeNull();
    expect(studentStatusLabel(noAge)).toBe('Se cayó');
  });
});

describe('signalLabel', () => {
  it('gives the text alternative for each signal strength', () => {
    expect(signalLabel('good')).toBe('Señal buena');
    expect(signalLabel('fair')).toBe('Señal regular');
    expect(signalLabel('weak')).toBe('Señal débil');
  });
});

describe('lowBatteryLabel', () => {
  it('warns below 20 percent only', () => {
    expect(lowBatteryLabel(19)).toBe('Batería baja 19 %');
    expect(lowBatteryLabel(20)).toBeNull();
    expect(lowBatteryLabel(88)).toBeNull();
  });

  it('stays quiet when the level is unknown', () => {
    expect(lowBatteryLabel(null)).toBeNull();
  });
});
