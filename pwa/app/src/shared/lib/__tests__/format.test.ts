import { describe, expect, it } from 'vitest';
import { formatDuration, formatFullDate } from '../format';

describe('formatDuration', () => {
  it('renders seconds with an optional estimate prefix', () => {
    expect(formatDuration(null)).toBe('');
    expect(formatDuration(undefined)).toBe('');
    expect(formatDuration(-1)).toBe('');
    expect(formatDuration(0)).toBe('0s');
    expect(formatDuration(45)).toBe('45s');
    expect(formatDuration(45, true)).toBe('~45s');
  });

  it('renders minutes with remainder', () => {
    expect(formatDuration(60)).toBe('1 min');
    expect(formatDuration(75)).toBe('1 min 15s');
    expect(formatDuration(153, true)).toBe('~2 min 33s');
  });
});

describe('formatFullDate', () => {
  it('returns an em-dash without a value', () => {
    expect(formatFullDate()).toBe('—');
    expect(formatFullDate(null)).toBe('—');
  });

  it('passes invalid dates through', () => {
    expect(formatFullDate('not-a-date')).toBe('not-a-date');
  });

  it('renders a Spanish datetime stamp', () => {
    const out = formatFullDate('2026-03-04T10:05:00');
    expect(out).toContain('04/03/2026');
    expect(out).toContain('10:05');
  });
});
