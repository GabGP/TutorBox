/**
 * Shared formatting helpers for generation telemetry display.
 * Latency speaks min/sec (`29s`, `1 min 15s`), matching the language of
 * the generation progress clock.
 */

/** Latency in ms rendered as min/sec. */
export function formatLatency(ms: number): string {
  const totalSeconds = Math.max(0, Math.round(ms / 1000));
  if (totalSeconds < 60) return `${totalSeconds}s`;
  const mins = Math.floor(totalSeconds / 60);
  const rem = totalSeconds % 60;
  return rem > 0 ? `${mins} min ${rem}s` : `${mins} min`;
}

/** Success rate fraction (0–1) rendered as percent (`89.58%`). */
export function formatPercent(rate: number): string {
  return `${Number((rate * 100).toFixed(2))}%`;
}

/** Compact `dd/mm hh:mm` stamp; empty when the log carries no date. */
export function formatShortDate(value?: string | null): string {
  if (!value) return '';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '';
  return d
    .toLocaleString('es', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
    .replace(', ', ' ');
}
