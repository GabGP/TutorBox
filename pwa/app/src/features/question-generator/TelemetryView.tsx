import React, { useCallback, useEffect, useState } from 'react';
import { Check, Gauge, X } from 'lucide-react';
import { DataList } from '../../shared/ui/DataList/DataList';
import { Pagination } from '../../shared/ui/Pagination/Pagination';
import { Skeleton } from '../../shared/ui/Skeleton/Skeleton';
import { getRoleLabel } from '../../shared/constants/roles';
import formStyles from '../../shared/styles/forms.module.css';
import listStyles from '../../shared/styles/lists.module.css';
import { useTopics } from '../../shared/taxonomy/useTopics';
import { generatorApi } from './generatorApi';
import { rosterApi } from '../roster/rosterApi';
import {
  FullGenerationMetrics,
  GenerationLogItem,
} from './generator.types';
import { TelemetryDetailSheet } from './TelemetryDetailSheet';
import { formatLatency, formatPercent, formatShortDate } from './telemetryFormat';
import { getSubconceptLabel, getTopicLabel } from '../../shared/taxonomy/labels';
import teleStyles from './TelemetryView.module.css';

const DEFAULT_PAGE_SIZE = 5;
const PAGE_SIZE_OPTIONS = [5, 10, 20, 50];

interface TelemetryLogRowProps {
  log: GenerationLogItem;
  userLabel: string;
  onOpen: () => void;
}

