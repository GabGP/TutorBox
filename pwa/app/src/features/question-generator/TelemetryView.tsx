import React, { useCallback, useEffect, useState } from 'react';
import { DataList } from '../../shared/ui/DataList/DataList';
import { Pager } from '../../shared/ui/Pager/Pager';
import { Skeleton } from '../../shared/ui/Skeleton/Skeleton';
import { toErrorMessage } from '../../shared/lib/errors';
import { usePagination } from '../../shared/lib/pagination';
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
import { TelemetryFilters, type TelemetryFilterUser } from './TelemetryFilters';
import { TelemetryLogRow } from './TelemetryLogRow';
import { TelemetryMetricsCard } from './TelemetryMetricsCard';
import teleStyles from './TelemetryView.module.css';

const DEFAULT_PAGE_SIZE = 5;
const PAGE_SIZE_OPTIONS = [5, 10, 20, 50];

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
  const [userOptions, setUserOptions] = useState<TelemetryFilterUser[]>([]);
  const [successFilter, setSuccessFilter] = useState<string>('');
  const { offset, setOffset, pageSize, setPageSize } = usePagination(DEFAULT_PAGE_SIZE);
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
        setError(toErrorMessage(err, 'Error al cargar actividad'));
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    load(topic, userId, successFilter, offset, pageSize);
  }, [topic, userId, successFilter, offset, pageSize, load]);

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

  const tableHead = (
    <div className={`${teleStyles.headRow} ${teleStyles.headGrow}`}>
      <span />
      <span>Tema</span>
      <span>Usuario</span>
      <span className={teleStyles.headRight}>Datos</span>
    </div>
  );

  return (
    <div className={listStyles.container} id="telemetry">
      <div className={listStyles.rowb}>
        <b>Actividad de generación</b>
        <span id="telemetryCount">{total}</span>
      </div>

      <TelemetryFilters
        topics={topics}
        topic={topic}
        successFilter={successFilter}
        userId={userId}
        userOptions={userOptions}
        extraUserIds={extraUserIds}
        onTopicChange={(v) => {
          setTopic(v);
          setOffset(0);
        }}
        onSuccessFilterChange={(v) => {
          setSuccessFilter(v);
          setOffset(0);
        }}
        onUserIdChange={(v) => {
          setUserId(v);
          setOffset(0);
        }}
      />

      {error && <div className={formStyles.errorBanner}>{error}</div>}

      {metrics && <TelemetryMetricsCard metrics={metrics} />}

      {loading ? (
        <DataList
          id="telemetryLogs"
          ariaLabel="Actividad de generación"
          busy
          isEmpty={false}
          header={tableHead}
        >
          {Array.from({ length: pageSize }, (_, i) => (
            <div
              key={`sk-${i}`}
              role="listitem"
              data-testid="telemetry-skeleton"
              className={teleStyles.row}
            >
              <div className={`${teleStyles.cell} ${teleStyles.status}`}>
                <Skeleton className={teleStyles.skIcon} />
              </div>
              <div className={teleStyles.cell}>
                <Skeleton className={teleStyles.skLine} />
                <Skeleton className={teleStyles.skSub70} />
              </div>
              <div className={teleStyles.cell}>
                <Skeleton className={teleStyles.skLine} />
                <Skeleton className={teleStyles.skSub60} />
              </div>
              <div className={teleStyles.cell}>
                <Skeleton className={teleStyles.skLine} />
                <Skeleton className={teleStyles.skSub80} />
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
          header={sortedLogs.length > 0 ? tableHead : undefined}
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

      <Pager
        id="telemetryPager"
        offset={offset}
        pageSize={pageSize}
        total={total}
        pageSizeOptions={PAGE_SIZE_OPTIONS}
        onOffsetChange={setOffset}
        onPageSizeChange={setPageSize}
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
