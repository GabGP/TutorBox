import React from 'react';
import { ClassPresenceList } from '../../features/presence/ClassPresenceList';
import { SessionModel } from '../../features/session-engine/session.types';
import utils from '../../shared/styles/utils.module.css';
import styles from './TeacherLobby.module.css';

export interface TeacherLobbyProps {
  session: SessionModel | null;
  hostAddress: string;
  onManageUsers: () => void;
  onOpenClickers: () => void;
}

/**
 * Teacher Pre-Game Lobby View component.
 * Displays how many questions are ready, where students connect, and the
 * class list: who is connected by phone or clicker, and who dropped.
 */
export const TeacherLobby: React.FC<TeacherLobbyProps> = ({
  session,
  hostAddress,
  onManageUsers,
  onOpenClickers,
}) => {
  return (
    <div className={styles.stack} id="s-lobby">
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

      <p className={utils.help} id="genHelp">
        Los alumnos entran con su usuario y PIN. Cuando estén listos, comience el juego.
      </p>

      <ClassPresenceList onManageUsers={onManageUsers} onOpenClickers={onOpenClickers} />
    </div>
  );
};
