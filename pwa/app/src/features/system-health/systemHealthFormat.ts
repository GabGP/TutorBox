import type { HealthStatus } from './systemHealth.types';

const decimalFormat = (fractionDigits: number) =>
  new Intl.NumberFormat('es', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });

/** Status word shown on each card, so the colour is never the only signal. */
export const STATUS_WORD: Record<HealthStatus, string> = {
  ok: 'Bien',
  warn: 'Atención',
  critical: 'Crítico',
  unknown: 'Sin datos',
};

/** Gigabytes with one decimal, in Spanish form (2,3 GB). */
export function formatGigabytes(gigabytes: number): string {
  return `${decimalFormat(1).format(gigabytes)} GB`;
}

/** A whole percentage (35 %), or a dash when the reading is missing. */
export function formatPercent(percent: number | null): string {
  return percent === null ? '—' : `${Math.round(percent)} %`;
}

/** A clock in MHz, or a dash. */
export function formatMhz(mhz: number | null): string {
  return mhz === null ? '—' : `${Math.round(mhz)} MHz`;
}

/** Power in watts from milliwatts (5,98 W). */
export function formatWatts(milliwatts: number): string {
  return `${decimalFormat(2).format(milliwatts / 1000)} W`;
}

export function formatCelsius(celsius: number): string {
  return `${decimalFormat(1).format(celsius)} °C`;
}

/** The three load averages, as Spanish numbers. */
export function formatLoadAverage(values: number[] | null): string {
  return values === null ? '—' : values.map((value) => decimalFormat(2).format(value)).join(' · ');
}

/** Uptime as "3 d 4 h", "5 h 12 min" or "12 min". */
export function formatUptime(seconds: number | null): string {
  if (seconds === null) return '—';
  const totalMinutes = Math.floor(seconds / 60);
  const days = Math.floor(totalMinutes / 1440);
  const hours = Math.floor((totalMinutes % 1440) / 60);
  const minutes = totalMinutes % 60;
  if (days > 0) return `${days} d ${hours} h`;
  if (hours > 0) return `${hours} h ${minutes} min`;
  return `${minutes} min`;
}

/** The worst status of a list of readings (unknown when there is none). */
export function worstStatus(statuses: HealthStatus[]): HealthStatus {
  if (statuses.includes('critical')) return 'critical';
  if (statuses.includes('warn')) return 'warn';
  if (statuses.includes('ok')) return 'ok';
  return 'unknown';
}
