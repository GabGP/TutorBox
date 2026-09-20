import React, { useCallback, useEffect, useState } from 'react';
import rosterStyles from '../roster/roster.module.css';
import { generatorApi } from './generatorApi';
import { FullGenerationMetrics, GenerationLogItem } from './generator.types';

const PAGE_SIZE = 20;

/**
 * Generation telemetry viewer: aggregate reliability/latency metrics plus
 * the paginated attempt log. Reuses the roster list language.
 */
export const TelemetryView: React.FC = () => {
  const [metrics, setMetrics] = useState<FullGenerationMetrics | null>(null);
  const [logs, setLogs] = useState<GenerationLogItem[]>([]);
  const [topic, setTopic] = useState('');
  const [userId, setUserId] = useState('');
  const [successFilter, setSuccessFilter] = useState<string>('');
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (t: string, u: string, s: string, off: number) => {
    setError(null);
    const uid = u.trim() === '' ? undefined : Number(u);
    if (u.trim() !== '' && !Number.isInteger(uid)) {
      setError('ID de usuario debe ser un número');
      return;
    }
    try {
      const [m, l] = await Promise.all([
        generatorApi.getFullMetrics({ topic: t || undefined }),
        generatorApi.getLogs({
          topic: t || undefined,
          user_id: uid,
          success: s === '' ? undefined : s === 'true',
          limit: PAGE_SIZE,
          offset: off,
        }),
      ]);
      setMetrics(m);
      setLogs(l.logs || []);
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Error al cargar actividad');
    }
  }, []);

  useEffect(() => {
    load(topic, userId, successFilter, offset);
  }, [topic, userId, successFilter, offset, load]);

  return (
    <div className={rosterStyles.container} id="telemetry">
      <div className={rosterStyles.rowb}>
        <b>Actividad de generación</b>
      </div>

      <div className={rosterStyles.addForm}>
        <input
          className={rosterStyles.addInput}
          style={{ flex: 1 }}
          placeholder="Tema (vacío = todos)"
          value={topic}
          onChange={(e) => {
            setTopic(e.target.value);
            setOffset(0);
          }}
        />
        <select
          className={rosterStyles.addInput}
          style={{ flex: '0 0 130px' }}
          value={successFilter}
          onChange={(e) => {
            setSuccessFilter(e.target.value);
            setOffset(0);
          }}
          aria-label="Resultado"
        >
          <option value="">Todos</option>
          <option value="true">Éxitos</option>
          <option value="false">Fallos</option>
        </select>
        <input
          className={rosterStyles.addInput}
          style={{ flex: '0 0 110px' }}
          inputMode="numeric"
          placeholder="ID usuario"
          value={userId}
          onChange={(e) => {
            setUserId(e.target.value);
            setOffset(0);
          }}
          aria-label="ID de usuario"
        />
      </div>

      {error && (
        <div className={rosterStyles.errorBanner}>{error}</div>
      )}

      {metrics && (
        <div className={rosterStyles.rosterList}>
          <div className={rosterStyles.rosterItem}>
            <span className={rosterStyles.studentName}>
              {metrics.total_generations} intentos · {metrics.success_rate}% éxito
            </span>
            <span className={rosterStyles.roleTag}>
              ⌀ {Math.round(metrics.avg_duration_ms)}ms
            </span>
          </div>
          <div className={rosterStyles.rosterItem}>
            <span className={rosterStyles.studentName}>
              ✔ {metrics.successful_generations} · ✘ {metrics.failed_generations} ·{' '}
              {metrics.avg_attempts} intentos/pregunta
            </span>
          </div>
        </div>
      )}

      <div className={rosterStyles.rosterList} id="telemetryLogs">
        {logs.length === 0 ? (
          <div style={{ color: 'var(--mute)' }}>Sin registros.</div>
        ) : (
          logs.map((l) => (
            <div key={l.id} className={rosterStyles.rosterItem}>
              <span className={rosterStyles.studentName}>
                {l.success ? '✔' : '✘'} {l.topic}
                {l.subconcept ? ` · ${l.subconcept}` : ''} · {l.model_name} ·{' '}
                {l.attempts} intentos · {Math.round(l.duration_ms)}ms
              </span>
            </div>
          ))
        )}
      </div>

      <div className={rosterStyles.pagerRow}>
        <button
          type="button"
          className={rosterStyles.submitAdd}
          disabled={offset === 0}
          onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
        >
          ← Anterior
        </button>
        <button
          type="button"
          className={rosterStyles.submitAdd}
          disabled={logs.length < PAGE_SIZE}
          onClick={() => setOffset((o) => o + PAGE_SIZE)}
        >
          Siguiente →
        </button>
      </div>
    </div>
  );
};
