import { requestApi, requestBlobUrl } from '../../shared/api/httpClient';
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
 * API client contract for offline TTS speech audio stream retrieval.
 */
export const speechApi = {
  /**
   * Retrieves offline synthesized misconception WAV audio blob URL for the current round.
   *
   * @param {string} sessionId - Active session UUID.
   * @param {SpeechLanguage} [language='es'] - Targeted synthesis language ('es' or 'quc').
   * @returns {Promise<string>} Blob URL ready for HTMLAudioElement playback.
   */
  async getSpeechBlobUrl(sessionId: string, language: SpeechLanguage = 'es'): Promise<string> {
    return requestBlobUrl(`/session/${sessionId}/speech?lang=${language}`);
  },
};
