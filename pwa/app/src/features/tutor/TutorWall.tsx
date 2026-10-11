import React from 'react';
import { useTutorSummary } from './useTutorSummary';
import styles from './tutorWall.module.css';

/**
 * The classroom screen in tutor mode: where to join, Q'uq', and live class totals
 * (connected, solved, asking for help). Totals only: the wall shows no names.
 *
 * @param {object} props - `host` of the appliance (e.g. `tutorbox`), `pollingIntervalMs` for tests.
 */
export const TutorWall: React.FC<{ host: string; pollingIntervalMs?: number }> = ({ host, pollingIntervalMs }) => {
  const summary = useTutorSummary(pollingIntervalMs);
  const stats = [
    { label: 'conectados', value: summary?.online, accent: false },
    { label: 'resueltos', value: summary?.solved, accent: false },
    { label: 'piden ayuda', value: summary?.need_help, accent: true },
  ];

  return (
    <section id="s-mode" className={styles.wall}>
      <div className={styles.copy}>
        <span className={styles.tag}>Modo tutor</span>
        <h1 className={styles.title}>Practica con el tutor</h1>
        <p className={styles.lead}>En tu teléfono, entra a esta dirección con tu usuario y PIN:</p>
        {host && <p className={styles.address}>{host}/alumno</p>}
      </div>
      <div className={styles.side}>
        <img src="/tareas/primero/icons/quq.svg" alt="" className={styles.quq} />
        <ul className={styles.stats} aria-label="La clase en el tutor">
          {stats.map((stat) => (
            <li key={stat.label}>
              <strong className={stat.accent ? styles.accent : undefined}>{stat.value ?? '–'}</strong>
              <span>{stat.label}</span>
            </li>
          ))}
        </ul>
      </div>
      <p className={styles.footer}>El tutor no da respuestas: te ayuda a encontrarlas.</p>
    </section>
  );
};
