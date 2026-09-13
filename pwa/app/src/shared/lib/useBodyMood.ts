import { useEffect } from 'react';

export type MoodType = 'good' | 'bad' | 'final' | null;

/**
 * Custom React hook that binds ambient theme mood tokens ('good', 'bad', 'final')
 * directly to the HTML document body `data-mood` attribute for dynamic UI tinting.
 *
 * @param {MoodType} [mood] - Current visual mood token.
 * @returns {void}
 */
export function useBodyMood(mood?: MoodType): void {
  useEffect(() => {
    if (typeof document === 'undefined') return;

    if (mood) {
      document.body.dataset.mood = mood;
    } else {
      delete document.body.dataset.mood;
    }

    return () => {
      delete document.body.dataset.mood;
    };
  }, [mood]);
}
