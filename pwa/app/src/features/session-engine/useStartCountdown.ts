import { useEffect, useState } from 'react';

const TICK_MS = 100;

/**
 * Whole seconds left of a game's start countdown (3, 2, 1), or null when none runs.
 *
 * `startsIn` comes from the server with every poll (round.starts_in). Each new value sets the
 * local deadline again, and the hook ticks between polls, so every screen shows the same digit
 * within one poll of the others.
 *
 * @param {number | null | undefined} startsIn - Seconds until the round takes votes.
 * @returns {number | null} The digit to show, or null when voting has begun.
 */
export function useStartCountdown(startsIn: number | null | undefined): number | null {
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null);

  useEffect(() => {
    if (startsIn == null || startsIn <= 0) {
      setSecondsLeft(null);
      return;
    }
    const deadline = Date.now() + startsIn * 1000;
    const tick = () => {
      const remainingSeconds = (deadline - Date.now()) / 1000;
      setSecondsLeft(remainingSeconds > 0 ? Math.ceil(remainingSeconds) : null);
    };
    tick();
    const intervalId = setInterval(tick, TICK_MS);
    return () => clearInterval(intervalId);
  }, [startsIn]);

  return secondsLeft;
}
