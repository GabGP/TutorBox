import { describe, expect, it } from 'vitest';
import {
  formatCelsius,
  formatGigabytes,
  formatLoadAverage,
  formatMhz,
  formatPercent,
  formatUptime,
  formatWatts,
  worstStatus,
} from '../systemHealthFormat';

describe('systemHealthFormat', () => {
  it('writes numbers in Spanish form, with a dash for a missing reading', () => {
    expect(formatGigabytes(2.34)).toBe('2,3 GB');
    expect(formatPercent(35.4)).toBe('35 %');
    expect(formatPercent(null)).toBe('—');
    expect(formatMhz(1344.2)).toBe('1344 MHz');
    expect(formatMhz(null)).toBe('—');
    expect(formatWatts(5981)).toBe('5,98 W');
    expect(formatCelsius(82.44)).toBe('82,4 °C');
    expect(formatLoadAverage([3.32, 4.45, 3.74])).toBe('3,32 · 4,45 · 3,74');
    expect(formatLoadAverage(null)).toBe('—');
  });

  it('counts uptime in the largest sensible unit', () => {
    expect(formatUptime(98992.6)).toBe('1 d 3 h');
    expect(formatUptime(5 * 3600 + 12 * 60)).toBe('5 h 12 min');
    expect(formatUptime(12 * 60)).toBe('12 min');
    expect(formatUptime(null)).toBe('—');
  });

  it('takes the worst status of a list, and unknown when there is none', () => {
    expect(worstStatus(['ok', 'warn', 'critical'])).toBe('critical');
    expect(worstStatus(['ok', 'warn'])).toBe('warn');
    expect(worstStatus(['unknown', 'ok'])).toBe('ok');
    expect(worstStatus([])).toBe('unknown');
  });
});
