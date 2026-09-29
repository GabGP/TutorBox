import React from 'react';
import styles from './mode.module.css';

/** The one drawing of Q'uq', served with the Primero app (pwa/tareas/primero/public/icons). */
const QUQ_SRC = '/tareas/primero/icons/quq.svg';

/**
 * What a student phone shows in take-home mode. No login needed.
 * (In tutor mode the phone shows the tutor chat instead: features/tutor.)
 *
 * @returns {JSX.Element} The take-home download card.
 */
export const StudentModeCard: React.FC = () => (
  <section className={styles.card} id="s-apps">
    <img src={QUQ_SRC} alt="" className={styles.quq} />
    <h2>¡Llévate a Q'uq' a casa!</h2>
    <p>Juega y aprende matemáticas en tu teléfono, sin internet.</p>
    <a className={styles.primary} href="/descargas/">
      Descargar la app
    </a>
    <a className={styles.secondary} href="/tareas/primero/">
      Jugar aquí, en el navegador
    </a>
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
        <p>Los teléfonos de los alumnos muestran la descarga de la app de Primero. También pueden abrir:</p>
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
