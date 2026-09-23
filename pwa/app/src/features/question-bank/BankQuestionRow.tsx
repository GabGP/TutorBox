import React, { useEffect } from 'react';
import { Eye, Pencil, Trash2 } from 'lucide-react';
import { getTopicLabel } from '../../shared/taxonomy/labels';
import listStyles from '../../shared/styles/lists.module.css';
import utils from '../../shared/styles/utils.module.css';
import { HoldButton } from '../../shared/ui/HoldButton/HoldButton';
import { HOLD_LONG_MS } from '../../shared/ui/HoldButton/holdDurations';
import { SwipeRow } from '../../shared/ui/SwipeRow/SwipeRow';
import styles from './BankQuestionRow.module.css';
import viewStyles from './QuestionBankView.module.css';
import type { BankQuestion } from './bankApi';

export interface BankQuestionRowProps {
  question: BankQuestion;
  selectable: boolean;
  selected: boolean;
  confirmArmed: boolean;
  swipeOpen: boolean;
  onToggleSelect: (id: string) => void;
  onFaceTap: (question: BankQuestion) => void;
  onOpenDetail: (question: BankQuestion) => void;
  onEdit: (question: BankQuestion) => void;
  onArmDelete: (id: string) => void;
  onCommitDelete: (id: string) => void;
  onDisarmDelete: () => void;
  onOpenChange: (open: boolean) => void;
}

/**
 * One bank row: select checkbox plus either the swipe strip
 * (Info/Edit/Delete) or, once delete is armed, a full-row
 * press-and-hold confirm with an explicit Cancelar affordance.
 * Escape disarms; opening another row disarms via onOpenChange.
 */
export const BankQuestionRow: React.FC<BankQuestionRowProps> = ({
  question,
  selectable,
  selected,
  confirmArmed,
  swipeOpen,
  onToggleSelect,
  onFaceTap,
  onOpenDetail,
  onEdit,
  onArmDelete,
  onCommitDelete,
  onDisarmDelete,
  onOpenChange,
}) => {
  useEffect(() => {
    if (!confirmArmed) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onDisarmDelete();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [confirmArmed, onDisarmDelete]);

  return (
    <div
      role="listitem"
      className={selectable ? viewStyles.selectRow : undefined}
    >
      {selectable && (
        <input
          type="checkbox"
          checked={selected}
          onChange={() => onToggleSelect(question.id)}
          aria-label={`Elegir pregunta ${question.id}`}
          className={viewStyles.selectCheck}
        />
      )}
      <div className={utils.grow}>
        {confirmArmed ? (
          <div className={styles.confirmRow}>
            <HoldButton
              holdTime={HOLD_LONG_MS}
              size="sm"
              className={styles.confirmHold}
              ariaLabel={`Mantén para eliminar pregunta ${question.id}`}
              backgroundColor="var(--bad-bg, #FFE9E7)"
              fillColor="var(--bad, #B3261E)"
              textColor="var(--bad-ink, #5F1710)"
              fillTextColor="#ffffff"
              doneLabel="Eliminada"
              onHold={() => onCommitDelete(question.id)}
            >
              Mantén para eliminar
            </HoldButton>
            <button
              type="button"
              className={styles.cancelBtn}
              onClick={onDisarmDelete}
              aria-label={`Cancelar eliminación pregunta ${question.id}`}
            >
              Cancelar
            </button>
          </div>
        ) : (
          <SwipeRow
            ariaLabel={`Pregunta ${question.id}`}
            open={swipeOpen}
            onOpenChange={onOpenChange}
            actions={[
              {
                key: 'info',
                label: 'Info',
                ariaLabel: `Ver detalle pregunta ${question.id}`,
                icon: <Eye aria-hidden />,
                onActivate: () => onOpenDetail(question),
              },
              {
                key: 'edit',
                label: 'Editar',
                ariaLabel: `Editar pregunta ${question.id}`,
                icon: <Pencil aria-hidden />,
                onActivate: () => onEdit(question),
              },
              {
                key: 'delete',
                label: 'Eliminar',
                icon: <Trash2 aria-hidden />,
                tone: 'danger',
                onActivate: () => onArmDelete(question.id),
              },
            ]}
          >
            <button
              type="button"
              className={`${listStyles.studentName} ${viewStyles.faceButton}`}
              onClick={() => onFaceTap(question)}
            >
              {question.question_text}
            </button>
            <span className={`${listStyles.roleTag} ${viewStyles.topicTag}`}>
              {getTopicLabel(question.topic)}
            </span>
          </SwipeRow>
        )}
      </div>
    </div>
  );
};
