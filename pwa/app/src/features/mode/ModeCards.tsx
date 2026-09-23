import React from 'react';
import { MessageCircle } from 'lucide-react';
import styles from './mode.module.css';

/** The one drawing of Q'uq', served with the Primero app (pwa/tareas/primero/public/icons). */
const QUQ_SRC = '/tareas/primero/icons/quq.svg';

/**
 * What a student phone shows while the class is not in quiz mode. No login needed.
 *
 * @param {object} props - `mode`: `tutor` or `apps`.
 * @returns {JSX.Element} The take-home download card or the tutor "coming soon" card.
 */
export const StudentModeCard: React.FC<{ mode: 'tutor' | 'apps' }> = ({ mode }) =>
  mode === 'apps' ? (
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
  ) : (
    <section className={styles.card} id="s-tutor">
      <MessageCircle size={56} aria-hidden />
      <h2>El tutor llega pronto</h2>
      <p>Muy pronto vas a practicar matemáticas conversando con el tutor. Espera las instrucciones de tu maestra o maestro.</p>
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
        <p>El tutor todavía no está listo: los teléfonos de los alumnos muestran «El tutor llega pronto».</p>
      </>
    )}
    <p className={styles.mute}>
      Para volver al juego, elige <strong>Quiz</strong> arriba.
    </p>
  </section>
);
