import React from 'react';
import { Check, Gauge, X } from 'lucide-react';
import { DataList } from '../../shared/ui/DataList/DataList';
import listStyles from '../../shared/styles/lists.module.css';
import utils from '../../shared/styles/utils.module.css';
import type { FullGenerationMetrics } from './generator.types';
import { formatLatency, formatPercent } from './telemetryFormat';
import styles from './TelemetryView.module.css';

export interface TelemetryMetricsCardProps {
  metrics: FullGenerationMetrics;
}

/** Aggregate reliability/latency summary for the generation telemetry. */
export const TelemetryMetricsCard: React.FC<TelemetryMetricsCardProps> = ({
  metrics,
}) => (
  <DataList
    id="telemetryMetrics"
    ariaLabel="Resumen de generación"
    isEmpty={false}
  >
    <div role="listitem" className={styles.metricsRow}>
      <span className={listStyles.studentName}>
        {metrics.total_generations} intentos ·{' '}
        {formatPercent(metrics.success_rate)} éxito
      </span>
      <span className={`${listStyles.roleTag} ${utils.rowInline4}`}>
        <Gauge size={13} aria-hidden /> {formatLatency(metrics.avg_duration_ms)}
      </span>
    </div>
    <div role="listitem" className={styles.metricsRow}>
      <span className={`${listStyles.studentName} ${utils.rowInline4}`}>
        <Check size={14} aria-hidden /> {metrics.successful_generations} · <X size={14} aria-hidden />{' '}
        {metrics.failed_generations} · {metrics.avg_attempts}{' '}
        intentos/pregunta
      </span>
    </div>
  </DataList>
);
