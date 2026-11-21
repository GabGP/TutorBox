import { useCallback, useMemo, useRef } from 'react';
import { formatSecondsEs } from '../../shared/lib/format';
import { storage } from '../../shared/lib/storage';
import type { NoticeSink } from '../model-residency/residencyNotices';
import { SpeechLanguage } from './speech.types';
import { ttsApi } from './speechApi';

/** Names the teacher sees for the backend's engine ids (core/tts/engines/<name>). */
const ENGINE_NAMES: Record<string, string> = {
  'qwen3-tts': 'Qwen3-TTS',
  piper: 'Piper',
  sherpa: 'Sherpa',
  kokoro: 'Kokoro',
  espeak: 'eSpeak',
  mms: 'MMS',
};

/** "la voz Qwen3-TTS", or "la voz" when the engine is not known yet. */
export function voiceName(engine?: string | null): string {
  if (!engine) return 'la voz';
  return `la voz ${ENGINE_NAMES[engine] ?? engine}`;
}

function capitalized(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export const VOICE_LOAD_FAILED =
  'No se pudo cargar la voz. El juego sigue: la explicación también aparece por escrito.';
export const VOICE_UNLOADED = 'Voz descargada de la memoria';
export const VOICE_UNLOAD_FAILED = 'No se pudo descargar la voz de la memoria.';

export interface LobbyVoice {
  /** Loads the class voice for a game that has just started; never throws. */
  prepare: (voiceLang: SpeechLanguage) => Promise<void>;
  /** Unloads the voice when the game ends or is dropped; never throws. */
  release: () => Promise<void>;
}

/**
 * The class voice around one game. A game no longer waits for its voice: Qwen3-TTS can take
 * several seconds to load, and the first explanation is spoken a whole round later. The voice
 * loads in the background with a sticky toast, then reports how long it took or that it failed.
 *
 * Single-resident policy: the backend's /tts/load evicts every other engine first. The engine is
 * the teacher's saved voice for this language, or the backend's default when none is saved.
 *
 * @param {NoticeSink} notices - Toast queue for the loading and result messages.
 * @returns {LobbyVoice} Stable `prepare` and `release` callbacks.
 */
export function useLobbyVoice({ pushToast, dismissToast }: NoticeSink): LobbyVoice {
  const loadedEngineRef = useRef<string | null>(null);
  const languageRef = useRef<SpeechLanguage>('es');
  const releasingRef = useRef(false);

  const prepare = useCallback(
    async (voiceLang: SpeechLanguage) => {
      languageRef.current = voiceLang;
      const saved = storage.getVoicePreference();
      const preference = saved?.lang === voiceLang ? saved : undefined;
      const status = await ttsApi.getStatus(preference?.engine, voiceLang).catch(() => null);
      if (status?.loaded) {
        loadedEngineRef.current = status.engine;
        return;
      }
      const engineShown = preference?.engine ?? status?.engine;
      const loadingToast = pushToast({ message: `Cargando ${voiceName(engineShown)}…`, duration: 0 });
      try {
        const loaded = await ttsApi.load({ lang: voiceLang, engine: preference?.engine, voice: preference?.voice });
        if (!loaded.loaded) throw new Error('The voice did not load.');
        loadedEngineRef.current = loaded.engine;
        const seconds = formatSecondsEs(loaded.load_ms);
        pushToast({ message: `${capitalized(voiceName(loaded.engine))} está lista (${seconds} s)`, tone: 'success' });
      } catch {
        pushToast({ message: VOICE_LOAD_FAILED, tone: 'warn' });
      } finally {
        dismissToast(loadingToast);
      }
    },
    [pushToast, dismissToast]
  );

  const release = useCallback(async () => {
    if (releasingRef.current) return;
    releasingRef.current = true;
    try {
      // The engine the game loaded; the speech endpoint may also have loaded one on demand.
      const engine = loadedEngineRef.current ?? undefined;
      const status = await ttsApi.getStatus(engine, languageRef.current);
      if (!status.loaded) return;
      await ttsApi.unload({});
      loadedEngineRef.current = null;
      pushToast({ message: VOICE_UNLOADED, tone: 'success' });
    } catch {
      pushToast({ message: VOICE_UNLOAD_FAILED, tone: 'warn' });
    } finally {
      releasingRef.current = false;
    }
  }, [pushToast]);

  return useMemo(() => ({ prepare, release }), [prepare, release]);
}
