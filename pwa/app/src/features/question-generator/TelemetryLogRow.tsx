import React from 'react';
import { Check, X } from 'lucide-react';
import type { GenerationLogItem } from './generator.types';
import { formatLatency, formatShortDate } from './telemetryFormat';
import { getSubconceptLabel, getTopicLabel } from '../../shared/taxonomy/labels';
import teleStyles from './TelemetryView.module.css';

export interface TelemetryLogRowProps {
  log: GenerationLogItem;
  userLabel: string;
  onOpen: () => void;
}

/** One attempt row: a full-row tap target opening the detail sheet. */
export const TelemetryLogRow: React.FC<TelemetryLogRowProps> = ({
  log,
  userLabel,
  onOpen,
}) => {
  const topicLabel = getTopicLabel(log.topic);
  const subLabel = getSubconceptLabel(log.subconcept);
  const shortDate = formatShortDate(log.created_at);
  return (
    <button
      type="button"
      className={teleStyles.rowBtn}
      onClick={onOpen}
      aria-label={`Ver detalle generación ${log.id}`}
    >
      <span
        className={`${teleStyles.cell} ${teleStyles.status} ${
          log.success ? teleStyles.ok : teleStyles.fail
        }`}
      >
        {log.success ? <Check size={16} aria-hidden /> : <X size={16} aria-hidden />}
      </span>
      <span className={teleStyles.cell}>
        <span className={teleStyles.primary}>{topicLabel}</span>
        {subLabel && (
          <span className={teleStyles.secondary}>{subLabel}</span>
        )}
      </span>
      <span className={teleStyles.cell}>
        <span className={teleStyles.primary}>{userLabel}</span>
        <span className={teleStyles.secondary}>{log.model_name}</span>
      </span>
        <span className={`${teleStyles.cell} ${teleStyles.numeric}`}>
          <span className={teleStyles.primary}>
            {log.attempts} {log.attempts === 1 ? 'intento' : 'intentos'}
          </span>
          <span className={teleStyles.secondary}>
            {formatLatency(log.duration_ms)}
          </span>
          {shortDate && (
            <span className={teleStyles.tertiary}>{shortDate}</span>
          )}
        </span>
    </button>
  );
};
