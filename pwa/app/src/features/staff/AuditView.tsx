import React, { useEffect, useState } from 'react';
import { toErrorMessage } from '../../shared/lib/errors';
import formStyles from '../../shared/styles/forms.module.css';
import listStyles from '../../shared/styles/lists.module.css';
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
        setError(toErrorMessage(err, 'Error al cargar auditoría'));
      });
  }, []);

  return (
    <div className={listStyles.container} id="audit">
      <div className={listStyles.rowb}>
        <b>Auditoría</b>
        <span>{logs.length}</span>
      </div>
      {error && <div className={formStyles.errorBanner}>{error}</div>}
      <div className={listStyles.rosterList}>
        {logs.length === 0 && !error ? (
          <div style={{ color: 'var(--mute)' }}>Sin registros.</div>
        ) : (
          logs.map((l) => (
            <div key={l.id} className={listStyles.rosterItem}>
              <span className={listStyles.studentName}>
                {l.action}
                {l.target_user_id != null && ` → usuario ${l.target_user_id}`}
              </span>
              <span className={listStyles.roleTag}>
                {l.actor_user_id != null ? `#${l.actor_user_id}` : 'sistema'}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
