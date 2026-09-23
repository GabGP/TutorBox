/**
 * Builds a `?key=value` query suffix from a params object, skipping
 * undefined / null / empty-string values. Single replacement for the
 * hand-rolled URLSearchParams blocks in bank / generator / speech APIs.
 */
export function toQuery(params: Record<string, string | number | boolean | undefined | null> = {}): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue;
    query.set(key, String(value));
  }
  const serialized = query.toString();
  return serialized ? `?${serialized}` : '';
}
