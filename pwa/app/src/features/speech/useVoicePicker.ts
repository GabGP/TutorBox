import { useCallback, useEffect, useRef, useState } from 'react';
import { toErrorMessage } from '../../shared/lib/errors';
import { storage } from '../../shared/lib/storage';
import { useToastQueue } from '../../shared/ui/Toast/useToastQueue';
import { speechApi, ttsApi } from './speechApi';
import type { SpeechLanguage, TTSStatusResponse, TTSVoiceItem } from './speech.types';

export type PreviewPhase = 'idle' | 'loading' | 'playing';

/** Option values are engine-qualified: two engines may share a voice id. */
export function optionKey(v: TTSVoiceItem): string {
  return `${v.engine}::${v.id}`;
}

export function parseKey(key: string): { engine?: string; voice?: string } {
  const sep = key.indexOf('::');
  if (sep < 0) return { voice: key || undefined };
  return { engine: key.slice(0, sep) || undefined, voice: key.slice(sep + 2) || undefined };
}

/**
 * State behind VoicePicker: language + voice selection, saved-default
 * persistence, short preview playback, and admin load/unload memory ops.
 * Confirmations and failures both float as toasts so the picker never
 * shifts layout.
 */
export function useVoicePicker() {
  const [lang, setLang] = useState<SpeechLanguage>(() => {
    const pref = storage.getVoicePreference();
    return pref?.lang === 'quc' ? 'quc' : 'es';
  });
  const [voices, setVoices] = useState<TTSVoiceItem[]>([]);
  const [voiceKey, setVoiceKey] = useState(() => {
    const pref = storage.getVoicePreference();
    return pref?.voice ? `${pref.engine || ''}::${pref.voice}` : '';
  });
  const [savedKey, setSavedKey] = useState(() => {
    const pref = storage.getVoicePreference();
    return pref?.voice ? `${pref.engine || ''}::${pref.voice}` : '';
  });
  const [status, setStatus] = useState<TTSStatusResponse | null>(null);
  const { toasts, pushToast, dismissToast } = useToastQueue();
  const [busy, setBusy] = useState(false);
  const [previewPhase, setPreviewPhase] = useState<PreviewPhase>('idle');
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const refresh = useCallback(async (l: SpeechLanguage) => {
    try {
      const [v, s] = await Promise.all([
        ttsApi.getVoices(l),
        ttsApi.getStatus(undefined, l).catch(() => null),
      ]);
      // Default first: voices of the currently loaded engine lead the list.
      const ordered =
        s?.loaded
          ? [...v.filter((x) => x.engine === s.engine), ...v.filter((x) => x.engine !== s.engine)]
          : v;
      setVoices(ordered);
      setStatus(s);
      setVoiceKey((prev) =>
        prev && ordered.some((x) => optionKey(x) === prev)
          ? prev
          : ordered[0]
            ? optionKey(ordered[0])
            : ''
      );
    } catch (err: unknown) {
      pushToast({ message: toErrorMessage(err, 'Error al cargar voces'), tone: 'error' });
    }
  }, [pushToast]);

  useEffect(() => {
    refresh(lang);
  }, [lang, refresh]);

  useEffect(() => {
    const audio = audioRef.current;
    return () => {
      audio?.pause();
      audioRef.current = null;
    };
  }, []);

  const { engine: engineOf, voice } = parseKey(voiceKey);

  const isSavedSelection = voiceKey !== '' && voiceKey === savedKey;

  const handleSaveDefault = async () => {
    if (!voice) return;
    setBusy(true);
    setStatus(null);
    try {
      storage.setVoicePreference({ lang, engine: engineOf, voice });
      setSavedKey(voiceKey);
      await ttsApi.unload({}).catch(() => null);
      const s = await ttsApi.getStatus(undefined, lang).catch(() => null);
      setStatus(s);
      pushToast({ message: 'Voz guardada como predeterminada para el juego.' });
    } catch (err: unknown) {
      pushToast({ message: toErrorMessage(err, 'Error al guardar la voz'), tone: 'error' });
    } finally {
      setBusy(false);
    }
  };

  const stopPreview = useCallback(() => {
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      const src = audio.src;
      if (src.startsWith('blob:')) URL.revokeObjectURL(src);
      audioRef.current = null;
    }
    setPreviewPhase('idle');
  }, []);

  const handlePreview = async () => {
    if (previewPhase === 'playing') {
      stopPreview();
      return;
    }
    if (previewPhase !== 'idle' || !voice) return;
    setPreviewPhase('loading');
    try {
      const url = await speechApi.getPreviewBlobUrl({
        lang,
        engine: engineOf,
        voice,
      });
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => {
        URL.revokeObjectURL(url);
        if (audioRef.current === audio) audioRef.current = null;
        setPreviewPhase('idle');
      };
      audio.onerror = () => {
        URL.revokeObjectURL(url);
        setPreviewPhase('idle');
        pushToast({ message: 'No se pudo reproducir la muestra', tone: 'error' });
      };
      await audio.play();
      setPreviewPhase('playing');
    } catch (err: unknown) {
      setPreviewPhase('idle');
      pushToast({ message: toErrorMessage(err, 'Error al generar muestra'), tone: 'error' });
    }
  };

  const handleLoad = async () => {
    setBusy(true);
    // Clear stale status first: the server evicts other resident engines
    // on load, so the previous "Motor" line must not linger as if current.
    setStatus(null);
    try {
      const res = await ttsApi.load({ lang, engine: engineOf, voice: voice || undefined });
      setStatus({ engine: res.engine, loaded: res.loaded, model_id: res.model_id });
      pushToast({ message: `Voz cargada (${res.engine}, ${res.load_ms}ms).` });
    } catch (err: unknown) {
      pushToast({ message: toErrorMessage(err, 'Error al cargar voz'), tone: 'error' });
      const s = await ttsApi.getStatus(undefined, lang).catch(() => null);
      setStatus(s);
    } finally {
      setBusy(false);
    }
  };

  const handleUnload = async () => {
    setBusy(true);
    setStatus(null);
    try {
      await ttsApi.unload({ engine: engineOf });
      const s = await ttsApi.getStatus(undefined, lang).catch(() => null);
      setStatus(s);
      pushToast({ message: 'Voz descargada de memoria.' });
    } catch (err: unknown) {
      pushToast({ message: toErrorMessage(err, 'Error al descargar voz'), tone: 'error' });
    } finally {
      setBusy(false);
    }
  };

  return {
    lang,
    setLang,
    voices,
    voiceKey,
    setVoiceKey,
    savedKey,
    status,
    toasts,
    dismissToast,
    busy,
    previewPhase,
    engineOf,
    voice,
    isSavedSelection,
    handleSaveDefault,
    handlePreview,
    handleLoad,
    handleUnload,
  };
}

export type VoicePickerModel = ReturnType<typeof useVoicePicker>;
