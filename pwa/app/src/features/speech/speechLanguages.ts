import { SpeechLanguage } from "./speech.types";

/** Languages the box can speak: Spanish and the Mayan languages with an MMS voice. */
export const SPEECH_LANGUAGES: readonly SpeechLanguage[] = ["es", "quc", "kek"];

/** Display names, lower case so they read inside a sentence ("Escuchar en …"). */
export const SPEECH_LANGUAGE_NAMES: Record<SpeechLanguage, string> = {
  es: "español",
  quc: "k'iche'",
  kek: "q'eqchi'",
};

/** A stored or received language code, or Spanish when it is not one we speak. */
export function toSpeechLanguage(value: unknown): SpeechLanguage {
  return SPEECH_LANGUAGES.includes(value as SpeechLanguage)
    ? (value as SpeechLanguage)
    : "es";
}

/** Mayan voices read the Spanish explanation until translated explanations exist. */
export function isMayanLanguage(language: SpeechLanguage): boolean {
  return language !== "es";
}
