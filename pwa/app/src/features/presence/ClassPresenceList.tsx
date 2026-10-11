import React from 'react';
import formStyles from '../../shared/styles/forms.module.css';
import listStyles from '../../shared/styles/lists.module.css';
import utils from '../../shared/styles/utils.module.css';
import styles from './presence.module.css';
import { PresenceRow } from './PresenceRow';
import type { ClassPresence } from './presence.types';
import { presenceSummaryLabel } from './presenceLabels';
import { useClassPresence } from './useClassPresence';

const EMPTY_CLASS_TEXT =
  'Todavía no hay alumnos. Agregue uno o pídales crear su cuenta en la dirección de arriba.';

export interface ClassPresenceListProps {
  onManageUsers: () => void;
  onOpenClickers: () => void;
  /** Pause between polls; tests shorten it. */
  pollingIntervalMs?: number;
}

interface UnassignedClickersProps {
  ids: string[];
  onOpenClickers: () => void;
}

/** Clickers that no student holds yet: their ids, why they matter, and the way to assign them. */
const UnassignedClickers: React.FC<UnassignedClickersProps> = ({ ids, onOpenClickers }) => (
  <section className={styles.unassigned} aria-labelledby="unassignedClickersTitle">
    <h3 id="unassignedClickersTitle" className={styles.subtitle}>
      Clickers sin alumno
    </h3>
    <ul className={styles.idList}>
      {ids.map((id) => (
        <li key={id} className={styles.idChip}>
          {id}
        </li>
      ))}
    </ul>
    <p className={utils.help}>Un clicker necesita un alumno antes de poder conectarse.</p>
    <button
      type="button"
      className={`${formStyles.submitAdd} ${styles.actionButton}`}
      onClick={onOpenClickers}
    >
      Asignar clickers
    </button>
  </section>
);

function countDropped(presence: ClassPresence): number {
  return presence.students.filter((student) => student.status === 'dropped').length;
}

/**
 * The teacher's lobby list: who is connected by phone or clicker, which
 * connections dropped, and the clickers nobody holds yet. Shows the last good
 * list while a poll fails, and a loading line until the first answer.
 */
export const ClassPresenceList: React.FC<ClassPresenceListProps> = ({
  onManageUsers,
  onOpenClickers,
  pollingIntervalMs,
}) => {
  const { presence, error } = useClassPresence(pollingIntervalMs);

  return (
    <section className={`${listStyles.container} ${styles.panel}`} aria-labelledby="classPresenceTitle">
      <div className={`${listStyles.rowb} ${styles.header}`}>
        <h2 id="classPresenceTitle" className={styles.title}>
          Alumnos
        </h2>
        {presence && (
          <span className={styles.summary}>
            {presenceSummaryLabel(presence.online, presence.total, countDropped(presence))}
          </span>
        )}
      </div>

      {error && (
        <p className={formStyles.errorBanner} role="alert">
          {error}
        </p>
      )}
      {presence === null && !error && <p className={utils.muted}>Cargando la lista de alumnos…</p>}
      {presence && presence.students.length === 0 && <p className={utils.help}>{EMPTY_CLASS_TEXT}</p>}
      {presence && presence.students.length > 0 && (
        <ul className={`${listStyles.rosterList} ${styles.rows}`}>
          {presence.students.map((student) => (
            <PresenceRow key={student.user_id} student={student} />
          ))}
        </ul>
      )}

      {presence && presence.unassigned_clickers.length > 0 && (
        <UnassignedClickers ids={presence.unassigned_clickers} onOpenClickers={onOpenClickers} />
      )}

      <button
        type="button"
        className={`${formStyles.submitAdd} ${styles.actionButton}`}
        onClick={onManageUsers}
      >
        Administrar usuarios
      </button>
    </section>
  );
};
