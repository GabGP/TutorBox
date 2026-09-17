import { useCallback, useEffect, useRef, useState } from 'react';
import { getAudioPlayer, stopAudio, unlockAudio } from '../../shared/lib/sound';
import { SpeechLanguage, SpeechState } from './speech.types';
import { speechApi } from './speechApi';

/**
 * Custom React hook for controlling offline speech synthesis playback.
 * Fetches synthesized WAV audio blobs (`/session/{id}/speech`), manages HTMLAudioElement
 * playback state, handles autoplay policies, and caches audio blobs for instantaneous replay.
 *
 * @param {string | null} sessionId - Target session ID for speech synthesis retrieval.
 * @param {SpeechLanguage} [language='es'] - Targeted synthesis language ('es' Spanish or 'quc' K'iche').
 * @returns {object} Speech playback state, user message, speak trigger, and stop method.
 */
export function useSpeechPlayback(sessionId: string | null, language: SpeechLanguage = 'es') {
  const [state, setState] = useState<SpeechState>('idle');
  const [message, setMessage] = useState('');
  const [currentRound, setCurrentRound] = useState<number>(-1);

  const clipUrlRef = useRef<string | null>(null);
  const activeRoundRef = useRef<number>(-1);
  const cachedLangRef = useRef<SpeechLanguage>(language);

  const stopPlayback = useCallback(() => {
    const player = getAudioPlayer();
    stopAudio(player);
    if (state === 'playing' || state === 'loading') {
      setState('idle');
      setMessage('');
    }
  }, [state]);

  const speak = useCallback(
    async (roundIndex: number) => {
      if (!sessionId) return;
      if (
        state === 'loading' ||
        (state === 'playing' && activeRoundRef.current === roundIndex && cachedLangRef.current === language)
      ) {
        return;
      }

      const player = getAudioPlayer();

      // If audio was already synthesized for this round and language, play immediately (synchronous in click event)
      if (
        activeRoundRef.current === roundIndex &&
        cachedLangRef.current === language &&
        clipUrlRef.current
      ) {
        player.pause();
        player.src = clipUrlRef.current;
        player.currentTime = 0;

        player.onended = () => {
          if (activeRoundRef.current === roundIndex) {
            setState('done');
            setMessage('Explicación leída.');
          }
        };

        player.onerror = () => {
          if (activeRoundRef.current === roundIndex) {
            setState('error');
            setMessage('No se pudo reproducir el audio.');
          }
        };

        setState('playing');
        setMessage('Leyendo la explicación en voz alta…');

        try {
          await player.play();
        } catch {
          setState('blocked');
          setMessage('Toque “Escuchar” para reproducir la explicación.');
        }
        return;
      }

      // Purge prior blob if changing round or language
      if (clipUrlRef.current) {
        stopAudio(player, clipUrlRef.current);
        clipUrlRef.current = null;
      }

      // Unlock audio synchronously inside active gesture
      unlockAudio(player);

      activeRoundRef.current = roundIndex;
      cachedLangRef.current = language;
      setCurrentRound(roundIndex);
      setState('loading');
      setMessage('Preparando la voz…');

      let url: string;
      try {
        url = await speechApi.getSpeechBlobUrl(sessionId, language);
      } catch (err: unknown) {
        const e = err as { status?: number };
        setState('error');
        if (e.status === 503) {
          setMessage(
            language === 'quc'
              ? "Todavía no hay voz en k'iche'; lea la explicación en voz alta."
              : 'Este aparato no tiene voz instalada (espeak-ng).'
          );
        } else {
          setMessage('No se pudo preparar la voz.');
        }
        return;
      }

      // If user moved to another round before download finished, discard URL
      if (activeRoundRef.current !== roundIndex || cachedLangRef.current !== language) {
        URL.revokeObjectURL(url);
        return;
      }

      clipUrlRef.current = url;
      player.src = url;

      player.onended = () => {
        if (activeRoundRef.current === roundIndex) {
          setState('done');
          setMessage('Explicación leída.');
        }
      };

      player.onerror = () => {
        if (activeRoundRef.current === roundIndex) {
          setState('error');
          setMessage('No se pudo reproducir el audio.');
        }
      };

      setState('playing');
      setMessage('Leyendo la explicación en voz alta…');

      try {
        await player.play();
      } catch {
        setState('blocked');
        setMessage('Toque “Escuchar” para reproducir la explicación.');
      }
    },
    [sessionId, language, state]
  );

  useEffect(() => {
    return () => {
      const player = getAudioPlayer();
      stopAudio(player, clipUrlRef.current);
      clipUrlRef.current = null;
    };
  }, []);

  return {
    state,
    message,
    currentRound,
    speak,
    stopPlayback,
  };
}
