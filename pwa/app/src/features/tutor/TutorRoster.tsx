import React from 'react';
import { useTutorRoster } from './useTutorRoster';
import styles from './tutor.module.css';

/** "hace 2 min" style age of a student's last activity. */
function lastSeen(seconds: number): string {
  if (seconds < 60) return 'ahora';
  return `hace ${Math.floor(seconds / 60)} min`;
}

/**
 * Teacher panel in tutor mode: which students have the tutor open, what they are working
 * on and how far up the hint ladder they are.
 *
 * @param {object} props - `host` shown in the empty state, `pollingIntervalMs` for tests.
 */
export const TutorRoster: React.FC<{ host: string; pollingIntervalMs?: number }> = ({
  host,
  pollingIntervalMs,
}) => {
  const { students, loaded, error } = useTutorRoster(pollingIntervalMs);
  const online = students.filter((student) => student.online).length;

  return (
    <section className={styles.roster} aria-label="Alumnos en el tutor">
      <h3>
        Alumnos en el tutor <span className={styles.count}>{online} conectados</span>
      </h3>
      {error && (
        <p className={styles.alert} role="alert">
          {error}
        </p>
      )}
      {loaded && students.length === 0 && (
        <p className={styles.mute}>
          Todavía nadie. Los alumnos entran desde su teléfono en <strong>{host}/alumno</strong> con su
          usuario y PIN.
        </p>
      )}
      <ul className={styles.students}>
        {students.map((student) => (
          <li key={student.username} className={styles.student}>
            <i
              className={student.online ? styles.dotOn : styles.dotOff}
              role="img"
              aria-label={student.online ? 'Conectado' : 'Desconectado'}
            />
            <div>
              <strong>{student.username}</strong>
              <span className={styles.mute}>
                {' '}
                · {student.turns} mensajes · {student.solved} resueltos · {lastSeen(student.seconds_ago)}
              </span>
              <p className={styles.work}>
                {student.problem
                  ? `Resolviendo ${student.problem} · pista ${student.hint_level} de 3`
                  : 'Sin problema abierto'}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
};
