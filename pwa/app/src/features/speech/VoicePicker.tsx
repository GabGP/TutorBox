import React from 'react';
import { Check, Volume2 } from 'lucide-react';
import { BtnSpinner, PlayButton } from '../../shared/ui/PlayButton/PlayButton';
import formStyles from '../../shared/styles/forms.module.css';
import listStyles from '../../shared/styles/lists.module.css';
import utils from '../../shared/styles/utils.module.css';
import type { SpeechLanguage } from './speech.types';
import { optionKey, useVoicePicker } from './useVoicePicker';

export interface VoicePickerProps {
  /** Only admins may load/unload voices (appliance memory safety). */
  isAdmin?: boolean;
}

/**
 * VoicePicker: language + voice selection for listening and loading.
 * Nothing persists by trying: the choice becomes the game default only
 * via Guardar como predeterminada. Loading/unloading model weights is
 * admin-only: voices share RAM with the LLM, so a teacher-triggered load
 * while the model is resident could exhaust memory on the appliance.
 * The saved voice is the one heard in game speech playback; preview uses
 * the same play/stop button language as the quiz speech controls.
 * State lives in useVoicePicker.
 */
export const VoicePicker: React.FC<VoicePickerProps> = ({ isAdmin = false }) => {
  const {
    lang,
    setLang,
    voices,
    voiceKey,
    setVoiceKey,
    savedKey,
    status,
    error,
    notice,
    busy,
    previewPhase,
    engineOf,
    voice,
    isSavedSelection,
    handleSaveDefault,
    handlePreview,
    handleLoad,
    handleUnload,
  } = useVoicePicker();

  return (
    <div className={listStyles.container} id="voices">
      <div className={listStyles.rowb}>
        <b>Voz</b>
      </div>

      <div className={formStyles.addForm}>
        <select
          className={formStyles.addInput}
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
          className={formStyles.addInput}
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
        <div className={utils.muted}>
          Motor: {status.engine} · Modelo: {status.model_id || '—'}
        </div>
      )}
      {isAdmin && busy && (
        <div className={utils.muted}>
          Actualizando memoria…
        </div>
      )}
      <div className={utils.muted}>
        La voz elegida es la que se escucha en el juego.
        {engineOf && engineOf.toLowerCase().startsWith('qwen') && (
          <> Esta voz varía en cada generación.</>
        )}
      </div>

      {error && <div className={formStyles.errorBanner}>{error}</div>}
      {notice && <div className={formStyles.alert}>{notice}</div>}

      <div className={formStyles.addForm}>
        <button
          type="button"
          className={formStyles.submitAdd}
          onClick={handleSaveDefault}
          disabled={busy || !voice || isSavedSelection}
        >
          {isSavedSelection ? (
            <span className={utils.rowInline6}><Check size={16} aria-hidden /> Predeterminada</span>
          ) : (
            'Guardar como predeterminada'
          )}
        </button>
      </div>

      <div className={formStyles.addForm}>
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
        <div className={formStyles.addForm}>
          <button
            type="button"
            className={formStyles.submitAdd}
            onClick={handleLoad}
            disabled={busy || previewPhase !== 'idle' || !voice}
          >
            {busy && <BtnSpinner />}
            <span>{busy ? 'Cargando…' : 'Cargar voz'}</span>
          </button>
          <button
            type="button"
            className={formStyles.submitAdd}
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
