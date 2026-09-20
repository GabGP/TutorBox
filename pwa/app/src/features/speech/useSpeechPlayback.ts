import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { getAudioPlayer, stopAudio, unlockAudio } from '../../shared/lib/sound';
import { SpeechLanguage, SpeechState } from './speech.types';
import { getSpeechVoiceKey, speechApi } from './speechApi';

export interface UseSpeechPlaybackReturn {
  state: SpeechState;
  message: string;
  currentRound: number;
  speak: (roundIndex: number) => Promise<void>;
  prefetch: (roundIndex: number) => Promise<void>;
  stopPlayback: () => void;
}

type InFlight = { roundIndex: number; key: string; promise: Promise<string>; generation: number };

function waitForNextPaint(): Promise<void> {
  if (typeof requestAnimationFrame === 'function') {
    return new Promise((resolve) => requestAnimationFrame(() => resolve()));
  }
  return new Promise((resolve) => setTimeout(resolve, 0));
}

/**
 * Custom React hook for controlling offline speech synthesis playback and speculative prefetching.
 * Pre-fetches WAV blobs on round close, manages audio playback, and bypasses mobile autoplay blocks.
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

  const clipUrlRef = useRef<string | null>(null);
  const cachedRoundRef = useRef<number>(-1);
  const cachedKeyRef = useRef<string>(activeVoiceKey);
  const inFlightRef = useRef<InFlight | null>(null);
  const voiceGenerationRef = useRef(0);
  const activeRunRef = useRef(0);
  const playbackTokenRef = useRef(0);
  // Tracks an in-progress run independently of rendered state, so a tap
  // can never be swallowed by a stale `loading` closure nor start a
  // duplicate fetch. Always released in `finally`.
  const busyRef = useRef(false);

  // Reset cached clip and preparation state when the saved voice changes.
  // This must run before child reveal effects can autoplay after Settings
  // closes; a passive effect lets autoplay race the old clip and skip the
  // preparation state.
  useLayoutEffect(() => {
    if (prevVoiceKey !== activeVoiceKey) {
      voiceGenerationRef.current += 1;
      activeRunRef.current += 1;
      playbackTokenRef.current += 1;
      busyRef.current = false;
      setPrevVoiceKey(activeVoiceKey);
      setState('idle');
      setMessage('');
      const player = getAudioPlayer();
      if (player) {
        player.onended = null;
        player.onerror = null;
        stopAudio(player, clipUrlRef.current);
      }
      if (clipUrlRef.current) {
        clipUrlRef.current = null;
      }
      cachedRoundRef.current = -1;
      cachedKeyRef.current = activeVoiceKey;
      inFlightRef.current = null;
    }
  }, [activeVoiceKey, prevVoiceKey]);

  const stopPlayback = useCallback(() => {
    activeRunRef.current += 1;
    playbackTokenRef.current += 1;
    busyRef.current = false;
    const player = getAudioPlayer();
    if (player) {
      player.onended = null;
      player.onerror = null;
      stopAudio(player);
    }
    if (state === 'playing' || state === 'loading') {
      setState('idle');
      setMessage('');
    }
  }, [state]);

  const prefetch = useCallback(async (roundIndex: number) => {
    if (!sessionId) return;
    const key = getSpeechVoiceKey(language);
    const generation = voiceGenerationRef.current;
    if (cachedRoundRef.current === roundIndex && cachedKeyRef.current === key && clipUrlRef.current) return;
    if (inFlightRef.current?.roundIndex === roundIndex && inFlightRef.current?.key === key) return;

    console.info(`[Speech] Prefetch started for round ${roundIndex} (${language})`);
    const fetchPromise = speechApi.getSpeechBlobUrl(sessionId, language);
    inFlightRef.current = { roundIndex, key, promise: fetchPromise, generation };
    try {
      const url = await fetchPromise;
      if (voiceGenerationRef.current === generation && cachedKeyRef.current === key) {
        if (clipUrlRef.current && clipUrlRef.current !== url) URL.revokeObjectURL(clipUrlRef.current);
        clipUrlRef.current = url;
        cachedRoundRef.current = roundIndex;
        console.info(`[Speech] Prefetch ready for round ${roundIndex}`);
      } else {
        URL.revokeObjectURL(url);
      }
    } catch {
      console.info(`[Speech] Prefetch skipped for round ${roundIndex} (>51% rule not met)`);
    } finally {
      if (inFlightRef.current?.promise === fetchPromise) inFlightRef.current = null;
    }
  }, [sessionId, language]);

  const playCachedUrl = useCallback(async (
    player: HTMLAudioElement,
    url: string,
    roundIndex: number,
    generation: number,
  ) => {
    const playbackToken = ++playbackTokenRef.current;
    const isCurrent = () =>
      voiceGenerationRef.current === generation && playbackTokenRef.current === playbackToken;
    if (!isCurrent()) return;

    player.pause();
    player.src = url;
    player.currentTime = 0;
    player.onended = () => {
      if (!isCurrent()) return;
      console.info(`[Speech] Playback finished for round ${roundIndex}`);
      setState('done');
      setMessage('Explicación leída.');
    };
    player.onerror = () => {
      if (!isCurrent()) return;
      setState('error');
      setMessage('No se pudo reproducir el audio.');
    };
    setCurrentRound(roundIndex);
    setState('playing');
    setMessage('Leyendo la explicación en voz alta…');
    console.info(`[Speech] Playback started for round ${roundIndex}`);
    try {
      await player.play();
    } catch {
      if (isCurrent()) {
        setState('blocked');
        setMessage('Toque “Escuchar” para reproducir la explicación.');
      }
    }
  }, []);

  const speak = useCallback(async (roundIndex: number) => {
    if (!sessionId) return;
    const key = getSpeechVoiceKey(language);
    if (busyRef.current) return;
    if (state === 'playing' && currentRound === roundIndex && cachedKeyRef.current === key) return;
    busyRef.current = true;
    const generation = voiceGenerationRef.current;
    const runId = ++activeRunRef.current;
    const isCurrent = () =>
      voiceGenerationRef.current === generation && activeRunRef.current === runId;
    try {
      const player = getAudioPlayer();
      if (!player) return;
      if (cachedRoundRef.current === roundIndex && cachedKeyRef.current === key && clipUrlRef.current) {
        await playCachedUrl(player, clipUrlRef.current, roundIndex, generation);
        return;
      }

      const inFlight = inFlightRef.current;
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
          await playCachedUrl(player, inFlightUrl, roundIndex, generation);
          return;
        } catch { /* Fall through to fresh fetch on error */ }
      }

      if (clipUrlRef.current) {
        stopAudio(player, clipUrlRef.current);
        clipUrlRef.current = null;
        cachedRoundRef.current = -1;
      }
      unlockAudio(player);
      cachedKeyRef.current = key;
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
            ? language === 'quc' ? "Todavía no hay voz en k'iche'; lea la explicación en voz alta." : 'Este aparato no tiene voz instalada (espeak-ng).'
            : 'No se pudo preparar la voz.'
        );
        return;
      }

      if (!isCurrent()) {
        URL.revokeObjectURL(url);
        return;
      }
      clipUrlRef.current = url;
      cachedRoundRef.current = roundIndex;
      await playCachedUrl(player, url, roundIndex, generation);
    } finally {
      if (activeRunRef.current === runId) busyRef.current = false;
    }
  }, [sessionId, language, state, currentRound, playCachedUrl]);

  useEffect(() => {
    return () => {
      activeRunRef.current += 1;
      playbackTokenRef.current += 1;
      busyRef.current = false;
      const player = getAudioPlayer();
      if (player) {
        player.onended = null;
        player.onerror = null;
        stopAudio(player, clipUrlRef.current);
      }
      clipUrlRef.current = null;
    };
  }, []);

  return { state, message, currentRound, speak, prefetch, stopPlayback };
}
