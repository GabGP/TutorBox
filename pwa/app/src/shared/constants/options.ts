/**
 * Canonical quiz option letters. Single source of truth for 'A'|'B'|'C'|'D'.
 * Replaces the 5+ duplicated literals across voting, keyboard, tally, bank and display layers.
 */

export type OptionLetter = 'A' | 'B' | 'C' | 'D';

export const OPTION_LETTERS: readonly OptionLetter[] = ['A', 'B', 'C', 'D'] as const;

const LETTER_SET: ReadonlySet<string> = new Set(OPTION_LETTERS);

/** Type-guard for runtime validation of option letters. */
export function isOptionLetter(value: unknown): value is OptionLetter {
  return typeof value === 'string' && LETTER_SET.has(value);
}
