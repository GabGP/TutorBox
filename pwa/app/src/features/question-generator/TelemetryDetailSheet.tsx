import React from 'react';
import { Check, X } from 'lucide-react';
import { Sheet } from '../../shared/ui/Sheet/Sheet';
import rosterStyles from '../roster/roster.module.css';
import { GenerationLogItem } from './generator.types';
import { formatLatency } from './telemetryFormat';
import { formatFullDate } from '../../shared/lib/format';
import { getSubconceptLabel, getTopicLabel } from '../../shared/taxonomy/labels';export interface TelemetryDetailSheetProps {
  /** Null = closed. */
  log: GenerationLogItem | null;
  /** Resolves a staff user id to its display name. */
  userNameById: Map<string, string>;
  onClose: () => void;
}

/**
 * Read-only detail card for a generation attempt: every field the log
 * carries (status, taxonomy, staff user, model, attempts, latency,
 * linked question, timestamp, rejection trail).
 */
export const TelemetryDetailSheet: React.FC<TelemetryDetailSheetProps> = ({
  log,
  userNameById,
  onClose,
}) => {
  if (!log) return null;
  const userLabel =
    log.user_id !== null && log.user_id !== undefined
      ? userNameById.get(String(log.user_id)) || `#${log.user_id}`
      : '—';
  return (
    <Sheet label={`Detalle de generación #${log.id}`} onClose={onClose}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <b style={{ fontSize: '16px', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
          {log.success ? <><Check size={16} aria-hidden /> Generación exitosa</> : <><X size={16} aria-hidden /> Generación fallida</>}
        </b>
        <div style={{ fontSize: '14px' }}>
          <b>Tema:</b> {getTopicLabel(log.topic)}
          {getSubconceptLabel(log.subconcept)
            ? ` · ${getSubconceptLabel(log.subconcept)}`
            : ''}
        </div>
        <div style={{ fontSize: '14px' }}>
          <b>Usuario:</b> {userLabel}
        </div>
        <div style={{ fontSize: '14px' }}>
          <b>Modelo:</b> {log.model_name}
        </div>
        <div style={{ fontSize: '14px' }}>
          <b>Intentos:</b> {log.attempts} · <b>Tiempo:</b>{' '}
          {formatLatency(log.duration_ms)}
        </div>
        <div style={{ fontSize: '14px' }}>
          <b>Fecha:</b> {formatFullDate(log.created_at)}
        </div>
        <div style={{ fontSize: '14px' }}>
          <b>Pregunta:</b>{' '}
          {log.question_id ? (
            <code style={{ overflowWrap: 'anywhere' }}>{log.question_id}</code>
          ) : (
            '—'
          )}
        </div>
        <div style={{ fontSize: '14px' }}>
          <b>Rechazos ({log.rejection_history?.length ?? 0}):</b>
        </div>
        {(log.rejection_history?.length ?? 0) > 0 ? (
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px' }}>
            {log.rejection_history.map((r, i) => (
              // eslint-disable-next-line react/no-array-index-key
              <li key={i}>{r}</li>
            ))}
          </ul>
        ) : (
          <div
            style={{ fontSize: '13px', color: 'var(--mute2)' }}
          >
            Sin rechazos registrados.
          </div>
        )}
        <div
          style={{
            color: 'var(--mute2)',
            fontSize: '13px',
            marginTop: '4px',
          }}
        >
          <span className={rosterStyles.roleTag}>#{log.id}</span>
        </div>
      </div>
    </Sheet>
  );
};
