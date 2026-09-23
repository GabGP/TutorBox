import React from 'react';
import { Check, X } from 'lucide-react';
import { Sheet } from '../../shared/ui/Sheet/Sheet';
import listStyles from '../../shared/styles/lists.module.css';
import { GenerationLogItem } from './generator.types';
import { formatLatency } from './telemetryFormat';
import { formatFullDate } from '../../shared/lib/format';
import { getSubconceptLabel, getTopicLabel } from '../../shared/taxonomy/labels';
import styles from './TelemetryDetailSheet.module.css';

export interface TelemetryDetailSheetProps {
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
      <div className={styles.detail}>
        <b className={styles.title}>
          {log.success ? <><Check size={16} aria-hidden /> Generación exitosa</> : <><X size={16} aria-hidden /> Generación fallida</>}
        </b>
        <div className={styles.row}>
          <b>Tema:</b> {getTopicLabel(log.topic)}
          {getSubconceptLabel(log.subconcept)
            ? ` · ${getSubconceptLabel(log.subconcept)}`
            : ''}
        </div>
        <div className={styles.row}>
          <b>Usuario:</b> {userLabel}
        </div>
        <div className={styles.row}>
          <b>Modelo:</b> {log.model_name}
        </div>
        <div className={styles.row}>
          <b>Intentos:</b> {log.attempts} · <b>Tiempo:</b>{' '}
          {formatLatency(log.duration_ms)}
        </div>
        <div className={styles.row}>
          <b>Fecha:</b> {formatFullDate(log.created_at)}
        </div>
        <div className={styles.row}>
          <b>Pregunta:</b>{' '}
          {log.question_id ? (
            <code className={styles.code}>{log.question_id}</code>
          ) : (
            '—'
          )}
        </div>
        <div className={styles.row}>
          <b>Rechazos ({log.rejection_history?.length ?? 0}):</b>
        </div>
        {(log.rejection_history?.length ?? 0) > 0 ? (
          <ul className={styles.rejections}>
            {log.rejection_history.map((r, i) => (
              // eslint-disable-next-line react/no-array-index-key
              <li key={i}>{r}</li>
            ))}
          </ul>
        ) : (
          <div className={styles.muted}>
            Sin rechazos registrados.
          </div>
        )}
        <div className={styles.footer}>
          <span className={listStyles.roleTag}>#{log.id}</span>
        </div>
      </div>
    </Sheet>
  );
};
