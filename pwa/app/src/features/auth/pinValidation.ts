/**
 * Shared PIN-pair validation. Single owner of the empty/mismatch/same-as-current
 * trio previously copied between ForcedPinModal and AccountCard.
 * Returns a machine-readable code; callers map it to their own Spanish copy.
 */

export type PinPairError = 'empty' | 'mismatch' | 'same';

/**
 * Validates a new-PIN + confirmation pair against the current PIN.
 *
 * @param a - New PIN entry (already trimmed by the caller).
 * @param b - Confirmation PIN entry (already trimmed by the caller).
 * @param current - Current/temporary PIN, or null when unknown.
 * @returns Error code, or null when the pair is valid.
 */
export function validatePinPair(
  a: string,
  b: string,
  current?: string | null
): PinPairError | null {
  if (!a || !b) return 'empty';
  if (a !== b) return 'mismatch';
  if (current && a === current) return 'same';
  return null;
}
