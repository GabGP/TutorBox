import { describe, expect, it } from 'vitest';
import { CLICKER_ID_ERROR, clickerIdError } from '../clickerId';
import { formatClickerDate } from '../clickerFormat';

describe('clickerIdError', () => {
  it.each(['ESP32-A4CF12', '1', 'a.b_c-d', 'x'.repeat(32)])('accepts %s', (typed) => {
    expect(clickerIdError(typed)).toBeNull();
  });

  it('trims surrounding spaces before checking', () => {
    expect(clickerIdError('  ESP32-A4CF12  ')).toBeNull();
  });

  it.each(['', '   ', 'x'.repeat(33), 'ESP 32', 'ñandú', 'ESP/32'])(
    'rejects %j with the Spanish message',
    (typed) => {
      expect(clickerIdError(typed)).toBe(CLICKER_ID_ERROR);
    }
  );

  it('states the rule in Spanish', () => {
    expect(CLICKER_ID_ERROR).toBe(
      'Use solo letras, números, punto, guion y guion bajo (máximo 32).'
    );
  });
});

describe('formatClickerDate', () => {
  const shortDate = (utcMillis: number) =>
    new Date(utcMillis).toLocaleDateString('es', { day: 'numeric', month: 'short', year: 'numeric' });

  it('reads the stamp as UTC and shows the day in the browser zone', () => {
    // 01:00 UTC on 1 Jan is 31 Dec in Guatemala (UTC-6). Read as local time,
    // the same stamp would show 1 Jan, so this catches that mistake there.
    expect(formatClickerDate('2026-01-01 01:00:00')).toBe(shortDate(Date.UTC(2026, 0, 1, 1)));
  });

  it('renders a short Spanish date with the year', () => {
    const formatted = formatClickerDate('2026-08-29 14:00:00');
    expect(formatted).toContain('2026');
    expect(formatted).toBe(shortDate(Date.UTC(2026, 7, 29, 14)));
  });

  it('accepts an ISO stamp that already carries its zone', () => {
    expect(formatClickerDate('2026-08-29T14:00:00Z')).toBe(shortDate(Date.UTC(2026, 7, 29, 14)));
  });

  it('returns the raw text when it cannot be parsed', () => {
    expect(formatClickerDate('no es fecha')).toBe('no es fecha');
  });
});
