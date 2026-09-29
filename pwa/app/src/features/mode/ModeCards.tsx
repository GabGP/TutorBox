import React from 'react';
import styles from './mode.module.css';

/** The one drawing of Q'uq', served with the Primero app (pwa/tareas/primero/public/icons). */
const QUQ_SRC = '/tareas/primero/icons/quq.svg';

/** The take-home apps, one per grade (pwa/tareas/<id>, APKs in pwa/tareas/descargas). */
const GRADES = [
  { id: 'primero', number: '1º', name: 'Primero' },
  { id: 'segundo', number: '2º', name: 'Segundo' },
  { id: 'tercero', number: '3º', name: 'Tercero' },
] as const;

/**
 * What a student phone shows in take-home mode: pick your grade, then download its app (the
 * download page opens on that grade, with the install steps) or play it in the browser.
 * No login needed. (In tutor mode the phone shows the tutor chat instead: features/tutor.)
 *
 * @returns {JSX.Element} The take-home grade menu.
 */
export const StudentModeCard: React.FC = () => (
  <section className={styles.card} id="s-apps">
    <img src={QUQ_SRC} alt="" className={styles.quq} />
    <h2>¡Llévate a Q'uq' a casa!</h2>
    <p>Elige la app de tu grado. Funciona en tu teléfono, sin internet.</p>
    <ul className={styles.grades}>
      {GRADES.map((grade) => (
        <li key={grade.id}>
          <a className={styles.primary} href={`/descargas/#${grade.id}`}>
            Descargar {grade.number} {grade.name}
          </a>
          <a className={styles.link} href={`/tareas/${grade.id}/`}>
            o juega {grade.name} en el navegador
          </a>
        </li>
      ))}
    </ul>
  </section>
);

/**
 * Teacher panel while the class is in tutor or take-home mode, in place of the quiz setup.
 *
 * @param {object} props - `mode` and the appliance `host` (e.g. `tutorbox`).
 * @returns {JSX.Element} What the students see and how to go back to the quiz.
 */
export const TeacherModeNotice: React.FC<{ mode: 'tutor' | 'apps'; host: string }> = ({ mode, host }) => (
  <section className={styles.card} id="s-mode">
    {mode === 'apps' ? (
      <>
        <h2>Modo: llevar a casa</h2>
        <p>
          Los teléfonos de los alumnos muestran las apps de Primero, Segundo y Tercero: cada alumno elige
          la de su grado. También pueden abrir:
        </p>
        <p className={styles.address}>{host}/descargas</p>
        <p>
          Chrome avisará que el archivo «no se puede descargar de forma segura»: los alumnos tocan{' '}
          <strong>Conservar</strong>.
        </p>
      </>
    ) : (
      <>
        <h2>Modo: tutor</h2>
        <p>Los alumnos entran desde su teléfono con su usuario y PIN en:</p>
        <p className={styles.address}>{host}/alumno</p>
        <p>
          Practican matemáticas del CNB con el tutor. El tutor no da respuestas: guía con preguntas y
          pistas.
        </p>
      </>
    )}
    <p className={styles.mute}>
      Para volver al juego, elige <strong>Quiz</strong> arriba.
    </p>
  </section>
);
