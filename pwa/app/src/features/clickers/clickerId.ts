/** Same rule the backend applies to `device_id`: 1 to 32 letters, digits, `_`, `.` or `-`. */
export const CLICKER_ID_PATTERN = /^[A-Za-z0-9_.-]{1,32}$/;

export const CLICKER_ID_ERROR =
  'Use solo letras, números, punto, guion y guion bajo (máximo 32).';

/**
 * Checks a typed clicker id after trimming surrounding spaces.
 * Returns the Spanish error text when it breaks the rule, otherwise null.
 */
export function clickerIdError(typedId: string): string | null {
  return CLICKER_ID_PATTERN.test(typedId.trim()) ? null : CLICKER_ID_ERROR;
}
