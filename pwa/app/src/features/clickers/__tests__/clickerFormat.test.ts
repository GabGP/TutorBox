import { describe, expect, it } from 'vitest';
import { formatClickerDate, parseClickerTimestamp } from '../clickerFormat';

describe('parseClickerTimestamp', () => {
  it('reads a zone-less stamp as UTC, whatever the browser time zone', () => {
    expect(parseClickerTimestamp('2026-08-29 14:00:00')).toBe(Date.UTC(2026, 7, 29, 14, 0, 0));
  });

  it('honours a trailing Z and a numeric offset when the stamp has one', () => {
    expect(parseClickerTimestamp('2026-08-29T14:00:00Z')).toBe(Date.UTC(2026, 7, 29, 14, 0, 0));
    expect(parseClickerTimestamp('2026-08-29T14:00:00+02:00')).toBe(
      Date.UTC(2026, 7, 29, 12, 0, 0)
    );
  });

  it('ignores surrounding spaces', () => {
    expect(parseClickerTimestamp('  2026-08-29 14:00:00 ')).toBe(Date.UTC(2026, 7, 29, 14, 0, 0));
  });

  it('returns NaN for text that is not a time', () => {
    expect(parseClickerTimestamp('no es fecha')).toBeNaN();
  });
});

describe('formatClickerDate', () => {
  it('formats the stamp as a short Spanish date', () => {
    const expected = new Date(Date.UTC(2026, 7, 29, 14, 0, 0)).toLocaleDateString('es', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
    expect(formatClickerDate('2026-08-29 14:00:00')).toBe(expected);
  });

  it('returns the raw text when it cannot be parsed', () => {
    expect(formatClickerDate('no es fecha')).toBe('no es fecha');
  });
});
