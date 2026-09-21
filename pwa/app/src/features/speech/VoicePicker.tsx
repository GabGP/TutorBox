import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Check, Volume2 } from 'lucide-react';
import { storage } from '../../shared/lib/storage';
import { BtnSpinner, PlayButton } from '../../shared/ui/PlayButton/PlayButton';
import rosterStyles from '../roster/roster.module.css';
import { speechApi, ttsApi } from './speechApi';
import { SpeechLanguage, TTSStatusResponse, TTSVoiceItem } from './speech.types';

export interface VoicePickerProps {
  /** Only admins may load/unload voices (appliance memory safety). */
  isAdmin?: boolean;
}

/** Option values are engine-qualified: two engines may share a voice id. */
function optionKey(v: TTSVoiceItem): string {
  return `${v.engine}::${v.id}`;
}

function parseKey(key: string): { engine?: string; voice?: string } {
  const sep = key.indexOf('::');
  if (sep < 0) return { voice: key || undefined };
  return { engine: key.slice(0, sep) || undefined, voice: key.slice(sep + 2) || undefined };
}

/**
 * VoicePicker: language + voice selection for listening and loading.
 * Nothing persists by trying: the choice becomes the game default only
 * via Guardar como predeterminada. Loading/unloading model weights is
 * admin-only: voices share RAM with the LLM, so a teacher-triggered load
 * while the model is resident could exhaust memory on the appliance.
 * The saved voice is the one heard in game speech playback; preview uses
 * the same play/stop button language as the quiz speech controls.
 */
export const VoicePicker: React.FC<VoicePickerProps> = ({ isAdmin = false }) => {
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
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [previewPhase, setPreviewPhase] = useState<'idle' | 'loading' | 'playing'>('idle');
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const refresh = useCallback(async (l: SpeechLanguage) => {
    setError(null);
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
      const e = err as { message?: string };
      setError(e.message || 'Error al cargar voces');
    }
  }, []);

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
    setError(null);
    setNotice(null);
    setStatus(null);
    try {
      storage.setVoicePreference({ lang, engine: engineOf, voice });
      setSavedKey(voiceKey);
      await ttsApi.unload({}).catch(() => null);
      const s = await ttsApi.getStatus(undefined, lang).catch(() => null);
      setStatus(s);
      setNotice('Voz guardada como predeterminada para el juego.');
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Error al guardar la voz');
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
    setError(null);
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
        setError('No se pudo reproducir la muestra');
      };
      await audio.play();
      setPreviewPhase('playing');
    } catch (err: unknown) {
      const e = err as { message?: string };
      setPreviewPhase('idle');
      setError(e.message || 'Error al generar muestra');
    }
  };

  const handleLoad = async () => {
    setBusy(true);
    setError(null);
    setNotice(null);
    // Clear stale status first: the server evicts other resident engines
    // on load, so the previous "Motor" line must not linger as if current.
    setStatus(null);
    try {
      const res = await ttsApi.load({ lang, engine: engineOf, voice: voice || undefined });
      setStatus({ engine: res.engine, loaded: res.loaded, model_id: res.model_id });
      setNotice(`Voz cargada (${res.engine}, ${res.load_ms}ms).`);
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Error al cargar voz');
      const s = await ttsApi.getStatus(undefined, lang).catch(() => null);
      setStatus(s);
    } finally {
      setBusy(false);
    }
  };

  const handleUnload = async () => {
    setBusy(true);
    setError(null);
    setNotice(null);
    setStatus(null);
    try {
      await ttsApi.unload({ engine: engineOf });
      const s = await ttsApi.getStatus(undefined, lang).catch(() => null);
      setStatus(s);
      setNotice('Voz descargada de memoria.');
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Error al descargar voz');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className={rosterStyles.container} id="voices">
      <div className={rosterStyles.rowb}>
        <b>Voz</b>
      </div>

      <div className={rosterStyles.addForm}>
        <select
          className={rosterStyles.addInput}
          style={{ flex: '0 0 130px' }}
          value={lang}
          onChange={(e) => setLang(e.target.value as SpeechLanguage)}
          aria-label="Idioma"
        >
          <option value="es">Español</option>
          <option value="quc">K&apos;iche&apos;</option>
        </select>
        <select
          id="voicePick"
          className={rosterStyles.addInput}
          style={{ flex: 1 }}
          value={voiceKey}
          onChange={(e) => setVoiceKey(e.target.value)}
          aria-label="Voz"
        >
          {voices.length === 0 && <option value="">Sin voces</option>}
          {voices.map((v) => {
            const key = optionKey(v);
            return (
              <option key={key} value={key}>
                {v.engine} · {v.id}
                {key === savedKey ? ' · predeterminada' : ''}
              </option>
            );
          })}
        </select>
      </div>

      {isAdmin && status && !busy && (
        <div style={{ color: 'var(--mute2)', fontSize: '14px' }}>
          Motor: {status.engine} · Modelo: {status.model_id || '—'}
        </div>
      )}
      {isAdmin && busy && (
        <div style={{ color: 'var(--mute2)', fontSize: '14px' }}>
          Actualizando memoria…
        </div>
      )}
      <div style={{ color: 'var(--mute2)', fontSize: '14px' }}>
        La voz elegida es la que se escucha en el juego.
        {engineOf && engineOf.toLowerCase().startsWith('qwen') && (
          <> Esta voz varía en cada generación.</>
        )}
      </div>

      {error && <div className={rosterStyles.errorBanner}>{error}</div>}
      {notice && <div className={rosterStyles.alert}>{notice}</div>}

      <div className={rosterStyles.addForm}>
        <button
          type="button"
          className={rosterStyles.submitAdd}
          onClick={handleSaveDefault}
          disabled={busy || !voice || isSavedSelection}
        >
          {isSavedSelection ? (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}><Check size={16} aria-hidden /> Predeterminada</span>
          ) : (
            'Guardar como predeterminada'
          )}
        </button>
      </div>

      <div className={rosterStyles.addForm}>
        <PlayButton
          phase={previewPhase}
          onClick={handlePreview}
          disabled={previewPhase === 'loading' || busy || !voice}
          ariaLabel={
            previewPhase === 'loading'
              ? 'Generando muestra, espera'
              : previewPhase === 'playing'
                ? 'Sonando muestra, clic para detener'
                : 'Escuchar muestra de voz'
          }
          idleLabel={<><Volume2 size={18} aria-hidden /> Escuchar</>}
          loadingLabel="Generando…"
          playingLabel="Sonando…"
        />
      </div>

      {isAdmin && (
        <div className={rosterStyles.addForm}>
          <button
            type="button"
            className={rosterStyles.submitAdd}
            onClick={handleLoad}
            disabled={busy || previewPhase !== 'idle' || !voice}
          >
            {busy && <BtnSpinner />}
            <span>{busy ? 'Cargando…' : 'Cargar voz'}</span>
          </button>
          <button
            type="button"
            className={rosterStyles.submitAdd}
            onClick={handleUnload}
            disabled={busy || previewPhase !== 'idle'}
          >
            Descargar
          </button>
        </div>
      )}
    </div>
  );
};