/** One attempt row: a full-row tap target opening the detail sheet. */
const TelemetryLogRow: React.FC<TelemetryLogRowProps> = ({
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

/**
 * Generation telemetry viewer: aggregate reliability/latency metrics plus
 * the paginated attempt log. Merged into the shared DataList + Pagination
 * treatment (same as the question bank) while keeping all filters,
 * metrics info, and log details.
 */
export const TelemetryView: React.FC = () => {
  const [metrics, setMetrics] = useState<FullGenerationMetrics | null>(null);
  const [logs, setLogs] = useState<GenerationLogItem[]>([]);
  const [total, setTotal] = useState(0);
  const { topics } = useTopics();
  const [topic, setTopic] = useState('');
  const [userId, setUserId] = useState('');
  const [userOptions, setUserOptions] = useState<
    Array<{ id: string; username: string; role: string }>
  >([]);
  const [successFilter, setSuccessFilter] = useState<string>('');
  const [offset, setOffset] = useState(0);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<GenerationLogItem | null>(null);

  useEffect(() => {
    rosterApi
      .getAll()
      .then((res) => {
        const list = Array.isArray(res.users) ? res.users : [];
        // Only teachers/admins can generate questions, so students
        // never appear in this filter.
        setUserOptions(
          list
            .filter(
              (u) =>
                typeof (u as { username?: unknown }).username === 'string' &&
                ((u as { role?: unknown }).role === 'teacher' ||
                  (u as { role?: unknown }).role === 'admin')
            )
            .map((u) => ({
              id: String((u as { id: unknown }).id),
              username: (u as { username: string }).username,
              role: String((u as { role: unknown }).role),
            }))
        );
      })
      .catch(() => {});
  }, []);

  const load = useCallback(
    async (t: string, u: string, s: string, off: number, size: number) => {
      setError(null);
      const uid = u.trim() === '' ? undefined : Number(u);
      if (u.trim() !== '' && !Number.isInteger(uid)) {
        setError('ID de usuario debe ser un número');
        return;
      }
      setLoading(true);
      try {
        const [m, l] = await Promise.all([
          generatorApi.getFullMetrics({ topic: t || undefined }),
          generatorApi.getLogs({
            topic: t || undefined,
            user_id: uid,
            success: s === '' ? undefined : s === 'true',
            limit: size,
            offset: off,
          }),
        ]);
        setMetrics(m);
        setLogs(l.logs || []);
        setTotal(l.total ?? (l.logs || []).length);
      } catch (err: unknown) {
        const e = err as { message?: string };
        setError(e.message || 'Error al cargar actividad');
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    load(topic, userId, successFilter, offset, pageSize);
  }, [topic, userId, successFilter, offset, pageSize, load]);

  // Clamp offset when total shrinks (e.g. filter change) so pagination
  // never strands on an empty page.
  useEffect(() => {
    if (total > 0 && offset >= total) {
      setOffset(Math.max(0, (Math.ceil(total / pageSize) - 1) * pageSize));
    }
  }, [total, offset, pageSize]);

  const page = Math.floor(offset / pageSize) + 1;
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const userNameById = new Map(userOptions.map((u) => [u.id, u.username]));
  // Newest first (created_at, then id as tiebreak), so the latest
  // attempts always lead regardless of server ordering.
  const sortedLogs = React.useMemo(
    () =>
      [...logs].sort((a, b) => {
        const ca = a.created_at || '';
        const cb = b.created_at || '';
        if (cb !== ca) return cb < ca ? -1 : 1;
        return b.id - a.id;
      }),
    [logs]
  );
  // Keep IDs seen in the current page selectable too (e.g. deleted users
  // missing from the roster) plus the active filter so the select never
  // strands on a value with no option.
  const extraUserIds = Array.from(
    new Set(
      sortedLogs
        .map((l) => l.user_id)
        .filter((id) => id !== null && id !== undefined)
        .map((id) => String(id))
        .concat(userId ? [userId] : [])
        .filter((id) => id && !userNameById.has(id))
    )
  );

  const userLabelFor = (l: GenerationLogItem): string =>
    l.user_id !== null && l.user_id !== undefined
      ? userNameById.get(String(l.user_id)) || `#${l.user_id}`
      : '—';

  return (
    <div className={listStyles.container} id="telemetry">
      <div className={listStyles.rowb}>
        <b>Actividad de generación</b>
        <span id="telemetryCount">{total}</span>
      </div>

      <div className={formStyles.addForm}>
        <select
          className={formStyles.addInput}
          style={{ flex: 1 }}
          value={topic}
          onChange={(e) => {
            setTopic(e.target.value);
            setOffset(0);
          }}
          aria-label="Tema"
        >
          <option value="">Todos los temas</option>
          {topics.map((t) => (
            <option key={t.name} value={t.name}>
              {t.label || getTopicLabel(t.name)}
            </option>
          ))}
        </select>
        <select
          className={formStyles.addInput}
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
        <select
          className={formStyles.addInput}
          style={{ flex: '0 0 150px' }}
          value={userId}
          onChange={(e) => {
            setUserId(e.target.value);
            setOffset(0);
          }}
          aria-label="ID de usuario"
        >
          <option value="">Todos los usuarios</option>
          {userOptions.map((u) => (
            <option key={u.id} value={u.id}>
              {u.username} · {getRoleLabel(u.role)}
            </option>
          ))}
          {extraUserIds.map((id) => (
            <option key={id} value={id}>
              #{id}
            </option>
          ))}
        </select>
      </div>

      {error && <div className={formStyles.errorBanner}>{error}</div>}

      {metrics && (
        <DataList
          id="telemetryMetrics"
          ariaLabel="Resumen de generación"
          isEmpty={false}
        >
          <div
            role="listitem"
            style={{
              padding: '10px 12px',
              display: 'flex',
              gap: '10px',
              alignItems: 'center',
            }}
          >
            <span className={listStyles.studentName}>
              {metrics.total_generations} intentos ·{' '}
              {formatPercent(metrics.success_rate)} éxito
            </span>
            <span className={listStyles.roleTag} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              <Gauge size={13} aria-hidden /> {formatLatency(metrics.avg_duration_ms)}
            </span>
          </div>
          <div role="listitem" style={{ padding: '10px 12px' }}>
            <span className={listStyles.studentName} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              <Check size={14} aria-hidden /> {metrics.successful_generations} · <X size={14} aria-hidden />{' '}
              {metrics.failed_generations} · {metrics.avg_attempts}{' '}
              intentos/pregunta
            </span>
          </div>
        </DataList>
      )}

      {loading ? (
        <DataList
          id="telemetryLogs"
          ariaLabel="Actividad de generación"
          busy
          isEmpty={false}
          header={
            <div className={teleStyles.headRow} style={{ flex: 1 }}>
              <span />
              <span>Tema</span>
              <span>Usuario</span>
              <span style={{ textAlign: 'right' }}>Datos</span>
            </div>
          }
        >
          {Array.from({ length: pageSize }, (_, i) => (
            <div
              key={`sk-${i}`}
              role="listitem"
              data-testid="telemetry-skeleton"
              className={teleStyles.row}
            >
              <div className={`${teleStyles.cell} ${teleStyles.status}`}>
                <Skeleton style={{ width: '18px', height: '18px' }} />
              </div>
              <div className={teleStyles.cell}>
                <Skeleton style={{ height: '16px', marginBottom: '4px' }} />
                <Skeleton style={{ height: '12px', width: '70%' }} />
              </div>
              <div className={teleStyles.cell}>
                <Skeleton style={{ height: '16px', marginBottom: '4px' }} />
                <Skeleton style={{ height: '12px', width: '60%' }} />
              </div>
              <div className={teleStyles.cell}>
                <Skeleton style={{ height: '16px', marginBottom: '4px' }} />
                <Skeleton style={{ height: '12px', width: '80%' }} />
              </div>
            </div>
          ))}
        </DataList>
      ) : (
        <DataList
          id="telemetryLogs"
          ariaLabel="Actividad de generación"
          isEmpty={sortedLogs.length === 0}
          emptyText="Sin registros."
          header={
            sortedLogs.length > 0 ? (
              <div className={teleStyles.headRow} style={{ flex: 1 }}>
                <span />
                <span>Tema</span>
                <span>Usuario</span>
                <span style={{ textAlign: 'right' }}>Datos</span>
              </div>
            ) : undefined
          }
        >
          {sortedLogs.map((l) => (
            <div key={l.id} role="listitem">
              <TelemetryLogRow
                log={l}
                userLabel={userLabelFor(l)}
                onOpen={() => setDetail(l)}
              />
            </div>
          ))}
        </DataList>
      )}

      <Pagination
        id="telemetryPager"
        page={page}
        pages={pages}
        pageSize={pageSize}
        pageSizeOptions={PAGE_SIZE_OPTIONS}
        onPrev={() => setOffset((o) => Math.max(0, o - pageSize))}
        onNext={() =>
          setOffset((o) => Math.min((pages - 1) * pageSize, o + pageSize))
        }
        onFirst={() => setOffset(0)}
        onLast={() => setOffset((pages - 1) * pageSize)}
        onPageSizeChange={(size) => {
          setPageSize(size);
          setOffset(0);
        }}
        disabled={loading}
      />

      <TelemetryDetailSheet
        log={detail}
        userNameById={userNameById}
        onClose={() => setDetail(null)}
      />
    </div>
  );
};
