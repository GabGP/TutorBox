import { requestApi, requestBlobUrl } from '../../shared/api/httpClient';
import { toQuery } from '../../shared/api/query';
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
    return requestApi<TTSStatusResponse>(
      'GET',
      `/tts/status${toQuery({ lang, engine })}`
    );
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
    return requestApi<TTSVoiceItem[]>('GET', `/tts/voices${toQuery({ lang, engine })}`);
  },
};

export { getSpeechVoiceKey } from '../../shared/lib/voicePreference';

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
    const pref = storage.getVoicePreference();
    const suffix = toQuery({
      lang: language,
      engine: pref && (pref.lang || 'es') === language ? pref.engine : undefined,
      voice: pref && (pref.lang || 'es') === language ? pref.voice : undefined,
    });
    return requestBlobUrl(`/session/${sessionId}/speech${suffix}`);
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
