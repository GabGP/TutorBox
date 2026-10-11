import React, { useEffect, useState } from 'react';
import styles from './ServerBadge.module.css';

export interface HealthResponse {
  status: string;
  database?: string;
}

/**
 * Local Appliance Server Connectivity Badge.
 * Performs a lightweight `/health` probe to verify backend database and service availability,
 * displaying a green or red status dot.
 *
 * @returns {JSX.Element} The rendered server health badge.
 */
export const ServerBadge: React.FC = () => {
  const [status, setStatus] = useState<'loading' | 'ok' | 'err'>('loading');
  const [label, setLabel] = useState("Buscando Utz'tutor…");

  useEffect(() => {
    let mounted = true;

    // /health lives outside /api/v1 so it intentionally bypasses requestApi.
    fetch('/health')
      .then((r) => r.json())
      .then((h: HealthResponse) => {
        if (!mounted) return;
        if (h.status === 'ok') {
          setStatus('ok');
          setLabel("Utz'tutor listo");
        } else {
          setStatus('err');
          setLabel(`Utz'tutor con problemas: ${h.database || 'desconocido'}`);
        }
      })
      .catch(() => {
        if (!mounted) return;
        setStatus('err');
        setLabel("Sin conexión con Utz'tutor");
      });

    return () => {
      mounted = false;
    };
  }, []);

  const stateClass = status === 'ok' ? styles.ok : status === 'err' ? styles.err : '';

  return (
    <div className={`${styles.status} ${stateClass}`} id="health">
      <i className={styles.dot} />
      <span>{label}</span>
    </div>
  );
};
