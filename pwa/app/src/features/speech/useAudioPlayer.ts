import { useCallback, useRef } from 'react';
import { getAudioPlayer, stopAudio } from '../../shared/lib/sound';

export interface PlayEvents {
  onPlaying: (roundIndex: number) => void;
  onDone: () => void;
  onError: () => void;
  onBlocked: () => void;
}

/**
 * Thin wrapper over the shared audio element. Owns the playback token that
 * invalidates stale play() runs; event reporting stays with the caller so
 * this hook carries no React state.
 */
export function useAudioPlayer() {
  const playbackTokenRef = useRef(0);

  /** Invalidates any in-flight play() run. */
  const invalidate = useCallback(() => {
    playbackTokenRef.current += 1;
  }, []);

  /** Detaches handlers and stops the element, optionally revoking a blob URL. */
  const stop = useCallback(
    (url?: string | null) => {
      invalidate();
      const player = getAudioPlayer();
      if (player) {
        player.onended = null;
        player.onerror = null;
        stopAudio(player, url ?? undefined);
      }
    },
    [invalidate]
  );

  /**
   * Plays a blob URL, wiring ended/error/blocked events. No-ops when the
   * caller's isCurrent() gate already failed.
   */
  const play = useCallback(
    async (
      player: HTMLAudioElement,
      url: string,
      roundIndex: number,
      isCurrent: () => boolean,
      events: PlayEvents
    ) => {
      const playbackToken = ++playbackTokenRef.current;
      const current = () => isCurrent() && playbackTokenRef.current === playbackToken;
      if (!current()) return;

      player.pause();
      player.src = url;
      player.currentTime = 0;
      player.onended = () => {
        if (!current()) return;
        events.onDone();
      };
      player.onerror = () => {
        if (!current()) return;
        events.onError();
      };
      events.onPlaying(roundIndex);
      try {
        await player.play();
      } catch {
        if (current()) events.onBlocked();
      }
    },
    []
  );

  return { invalidate, stop, play };
}

export type AudioPlayer = ReturnType<typeof useAudioPlayer>;
