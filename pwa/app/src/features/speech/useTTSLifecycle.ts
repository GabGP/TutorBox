import { useCallback, useRef, useState } from 'react';
import { SpeechLanguage } from './speech.types';
import { ttsApi } from './speechApi';

export interface UseTTSLifecycleReturn {
  isLoaded: boolean;
  isLoading: boolean;
  activeEngine: string | null;
  error: string | null;
  preloadIfUnloaded: (lang?: SpeechLanguage, engine?: string, voice?: string) => Promise<boolean>;
  unloadIfLoaded: (engine?: string) => Promise<boolean>;
  checkStatus: (engine?: string, lang?: SpeechLanguage) => Promise<boolean>;
}

/**
 * Custom React hook for managing the TTS engine lifecycle (proactive load and cleanup unload).
 * Ensures memory on edge appliances (like Jetson Orin Nano) is managed conservatively.
 */
export function useTTSLifecycle(): UseTTSLifecycleReturn {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [activeEngine, setActiveEngine] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isOperatingRef = useRef(false);

  const checkStatus = useCallback(
    async (engine?: string, lang: SpeechLanguage = 'es'): Promise<boolean> => {
      try {
        const res = await ttsApi.getStatus(engine, lang);
        setIsLoaded(res.loaded);
        setActiveEngine(res.engine);
        setError(null);
        return res.loaded;
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Error checking TTS status';
        setError(message);
        return false;
      }
    },
    []
  );

  const preloadIfUnloaded = useCallback(
    async (
      lang: SpeechLanguage = 'es',
      engine?: string,
      voice?: string
    ): Promise<boolean> => {
      if (isOperatingRef.current) return isLoaded;
      isOperatingRef.current = true;
      setIsLoading(true);
      setError(null);

      try {
        const status = await ttsApi.getStatus(engine, lang);
        if (status.loaded) {
          setIsLoaded(true);
          setActiveEngine(status.engine);
          return true;
        }

        const res = await ttsApi.load({ lang, engine, voice });
        setIsLoaded(res.loaded);
        setActiveEngine(res.engine);
        return res.loaded;
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to preload TTS engine';
        setError(message);
        return false;
      } finally {
        setIsLoading(false);
        isOperatingRef.current = false;
      }
    },
    [isLoaded]
  );

  const unloadIfLoaded = useCallback(
    async (engine?: string): Promise<boolean> => {
      if (isOperatingRef.current) return !isLoaded;
      isOperatingRef.current = true;
      setIsLoading(true);
      setError(null);

      try {
        const status = await ttsApi.getStatus(engine);
        if (!status.loaded) {
          setIsLoaded(false);
          setActiveEngine(status.engine);
          return true;
        }

        const res = await ttsApi.unload({ engine });
        setIsLoaded(res.loaded);
        setActiveEngine(res.engine);
        return !res.loaded;
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to unload TTS engine';
        setError(message);
        return false;
      } finally {
        setIsLoading(false);
        isOperatingRef.current = false;
      }
    },
    [isLoaded]
  );

  return {
    isLoaded,
    isLoading,
    activeEngine,
    error,
    preloadIfUnloaded,
    unloadIfLoaded,
    checkStatus,
  };
}
