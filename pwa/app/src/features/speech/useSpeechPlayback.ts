import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { getAudioPlayer, stopAudio, unlockAudio } from '../../shared/lib/sound';
import { getSpeechVoiceKey, speechApi } from './speechApi';
import { SpeechLanguage, SpeechState } from './speech.types';
import { useAudioPlayer } from './useAudioPlayer';
import { useVoiceCache } from './useVoiceCache';

export interface UseSpeechPlaybackReturn {
  state: SpeechState;
  message: string;
  currentRound: number;
  speak: (roundIndex: number) => Promise<void>;
  prefetch: (roundIndex: number) => Promise<void>;
  stopPlayback: () => void;
}

function waitForNextPaint(): Promise<void> {
  if (typeof requestAnimationFrame === 'function') {
    return new Promise((resolve) => requestAnimationFrame(() => resolve()));
  }
  return new Promise((resolve) => setTimeout(resolve, 0));
}

/**
 * Speech playback orchestration: voice-keyed blob cache (useVoiceCache) plus
 * audio element control (useAudioPlayer), with run/generation tokens that
 * invalidate stale fetches and plays. Pre-fetches WAV blobs on round close
 * and bypasses mobile autoplay blocks.
 */
export function useSpeechPlayback(
  sessionId: string | null,
  language: SpeechLanguage = 'es'
): UseSpeechPlaybackReturn {
  const [state, setState] = useState<SpeechState>('idle');
  const [message, setMessage] = useState('');
  const [currentRound, setCurrentRound] = useState<number>(-1);

  const activeVoiceKey = getSpeechVoiceKey(language);
  const [prevVoiceKey, setPrevVoiceKey] = useState(activeVoiceKey);

  const {
    prefetch,
    generation: cacheGeneration,
    bumpGeneration,
    keyMatches,
    setKey,
    peekUrl,
    readCached,
    store,
    clearSlot,
    drop,
    release,
    getInFlight,
    clearInFlight,
  } = useVoiceCache(sessionId, language);
  const { stop: stopPlayer, play } = useAudioPlayer();
  const activeRunRef = useRef(0);
  // Tracks an in-progress run independently of rendered state, so a tap
  // can never be swallowed by a stale `loading` closure nor start a
  // duplicate fetch. Always released in `finally`.
  const busyRef = useRef(false);
  // Ref mirrors so speak/stopPlayback stay referentially stable instead of
  // churning on every state transition.
  const stateRef = useRef(state);
  const currentRoundRef = useRef(currentRound);
  useEffect(() => {
    stateRef.current = state;
    currentRoundRef.current = currentRound;
  }, [state, currentRound]);

  // Reset cached clip and preparation state when the saved voice changes.
  // This must run before child reveal effects can autoplay after Settings
  // closes; a passive effect lets autoplay race the old clip and skip the
  // preparation state.
  useLayoutEffect(() => {
    if (prevVoiceKey !== activeVoiceKey) {
      bumpGeneration();
      activeRunRef.current += 1;
      stopPlayer(peekUrl());
      busyRef.current = false;
      setPrevVoiceKey(activeVoiceKey);
      setState('idle');
      setMessage('');
      drop();
      setKey(activeVoiceKey);
      clearInFlight();
    }
  }, [
    activeVoiceKey,
    prevVoiceKey,
    bumpGeneration,
    stopPlayer,
    peekUrl,
    drop,
    setKey,
    clearInFlight,
  ]);

  const stopPlayback = useCallback(() => {
    activeRunRef.current += 1;
    stopPlayer();
    busyRef.current = false;
    if (stateRef.current === 'playing' || stateRef.current === 'loading') {
      setState('idle');
      setMessage('');
    }
  }, [stopPlayer]);

  const playCachedUrl = useCallback(
    async (
      playerEl: HTMLAudioElement,
      url: string,
      roundIndex: number,
      isCurrent: () => boolean
    ) => {
      await play(playerEl, url, roundIndex, isCurrent, {
        onPlaying: (idx) => {
          setCurrentRound(idx);
          setState('playing');
          setMessage('Leyendo la explicación en voz alta…');
        },
        onDone: () => {
          setState('done');
          setMessage('Explicación leída.');
        },
        onError: () => {
          setState('error');
          setMessage('No se pudo reproducir el audio.');
        },
        onBlocked: () => {
          setState('blocked');
          setMessage('Toque “Escuchar” para reproducir la explicación.');
        },
      });
    },
    [play]
  );

  const speak = useCallback(
    async (roundIndex: number) => {
      if (!sessionId) return;
      const key = getSpeechVoiceKey(language);
      if (busyRef.current) return;
      if (
        stateRef.current === 'playing' &&
        currentRoundRef.current === roundIndex &&
        keyMatches(key)
      ) {
        return;
      }
      busyRef.current = true;
      const generation = cacheGeneration();
      const runId = ++activeRunRef.current;
      const isCurrent = () =>
        cacheGeneration() === generation && activeRunRef.current === runId;
      try {
        const playerEl = getAudioPlayer();
        if (!playerEl) return;
        const cachedUrl = readCached(roundIndex, key);
        if (cachedUrl) {
          await playCachedUrl(playerEl, cachedUrl, roundIndex, isCurrent);
          return;
        }

        const inFlight = getInFlight();
        if (
          inFlight?.roundIndex === roundIndex &&
          inFlight.key === key &&
          inFlight.generation === generation
        ) {
          setState('loading');
          setMessage('Preparando la voz…');
          await waitForNextPaint();
          if (!isCurrent()) return;
          try {
            const inFlightUrl = await inFlight.promise;
            if (!isCurrent()) {
              URL.revokeObjectURL(inFlightUrl);
              return;
            }
            await playCachedUrl(playerEl, inFlightUrl, roundIndex, isCurrent);
            return;
          } catch {
            // Fall through to fresh fetch on error
          }
        }

        const oldUrl = peekUrl();
        if (oldUrl) {
          stopAudio(playerEl, oldUrl);
          clearSlot();
        }
        unlockAudio(playerEl);
        setKey(key);
        setState('loading');
        setMessage('Preparando la voz…');
        // Start the fetch synchronously so concurrent speak() calls dedupe
        // onto it (via busyRef) and autoplay observes it in the same tick;
        // the paint wait below only lets the 'loading' state flush first.
        const pendingFetch = speechApi.getSpeechBlobUrl(sessionId, language);
        await waitForNextPaint();
        if (!isCurrent()) {
          // Voice switched (or a newer run started) while preparing: drop
          // the take and release its blob so stale audio never plays.
          void pendingFetch.then(
            (staleUrl) => URL.revokeObjectURL(staleUrl),
            () => {}
          );
          return;
        }

        let url: string;
        try {
          url = await pendingFetch;
        } catch (err: unknown) {
          if (!isCurrent()) return;
          const e = err as { status?: number };
          setState('error');
          setMessage(
            e.status === 503
              ? language === 'quc'
                ? "Todavía no hay voz en k'iche'; lea la explicación en voz alta."
                : 'Este aparato no tiene voz instalada (espeak-ng).'
              : 'No se pudo preparar la voz.'
          );
          return;
        }

        if (!isCurrent()) {
          URL.revokeObjectURL(url);
          return;
        }
        store(roundIndex, key, url);
        await playCachedUrl(playerEl, url, roundIndex, isCurrent);
      } finally {
        if (activeRunRef.current === runId) busyRef.current = false;
      }
    },
    [
      sessionId,
      language,
      cacheGeneration,
      keyMatches,
      readCached,
      getInFlight,
      peekUrl,
      clearSlot,
      setKey,
      store,
      playCachedUrl,
    ]
  );

  useEffect(() => {
    return () => {
      activeRunRef.current += 1;
      busyRef.current = false;
      stopPlayer(peekUrl());
      release();
    };
    // Stable callbacks + refs only; runs once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { state, message, currentRound, speak, prefetch, stopPlayback };
}
