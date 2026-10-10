import React from 'react';
import type { TutorStudent } from './tutorApi';
import { useTutorRoster } from './useTutorRoster';
import styles from './tutor.module.css';

/** On the last hint and still connected: the teacher should go over. */
const needsHelp = (student: TutorStudent): boolean =>
  student.online && Boolean(student.problem) && student.hint_level >= 3;

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
  // Stuck students first; otherwise keep the backend's order (connected first, then by name).
  const ordered = [...students.filter(needsHelp), ...students.filter((student) => !needsHelp(student))];

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
        {ordered.map((student) => (
          <li
            key={student.username}
            className={needsHelp(student) ? `${styles.student} ${styles.needsHelp}` : styles.student}
          >
            <i
              className={student.online ? styles.dotOn : styles.dotOff}
              role="img"
              aria-label={student.online ? 'Conectado' : 'Desconectado'}
            />
            <div className={styles.studentBody}>
              <strong>{student.username}</strong>
              {needsHelp(student) && <span className={styles.helpTag}>Necesita ayuda</span>}
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
