import React from 'react';
import { GenerationProgress } from '../../features/question-generator/generator.types';
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
 * Displays connection instructions, student URL badges, generation progress telemetry,
 * and the student roster table for classroom preparation.
 *
 * @param {TeacherLobbyProps} props - Component props containing session status, progress, roster props, and URL address.
 * @returns {JSX.Element} The rendered pre-game lobby interface.
 */
export const TeacherLobby: React.FC<TeacherLobbyProps> = ({
  session,
  progress,
  rosterProps,
  hostAddress,
}) => {
  let heroLbl = '';
  let heroBig: string | number = '';
  let genHelp = '';

  if (session) {
    heroLbl = 'PREGUNTAS LISTAS';
    heroBig = session.question_count;
    genHelp =
      'Los alumnos entran con su usuario y PIN. Cuando estén listos, comience el juego.';
  } else if (progress) {
    heroLbl = 'TUTORBOX ESTÁ CREANDO';
    heroBig = `Pregunta ${Math.min(progress.done + 1, progress.total)} de ${progress.total}`;
    genHelp =
      'El modelo local escribe cada pregunta y la revisa con matemáticas.' +
      (progress.eta ? ` Tarda aprox. ${progress.eta} s por pregunta.` : '');
  }

  const failed = progress?.failed || 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }} id="s-lobby">
      <div className={styles.hero}>
        <div>
          <div className={styles.lbl} id="heroLbl">
            {heroLbl}
          </div>
          <div className={styles.big} id="heroBig">
            {heroBig}
          </div>
        </div>
        <div>
          <div className={styles.lbl}>ENTRAN EN</div>
          <div className={styles.addr} id="addr">
            {hostAddress}
          </div>
        </div>
      </div>

      <p style={{ fontSize: '15px', color: 'var(--mute2)', margin: 0 }} id="genHelp">
        {genHelp}
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
