import { describe, expect, it } from 'vitest';
import {
  SPEECH_LANGUAGES,
  SPEECH_LANGUAGE_NAMES,
  isMayanLanguage,
  toSpeechLanguage,
} from '../speechLanguages';

describe('speechLanguages', () => {
  it('lists Spanish and both Mayan languages, each with a name', () => {
    expect(SPEECH_LANGUAGES).toEqual(['es', 'quc', 'kek']);
    expect(SPEECH_LANGUAGE_NAMES).toEqual({ es: 'español', quc: "k'iche'", kek: "q'eqchi'" });
  });

  it('keeps a known stored language and falls back to Spanish otherwise', () => {
    expect(toSpeechLanguage('kek')).toBe('kek');
    expect(toSpeechLanguage('quc')).toBe('quc');
    expect(toSpeechLanguage('fr')).toBe('es');
    expect(toSpeechLanguage(undefined)).toBe('es');
  });

  it('marks only the Mayan languages as Mayan', () => {
    expect(isMayanLanguage('es')).toBe(false);
    expect(isMayanLanguage('quc')).toBe(true);
    expect(isMayanLanguage('kek')).toBe(true);
  });
});
