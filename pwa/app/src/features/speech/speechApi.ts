import { requestApi, requestBlobUrl } from '../../shared/api/httpClient';
import { storage } from '../../shared/lib/storage';
import {
  SpeechLanguage,
  TTSLoadRequest,
  TTSLoadResponse,
  TTSStatusResponse,
  TTSUnloadRequest,
  TTSUnloadResponse,
  TTSVoiceItem,
} from './speech.types';

/**
 * API client contract for speech engine lifecycle operations (load, unload, status).
 */
export const ttsApi = {
  /**
   * Checks current memory residency and active model status.
   */
  async getStatus(engine?: string, lang: SpeechLanguage = 'es'): Promise<TTSStatusResponse> {
    const params = new URLSearchParams({ lang });
    if (engine) params.set('engine', engine);
    return requestApi<TTSStatusResponse>('GET', `/tts/status?${params.toString()}`);
  },

  /**
   * Proactively preloads TTS voice weights into RAM/VRAM.
   */
  async load(payload: TTSLoadRequest = { lang: 'es' }): Promise<TTSLoadResponse> {
    return requestApi<TTSLoadResponse>('POST', '/tts/load', payload);
  },

  /**
   * Unloads TTS model weights from memory to reclaim RAM.
   */
  async unload(payload: TTSUnloadRequest = {}): Promise<TTSUnloadResponse> {
    return requestApi<TTSUnloadResponse>('POST', '/tts/unload', payload);
  },

  /**
   * Lists available voices for the specified language and optional engine.
   */
  async getVoices(lang: SpeechLanguage = 'es', engine?: string): Promise<TTSVoiceItem[]> {
    const params = new URLSearchParams({ lang });
    if (engine) params.set('engine', engine);
    return requestApi<TTSVoiceItem[]>('GET', `/tts/voices?${params.toString()}`);
  },
};

/**
 * Cache key for a round clip: language plus the saved voice selection,
 * so changing the default voice never replays a stale clip.
 */
export function getSpeechVoiceKey(language: SpeechLanguage): string {
  const pref = storage.getVoicePreference();
  if (
    pref &&
    (pref.lang || 'es') === language &&
    (pref.engine || pref.voice)
  ) {
    return `${language}::${pref.engine || ''}::${pref.voice || ''}`;
  }
  return `${language}::default`;
}

/**
 * API client contract for offline TTS speech audio stream retrieval.
 */
export const speechApi = {
  /**
   * Retrieves offline synthesized misconception WAV audio blob URL for the current round.
   * Appends the teacher's saved voice (engine/voice) when it matches the
   * language; otherwise the configured default engine speaks.
   *
   * @param {string} sessionId - Active session UUID.
   * @param {SpeechLanguage} [language='es'] - Targeted synthesis language ('es' or 'quc').
   * @returns {Promise<string>} Blob URL ready for HTMLAudioElement playback.
   */
  async getSpeechBlobUrl(sessionId: string, language: SpeechLanguage = 'es'): Promise<string> {
    const params = new URLSearchParams({ lang: language });
    const pref = storage.getVoicePreference();
    if (pref && (pref.lang || 'es') === language) {
      if (pref.engine) params.set('engine', pref.engine);
      if (pref.voice) params.set('voice', pref.voice);
    }
    return requestBlobUrl(`/session/${sessionId}/speech?${params.toString()}`);
  },

  /**
   * Synthesizes a short voice sample via `POST /tts/preview`.
   * The server auto-loads the engine and unloads it afterwards when it
   * was idle, so previews never leave weights in RAM.
   */
  async getPreviewBlobUrl(payload: {
    lang?: SpeechLanguage;
    engine?: string;
    voice?: string;
  }): Promise<string> {
    return requestBlobUrl('/tts/preview', 'POST', {
      lang: payload.lang || 'es',
      engine: payload.engine,
      voice: payload.voice,
    });
  },
};
