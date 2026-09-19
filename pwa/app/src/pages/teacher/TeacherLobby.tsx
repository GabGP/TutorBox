import React from 'react';
import { GenerationProgress } from '../../features/question-generator/generator.types';
import { QuestionGenerationProgress } from '../../features/question-generator/QuestionGenerationProgress';
import { RosterTable, RosterTableProps } from '../../features/roster/RosterTable';
import { SessionModel } from '../../features/session-engine/session.types';
import styles from './TeacherLobby.module.css';

export interface TeacherLobbyProps {
  session: SessionModel | null;
  progress: GenerationProgress | null;
  rosterProps: RosterTableProps;
  hostAddress: string;
}

/**
 * Teacher Pre-Game Lobby View component.
 * Displays connection instructions, question generation progress telemetry,
 * and the student roster table for classroom preparation.
 */
export const TeacherLobby: React.FC<TeacherLobbyProps> = ({
  session,
  progress,
  rosterProps,
  hostAddress,
}) => {
  const failed = progress?.failed || 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }} id="s-lobby">
      {progress ? (
        <QuestionGenerationProgress
          progress={progress}
          isComplete={Boolean(session)}
        />
      ) : (
        <div className={styles.hero}>
          <div>
            <div className={styles.lbl} id="heroLbl">
              PREGUNTAS LISTAS
            </div>
            <div className={styles.big} id="heroBig">
              {session ? session.question_count : ''}
            </div>
          </div>
          <div>
            <div className={styles.lbl}>ENTRAN EN</div>
            <div className={styles.addr} id="addr">
              {hostAddress}
            </div>
          </div>
        </div>
      )}

      {progress && (
        <div className={styles.connectionCard}>
          <span className={styles.connectionLabel}>ENTRAN EN</span>
          <span className={styles.connectionAddr} id="addr">
            {hostAddress}
          </span>
        </div>
      )}

      <p style={{ fontSize: '15px', color: 'var(--mute2)', margin: 0 }} id="genHelp">
        Los alumnos entran con su usuario y PIN. Cuando estén listos, comience el juego.
      </p>

      {failed > 0 && (
        <div className="note" id="genNote">
          {failed} pregunta(s) no salieron del modelo; el juego tendrá{' '}
          {progress?.ids.length} preguntas.
        </div>
      )}

      <RosterTable {...rosterProps} />
    </div>
  );
};
