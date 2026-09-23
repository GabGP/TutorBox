import React, { useEffect, useMemo, useState } from 'react';
import { useApplianceMode } from '../../features/mode/useApplianceMode';
import { computeDisplayStep } from '../../features/session-engine/sessionStateMachine';
import { useSessionEngine } from '../../features/session-engine/useSessionEngine';
import { OPTION_LETTERS } from '../../shared/constants/options';
import { getSessionQueryParamId, useHostAddress } from '../../shared/routing/session';
import { CountdownRing } from '../../shared/ui/CountdownRing/CountdownRing';
import { TallyBars } from '../../shared/ui/TallyBars/TallyBars';
import styles from './DisplayView.module.css';

/**
 * HDMI Classroom Projector Display View.
 * Displays large-format high-contrast views for the classroom wall:
 * connection URL in idle mode, countdown question views with giant typography,
 * and animated tally bars upon round revelation.
 *
 * @returns {JSX.Element} The rendered HDMI classroom display.
 */
export const DisplayView: React.FC = () => {
  const [lastSid, setLastSid] = useState<string | null>(null);
  const targetSessionId = useMemo(() => getSessionQueryParamId(), []);

  const { session } = useSessionEngine({
    targetSessionId: targetSessionId || undefined,
    fallbackSessionId: lastSid,
  });

  const host = useHostAddress();
  const hostAddress = host ? `${host}/alumno` : '';
  const { mode } = useApplianceMode();

  useEffect(() => {
    if (session?.id) {
      setLastSid(session.id);
    }
  }, [session?.id]);

  // Tutor and take-home modes: the wall screen tells the class where to go on their phones.
  if (mode === 'tutor' || mode === 'apps') {
    const apps = mode === 'apps';
    return (
      <div className={styles.displayShell}>
        <section id="s-mode" className={`${styles.section} ${styles.center}`}>
          <img src="/tareas/primero/icons/quq.svg" alt="" width={120} height={170} />
          <div className={styles.h}>{apps ? "¡Llévate a Q'uq' a casa!" : 'El tutor llega pronto'}</div>
          <div className={styles.sub}>
            {apps ? 'En tu teléfono, abre esta dirección y descarga la app:' : 'Muy pronto vas a practicar con el tutor en tu teléfono.'}
          </div>
          <div className={styles.count}>{host ? `${host}/${apps ? 'descargas' : 'alumno'}` : ''}</div>
        </section>
      </div>
    );
  }

  const step = computeDisplayStep(session);
  const round = session?.current_round;
  const question = round?.question;
  const tally = round?.result?.tally;

  return (
    <div className={styles.displayShell}>
      {step === 'idle' && (
        <section id="s-idle" className={`${styles.section} ${styles.center}`}>
          <div className={styles.logo}>T</div>
          <div className={styles.h}>TutorBox está listo</div>
          <div className={styles.sub} id="idleSub">
            {session
              ? 'El docente está preparando el juego'
              : 'Esperando a que el docente inicie el juego'}
          </div>
          <div className={styles.count} id="ready">
            {hostAddress}
          </div>
        </section>
      )}

      {step === 'question' && round && question && (
        <section id="s-question" className={styles.section}>
          <div className={styles.top}>
            <div className={styles.sub} id="counter">
              Pregunta {round.round_index + 1} de {session?.question_count} · {round.votes_cast} respuestas
            </div>
            <CountdownRing
              id="ring"
              size={92}
              remaining={round.status === 'open' ? round.time_remaining : 0}
              duration={round.duration_seconds}
              theme="dark"
            />
          </div>
          <div className={styles.q} id="qtext">
            {question.question_text}
          </div>
          <div className={styles.opts} id="opts">
            {OPTION_LETTERS.map((letter) => (
              <div
                key={letter}
                className={`${styles.opt} ${styles[`k_${letter}`]}`}
              >
                <i>{letter}</i>
                <span>{question.options[letter] || ''}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {step === 'reveal' && round && question && tally && (
        <section id="s-reveal" className={`${styles.section} ${styles.center}`}>
          <div className={styles.lbl}>RESPUESTA CORRECTA</div>
          <div className={styles.reveal}>
            <i
              id="cletter"
              className={styles[`k_${tally.correct_option}`]}
            >
              {tally.correct_option}
            </i>
            <b id="ctext">{question.options[tally.correct_option]}</b>
          </div>
          <div className={styles.rbarsContainer}>
            <TallyBars
              id="rbars"
              options={question.options}
              counts={tally.counts}
              totalVotes={tally.total_votes}
              animate
              theme="dark"
            />
          </div>
        </section>
      )}

      {step === 'stats' && (
        <section id="s-stats" className={`${styles.section} ${styles.center}`}>
          <div className={styles.h}>¡Buen trabajo, grupo!</div>
          <div className={styles.sub}>Terminó el juego</div>
        </section>
      )}
    </div>
  );
};
