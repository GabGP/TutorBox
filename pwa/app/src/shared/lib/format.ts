/**
 * Canonical duration / date formatting. Converges the three copies previously
 * split between QuestionGenerationProgress.formatDuration, telemetryFormat and
 * TelemetryDetailSheet.formatFullDate.
 */

/** Seconds rendered as `45s` / `1 min 15s`, with optional `~` estimate prefix. */
export function formatDuration(seconds: number | null | undefined, isEstimate = false): string {
  if (seconds == null || seconds < 0) return '';
  const normalized = Math.round(seconds);
  const prefix = isEstimate ? '~' : '';
  if (normalized < 60) return `${prefix}${normalized}s`;
  const mins = Math.floor(normalized / 60);
  const rem = normalized % 60;
  return rem > 0 ? `${prefix}${mins} min ${rem}s` : `${prefix}${mins} min`;
}

/** Full `dd/mm/yyyy hh:mm` stamp; em-dash when the log carries no date. */
export function formatFullDate(value?: string | null): string {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString('es', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
