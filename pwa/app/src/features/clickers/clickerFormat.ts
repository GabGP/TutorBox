/**
 * Short Spanish day, month and year ("29 ago 2026"). `shared/lib/format`
 * is not used: it reads timestamps without a zone as local time, which
 * would shift the clicker dates the backend sends in UTC.
 */
const SHORT_DATE_OPTIONS: Intl.DateTimeFormatOptions = {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
};

/** A trailing `Z` or `+hh:mm` / `-hhmm` offset, when the stamp carries one. */
const ZONE_SUFFIX = /(Z|[+-]\d{2}:?\d{2})$/i;

/**
 * Formats a backend timestamp ("2026-08-29 14:00:00", UTC, no zone marker)
 * as a short date in the browser's own time zone.
 * Returns the raw text when it cannot be parsed.
 */
export function formatClickerDate(stamp: string): string {
  const isoText = stamp.trim().replace(' ', 'T');
  const utcText = ZONE_SUFFIX.test(isoText) ? isoText : `${isoText}Z`;
  const date = new Date(utcText);
  return Number.isNaN(date.getTime())
    ? stamp
    : date.toLocaleDateString('es', SHORT_DATE_OPTIONS);
}
