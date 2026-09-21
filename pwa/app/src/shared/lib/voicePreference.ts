import { storage } from './storage';
import type { SpeechLanguage } from '../../features/speech/speech.types';

/**
 * Cache key for a round clip: language plus the saved voice selection,
 * so changing the default voice never replays a stale clip.
 * Moved here from speechApi so non-API layers can share it without
 * pulling the HTTP client.
 */
export function getSpeechVoiceKey(language: SpeechLanguage): string {
  const pref = storage.getVoicePreference();
  if (pref && (pref.lang || 'es') === language && (pref.engine || pref.voice)) {
    return `${language}::${pref.engine || ''}::${pref.voice || ''}`;
  }
  return `${language}::default`;
}
