import { requestBlobUrl } from '../../shared/api/httpClient';
import { SpeechLanguage } from './speech.types';

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
