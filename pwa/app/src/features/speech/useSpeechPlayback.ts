import { useCallback, useEffect, useRef, useState } from 'react';
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

type InFlight = { roundIndex: number; key: string; promise: Promise<string> };

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
  // Tracks an in-progress run independently of rendered state, so a tap
  // can never be swallowed by a stale `loading` closure nor start a
  // duplicate fetch. Always released in `finally`.
  const busyRef = useRef(false);

  // Reset cached clip and preparation state when the saved voice changes.
  // Runs as an effect (not during render) so blob revocation and audio
  // stopping never race with an in-flight `speak` render.
  useEffect(() => {
    if (prevVoiceKey !== activeVoiceKey) {
      setPrevVoiceKey(activeVoiceKey);
      setState('idle');
      setMessage('');
      if (clipUrlRef.current) {
        stopAudio(getAudioPlayer(), clipUrlRef.current);
        clipUrlRef.current = null;
      }
      cachedRoundRef.current = -1;
      cachedKeyRef.current = activeVoiceKey;
      inFlightRef.current = null;
    }
  }, [activeVoiceKey, prevVoiceKey]);

  const stopPlayback = useCallback(() => {
    stopAudio(getAudioPlayer());
    if (state === 'playing' || state === 'loading') {
      setState('idle');
      setMessage('');
    }
  }, [state]);

  const prefetch = useCallback(async (roundIndex: number) => {
    if (!sessionId) return;
    const key = getSpeechVoiceKey(language);
    if (cachedRoundRef.current === roundIndex && cachedKeyRef.current === key && clipUrlRef.current) return;
    if (inFlightRef.current?.roundIndex === roundIndex && inFlightRef.current?.key === key) return;

    console.info(`[Speech] Prefetch started for round ${roundIndex} (${language})`);
    const fetchPromise = speechApi.getSpeechBlobUrl(sessionId, language);
    inFlightRef.current = { roundIndex, key, promise: fetchPromise };
    try {
      const url = await fetchPromise;
      if (cachedKeyRef.current === key) {
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
      if (inFlightRef.current?.roundIndex === roundIndex) inFlightRef.current = null;
    }
  }, [sessionId, language]);

  const playCachedUrl = useCallback(async (player: HTMLAudioElement, url: string, roundIndex: number) => {
    player.pause();
    player.src = url;
    player.currentTime = 0;
    player.onended = () => (console.info(`[Speech] Playback finished for round ${roundIndex}`), setState('done'), setMessage('Explicación leída.'));
    player.onerror = () => (setState('error'), setMessage('No se pudo reproducir el audio.'));
    setCurrentRound(roundIndex);
    setState('playing');
    setMessage('Leyendo la explicación en voz alta…');
    console.info(`[Speech] Playback started for round ${roundIndex}`);
    try {
      await player.play();
    } catch {
      setState('blocked');
      setMessage('Toque “Escuchar” para reproducir la explicación.');
    }
  }, []);

  const speak = useCallback(async (roundIndex: number) => {
    if (!sessionId) return;
    const key = getSpeechVoiceKey(language);
    if (busyRef.current) return;
    if (state === 'playing' && currentRound === roundIndex && cachedKeyRef.current === key) return;
    busyRef.current = true;
    try {
      const player = getAudioPlayer();
      if (cachedRoundRef.current === roundIndex && cachedKeyRef.current === key && clipUrlRef.current) {
        await playCachedUrl(player, clipUrlRef.current, roundIndex);
        return;
      }

      if (inFlightRef.current?.roundIndex === roundIndex && inFlightRef.current?.key === key) {
        setState('loading');
        setMessage('Preparando la voz…');
        try {
          const inFlightUrl = await inFlightRef.current.promise;
          await playCachedUrl(player, inFlightUrl, roundIndex);
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

      let url: string;
      try {
        url = await speechApi.getSpeechBlobUrl(sessionId, language);
      } catch (err: unknown) {
        const e = err as { status?: number };
        setState('error');
        setMessage(
          e.status === 503
            ? language === 'quc' ? "Todavía no hay voz en k'iche'; lea la explicación en voz alta." : 'Este aparato no tiene voz instalada (espeak-ng).'
            : 'No se pudo preparar la voz.'
        );
        return;
      }

      clipUrlRef.current = url;
      cachedRoundRef.current = roundIndex;
      await playCachedUrl(player, url, roundIndex);
    } finally {
      busyRef.current = false;
    }
  }, [sessionId, language, state, currentRound, playCachedUrl]);

  useEffect(() => {
    return () => {
      stopAudio(getAudioPlayer(), clipUrlRef.current);
      clipUrlRef.current = null;
    };
  }, []);

  return { state, message, currentRound, speak, prefetch, stopPlayback };
}
