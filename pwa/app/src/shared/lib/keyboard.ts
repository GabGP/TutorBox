import { useEffect } from 'react';

export type OptionLetter = 'A' | 'B' | 'C' | 'D';

const KEY_MAP: Record<string, OptionLetter> = {
  a: 'A',
  b: 'B',
  c: 'C',
  d: 'D',
  '1': 'A',
  '2': 'B',
  '3': 'C',
  '4': 'D',
};

/**
 * Normalizes alphanumeric keyboard inputs (A-D, 1-4) to standardized quiz option letters.
 *
 * @param {string} key - Raw keyboard event key string.
 * @returns {OptionLetter | null} Mapped option letter ('A', 'B', 'C', 'D') or null if non-matching.
 */
export function mapKeyToOption(key: string): OptionLetter | null {
  return KEY_MAP[key.toLowerCase()] || null;
}

/**
 * Custom React hook for listening to global keyboard shortcuts during quiz rounds.
 * Ignores keystrokes when form inputs/textareas are actively focused.
 *
 * @param {(option: OptionLetter) => void} onSelect - Vote selection callback.
 * @param {boolean} enabled - Whether keyboard listener should be active.
 * @returns {void}
 */
export function useOptionKeyboard(
  onSelect: (option: OptionLetter) => void,
  enabled: boolean
): void {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't intercept when focusing inputs
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes((event.target as HTMLElement)?.tagName)) {
        return;
      }
      const option = mapKeyToOption(event.key);
      if (option) {
        event.preventDefault();
        onSelect(option);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onSelect, enabled]);
}
