import { useCallback, useEffect, useRef, useState } from 'react';
import { getAudioPlayer, stopAudio, unlockAudio } from '../../shared/lib/sound';
import { SpeechLanguage, SpeechState } from './speech.types';
import { speechApi } from './speechApi';

export interface UseSpeechPlaybackReturn {
  state: SpeechState;
  message: string;
  currentRound: number;
  speak: (roundIndex: number) => Promise<void>;
  prefetch: (roundIndex: number) => Promise<void>;
  stopPlayback: () => void;
}

type InFlight = { roundIndex: number; lang: SpeechLanguage; promise: Promise<string> };

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

  const clipUrlRef = useRef<string | null>(null);
  const cachedRoundRef = useRef<number>(-1);
  const cachedLangRef = useRef<SpeechLanguage>(language);
  const inFlightRef = useRef<InFlight | null>(null);

  const stopPlayback = useCallback(() => {
    stopAudio(getAudioPlayer());
    if (state === 'playing' || state === 'loading') {
      setState('idle');
      setMessage('');
    }
  }, [state]);

  const prefetch = useCallback(async (roundIndex: number) => {
    if (!sessionId) return;
    if (cachedRoundRef.current === roundIndex && cachedLangRef.current === language && clipUrlRef.current) return;
    if (inFlightRef.current?.roundIndex === roundIndex && inFlightRef.current?.lang === language) return;

    console.info(`[Speech] Prefetch started for round ${roundIndex} (${language})`);
    const fetchPromise = speechApi.getSpeechBlobUrl(sessionId, language);
    inFlightRef.current = { roundIndex, lang: language, promise: fetchPromise };
    try {
      const url = await fetchPromise;
      if (cachedLangRef.current === language) {
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
    if (!sessionId || state === 'loading') return;
    if (state === 'playing' && currentRound === roundIndex && cachedLangRef.current === language) return;

    const player = getAudioPlayer();
    if (cachedRoundRef.current === roundIndex && cachedLangRef.current === language && clipUrlRef.current) {
      await playCachedUrl(player, clipUrlRef.current, roundIndex);
      return;
    }

    if (inFlightRef.current?.roundIndex === roundIndex && inFlightRef.current?.lang === language) {
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
    cachedLangRef.current = language;
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
  }, [sessionId, language, state, currentRound, playCachedUrl]);

  useEffect(() => {
    return () => {
      stopAudio(getAudioPlayer(), clipUrlRef.current);
      clipUrlRef.current = null;
    };
  }, []);

  return { state, message, currentRound, speak, prefetch, stopPlayback };
}
