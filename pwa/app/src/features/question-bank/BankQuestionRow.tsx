import React, { useEffect } from 'react';
import { Check, ChevronDown, Eye, Pencil, Trash2 } from 'lucide-react';
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
  /** Select mode only: the inline option editor is open below the row. */
  expanded?: boolean;
  /** Select mode only: rendered under the row while expanded. */
  expandedContent?: React.ReactNode;
  confirmArmed: boolean;
  swipeOpen: boolean;
  onFaceTap: (question: BankQuestion) => void;
  onOpenDetail: (question: BankQuestion) => void;
  onEdit: (question: BankQuestion) => void;
  onArmDelete: (id: string) => void;
  onCommitDelete: (id: string) => void;
  onDisarmDelete: () => void;
  onOpenChange: (open: boolean) => void;
}

/**
 * One bank row: either the swipe strip (Info/Edit/Delete) or, once
 * delete is armed, a full-row press-and-hold confirm with an explicit
 * Cancelar affordance. In select mode the face toggles an inline panel
 * (expandedContent) and a tag marks questions chosen for the match.
 * Escape disarms; opening another row disarms via onOpenChange.
 */
export const BankQuestionRow: React.FC<BankQuestionRowProps> = ({
  question,
  selectable,
  selected,
  expanded = false,
  expandedContent,
  confirmArmed,
  swipeOpen,
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
      className={
        selectable
          ? `${viewStyles.selectRow} ${selected ? viewStyles.selectRowOn : ''} ${expanded ? viewStyles.selectRowOpen : ''}`
          : undefined
      }
    >
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
              aria-expanded={selectable ? expanded : undefined}
            >
              {question.question_text}
            </button>
            {selectable && selected && (
              <span className={`${listStyles.roleTag} ${viewStyles.chosenTag}`}>
                <Check size={14} aria-hidden /> En el juego
              </span>
            )}
            <span className={`${listStyles.roleTag} ${viewStyles.topicTag}`}>
              {getTopicLabel(question.topic)}
            </span>
            {selectable && (
              <ChevronDown
                size={18}
                aria-hidden
                className={`${viewStyles.chev} ${expanded ? viewStyles.chevOpen : ''}`}
              />
            )}
          </SwipeRow>
        )}
        {selectable && expanded && !confirmArmed && expandedContent}
      </div>
    </div>
  );
};
