import { useCallback, useRef } from 'react';
import { getSpeechVoiceKey, speechApi } from './speechApi';
import type { SpeechLanguage } from './speech.types';

export interface InFlightFetch {
  roundIndex: number;
  key: string;
  promise: Promise<string>;
  generation: number;
}

/**
 * Voice-keyed blob cache behind speech playback. Owns the prefetched clip URL,
 * its round/voice identity, in-flight fetch deduping, and the voice-generation
 * counter — all as refs, no React state. The orchestrating hook owns playback
 * state and the audio element.
 */
export function useVoiceCache(sessionId: string | null, language: SpeechLanguage) {
  const clipUrlRef = useRef<string | null>(null);
  const cachedRoundRef = useRef(-1);
  const cachedKeyRef = useRef(getSpeechVoiceKey(language));
  const inFlightRef = useRef<InFlightFetch | null>(null);
  const voiceGenerationRef = useRef(0);

  const generation = useCallback(() => voiceGenerationRef.current, []);
  const bumpGeneration = useCallback(() => {
    voiceGenerationRef.current += 1;
  }, []);

  const keyMatches = useCallback(
    (key: string) => cachedKeyRef.current === key,
    []
  );
  const setKey = useCallback((key: string) => {
    cachedKeyRef.current = key;
  }, []);

  const peekUrl = useCallback(() => clipUrlRef.current, []);

  const readCached = useCallback((roundIndex: number, key: string): string | null => {
    if (
      cachedRoundRef.current === roundIndex &&
      cachedKeyRef.current === key &&
      clipUrlRef.current
    ) {
      return clipUrlRef.current;
    }
    return null;
  }, []);

  const store = useCallback((roundIndex: number, key: string, url: string) => {
    if (clipUrlRef.current && clipUrlRef.current !== url) {
      URL.revokeObjectURL(clipUrlRef.current);
    }
    clipUrlRef.current = url;
    cachedRoundRef.current = roundIndex;
    cachedKeyRef.current = key;
  }, []);

  /** Forgets the slot after the caller revoked the URL via stopAudio. */
  const clearSlot = useCallback(() => {
    clipUrlRef.current = null;
    cachedRoundRef.current = -1;
  }, []);

  /** Drops cache identity on voice change (URL already revoked by the player). */
  const drop = useCallback(() => {
    clipUrlRef.current = null;
    cachedRoundRef.current = -1;
    inFlightRef.current = null;
  }, []);

  /** Revokes and forgets the clip (unmount). Revoking twice is a harmless no-op. */
  const release = useCallback(() => {
    const url = clipUrlRef.current;
    clipUrlRef.current = null;
    cachedRoundRef.current = -1;
    if (url && url.startsWith('blob:')) {
      try {
        URL.revokeObjectURL(url);
      } catch {
        // Ignore revoke errors
      }
    }
  }, []);

  const getInFlight = useCallback((): InFlightFetch | null => inFlightRef.current, []);
  const clearInFlight = useCallback(() => {
    inFlightRef.current = null;
  }, []);

  const prefetch = useCallback(
    async (roundIndex: number) => {
      if (!sessionId) return;
      const key = getSpeechVoiceKey(language);
      const fetchGeneration = voiceGenerationRef.current;
      if (readCached(roundIndex, key)) return;
      if (
        inFlightRef.current?.roundIndex === roundIndex &&
        inFlightRef.current?.key === key
      ) {
        return;
      }

      const fetchPromise = speechApi.getSpeechBlobUrl(sessionId, language);
      inFlightRef.current = { roundIndex, key, promise: fetchPromise, generation: fetchGeneration };
      try {
        const url = await fetchPromise;
        if (voiceGenerationRef.current === fetchGeneration && cachedKeyRef.current === key) {
          store(roundIndex, key, url);
        } else {
          URL.revokeObjectURL(url);
        }
      } catch {
        // No clip for this round (e.g. >51% rule not met): speak() falls
        // back to a fresh fetch.
      } finally {
        if (inFlightRef.current?.promise === fetchPromise) inFlightRef.current = null;
      }
    },
    [sessionId, language, readCached, store]
  );

  return {
    generation,
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
    prefetch,
  };
}

export type VoiceCache = ReturnType<typeof useVoiceCache>;
