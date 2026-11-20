import React, { useEffect, useRef } from 'react';
import { CheckCircle2, Circle, Eye, Pencil, Trash2 } from 'lucide-react';
import { getTopicLabel } from '../../shared/taxonomy/labels';
import listStyles from '../../shared/styles/lists.module.css';
import utils from '../../shared/styles/utils.module.css';
import { HoldButton } from '../../shared/ui/HoldButton/HoldButton';
import { HOLD_LONG_MS } from '../../shared/ui/HoldButton/holdDurations';
import { SwipeRow } from '../../shared/ui/SwipeRow/SwipeRow';
import styles from './BankQuestionRow.module.css';
import viewStyles from './QuestionBankView.module.css';
import type { BankQuestion } from './bankApi';

/**
 * Horizontal travel, in px, above which a click on the face is the end of a
 * drag rather than a tap (a mouse drag still fires its click). Same guard as
 * the clicker rows; taps stay well under it.
 */
const DRAG_CLICK_TOLERANCE_PX = 8;

export interface BankQuestionRowProps {
  question: BankQuestion;
  selectable: boolean;
  /** Seleccionar mode: a tap toggles the question for the match. */
  selecting?: boolean;
  selected: boolean;
  confirmArmed: boolean;
  swipeOpen: boolean;
  /** Tap on the face: toggles the question in Seleccionar mode, else slides the row open or shut. */
  onFaceTap: (question: BankQuestion) => void;
  /** The circle in Seleccionar mode. */
  onToggleSelect: (id: string) => void;
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
 * Cancelar affordance. A tap on the face only slides the row open or shut;
 * the actions live in the strip. In Seleccionar mode a tap on the face or on
 * its circle toggles the question for the match; a check marks the chosen.
 * Escape disarms; opening another row disarms via onOpenChange.
 */
export const BankQuestionRow: React.FC<BankQuestionRowProps> = ({
  question,
  selectable,
  selecting = false,
  selected,
  confirmArmed,
  swipeOpen,
  onFaceTap,
  onToggleSelect,
  onOpenDetail,
  onEdit,
  onArmDelete,
  onCommitDelete,
  onDisarmDelete,
  onOpenChange,
}) => {
  // Where the pointer went down on the face; null when no press is pending.
  const pressX = useRef<number | null>(null);
  const handleFaceClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    const startX = pressX.current;
    pressX.current = null;
    if (startX !== null && Math.abs(event.clientX - startX) > DRAG_CLICK_TOLERANCE_PX) return;
    onFaceTap(question);
  };

  useEffect(() => {
    if (!confirmArmed) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onDisarmDelete();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [confirmArmed, onDisarmDelete]);

  return (
    <div role="listitem">
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
            {/* The check is the only mark of a chosen question; in Seleccionar
                mode it becomes a circle button that toggles it. */}
            {selectable && !selecting && selected && (
              <span
                className={`${viewStyles.selectMark} ${viewStyles.selectMarkOn}`}
                role="img"
                aria-label="En el juego"
              >
                <CheckCircle2 size={22} aria-hidden />
              </span>
            )}
            {selecting && (
              <button
                type="button"
                className={`${viewStyles.selectMark} ${selected ? viewStyles.selectMarkOn : ''}`}
                aria-label={`${selected ? 'Quitar' : 'Elegir'} pregunta ${question.id}`}
                aria-pressed={selected}
                onClick={() => onToggleSelect(question.id)}
              >
                {selected ? <CheckCircle2 size={22} aria-hidden /> : <Circle size={22} aria-hidden />}
              </button>
            )}
            <button
              type="button"
              className={`${listStyles.studentName} ${viewStyles.faceButton}`}
              onPointerDown={(event) => {
                pressX.current = event.clientX;
              }}
              onClick={handleFaceClick}
              aria-expanded={selecting ? undefined : swipeOpen}
              aria-pressed={selecting ? selected : undefined}
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
