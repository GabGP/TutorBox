import React, { useEffect, useState } from 'react';
import { toErrorMessage } from '../../shared/lib/errors';
import { usePagination } from '../../shared/lib/pagination';
import listStyles from '../../shared/styles/lists.module.css';
import { DataList } from '../../shared/ui/DataList/DataList';
import { Pager } from '../../shared/ui/Pager/Pager';
import { ToastViewport } from '../../shared/ui/Toast/ToastViewport';
import { useToastQueue } from '../../shared/ui/Toast/useToastQueue';
import { AuditLogItem, auditApi } from './auditApi';

const PAGE_SIZE_OPTIONS = [10, 20, 50];

/**
 * Admin audit trail viewer. Renders audit entries newest-first in a shared
 * DataList shell with client-side pagination. Parent must only mount for
 * `role === 'admin'`. Load failures float as error toasts so the list
 * never shifts.
 */
export const AuditView: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const { offset, setOffset, pageSize, setPageSize } = usePagination(20);
  const { toasts, pushToast, dismissToast } = useToastQueue();

  useEffect(() => {
    auditApi
      .getAuditLogs()
      .then((items) =>
        setLogs([...items].sort((a, b) => b.id - a.id))
      )
      .catch((err: unknown) => {
        pushToast({ message: toErrorMessage(err, 'Error al cargar auditoría'), tone: 'error' });
      });
  }, [pushToast]);

  const pageItems = logs.slice(offset, offset + pageSize);

  return (
    <div className={listStyles.container} id="audit">
      <div className={listStyles.rowb}>
        <b>Auditoría</b>
        <span>{logs.length}</span>
      </div>
      <ToastViewport toasts={toasts} onDismiss={(id) => dismissToast(id)} />
      <DataList
        id="auditList"
        ariaLabel="Auditoría"
        isEmpty={pageItems.length === 0}
        emptyText="Sin registros."
      >
        {pageItems.map((l) => (
          <div key={l.id} role="listitem" className={listStyles.rosterItem}>
            <span className={listStyles.studentName}>
              {l.action}
              {l.target_user_id != null && ` → usuario ${l.target_user_id}`}
            </span>
            <span className={listStyles.roleTag}>
              {l.actor_user_id != null ? `#${l.actor_user_id}` : 'sistema'}
            </span>
          </div>
        ))}
      </DataList>
      <Pager
        id="auditPager"
        offset={offset}
        pageSize={pageSize}
        total={logs.length}
        pageSizeOptions={PAGE_SIZE_OPTIONS}
        onOffsetChange={setOffset}
        onPageSizeChange={setPageSize}
      />
    </div>
  );
};
