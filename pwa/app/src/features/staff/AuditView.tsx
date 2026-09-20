import React, { useEffect, useState } from 'react';
import rosterStyles from '../roster/roster.module.css';
import { AuditLogItem, auditApi } from './auditApi';

/**
 * Admin audit trail viewer. Renders the last 500 audit entries newest-first.
 * Parent must only mount for `role === 'admin'`.
 */
export const AuditView: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    auditApi
      .getAuditLogs()
      .then(setLogs)
      .catch((err: unknown) => {
        const e = err as { message?: string };
        setError(e.message || 'Error al cargar auditoría');
      });
  }, []);

  return (
    <div className={rosterStyles.container} id="audit">
      <div className={rosterStyles.rowb}>
        <b>Auditoría</b>
        <span>{logs.length}</span>
      </div>
      {error && <div className={rosterStyles.errorBanner}>{error}</div>}
      <div className={rosterStyles.rosterList}>
        {logs.length === 0 && !error ? (
          <div style={{ color: 'var(--mute)' }}>Sin registros.</div>
        ) : (
          logs.map((l) => (
            <div key={l.id} className={rosterStyles.rosterItem}>
              <span className={rosterStyles.studentName}>
                {l.action}
                {l.target_user_id != null && ` → usuario ${l.target_user_id}`}
              </span>
              <span className={rosterStyles.roleTag}>
                {l.actor_user_id != null ? `#${l.actor_user_id}` : 'sistema'}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
