import React, { useCallback, useEffect, useState } from 'react';
import { DataList } from '../../shared/ui/DataList/DataList';
import { Pager } from '../../shared/ui/Pager/Pager';
import { Skeleton } from '../../shared/ui/Skeleton/Skeleton';
import { ToastViewport } from '../../shared/ui/Toast/ToastViewport';
import { useToastQueue } from '../../shared/ui/Toast/useToastQueue';
import { usePagination } from '../../shared/lib/pagination';
import { toErrorMessage } from '../../shared/lib/errors';
import { useTopics } from '../../shared/taxonomy/useTopics';
import { getTopicLabel } from '../../shared/taxonomy/labels';
import formStyles from '../../shared/styles/forms.module.css';
import listStyles from '../../shared/styles/lists.module.css';
import styles from './QuestionBankView.module.css';
import { BankQuestion, bankApi } from './bankApi';
import { BankQuestionRow } from './BankQuestionRow';
import { QuestionDetailSheet } from './QuestionDetailSheet';
import { QuestionEditSheet } from './QuestionEditSheet';
import { SchemaViewer } from './SchemaViewer';

const DEFAULT_PAGE_SIZE = 5;
const PAGE_SIZE_OPTIONS = [5, 10, 20, 50];

/**
 * Question-bank browser: topic filter, swipe rows with Info/Edit/Delete
 * actions, detail in a floating sheet (refreshed from the server on open),
 * full-row hold-to-confirm delete (see BankQuestionRow), and an edit
 * affordance opening the floating edit sheet.
 * Optional select mode (checkboxes + tap-to-toggle) lets the quiz-prep
 * flow build a match from hand-picked questions. Creation lives in the
 * Crear tab; the JSON contract viewer is admin-only.
 * Load and mutation failures float as error toasts so the list never
 * shifts; successes already toast through the same queue.
 */
export interface QuestionBankViewProps {
  selectable?: boolean;
  selectedIds?: string[];
  onToggleSelect?: (id: string) => void;
  reloadKey?: number;
  initialTopic?: string;
  isAdmin?: boolean;
}

export const QuestionBankView: React.FC<QuestionBankViewProps> = ({
  selectable = false,
  selectedIds = [],
  onToggleSelect,
  reloadKey = 0,
  initialTopic = '',
  isAdmin = false,
}) => {
  const { topics } = useTopics();
  const [topic, setTopic] = useState(initialTopic);
  const [questions, setQuestions] = useState<BankQuestion[]>([]);
  const [total, setTotal] = useState(0);
  const { offset, setOffset, pageSize, setPageSize } = usePagination(DEFAULT_PAGE_SIZE);
  const [loading, setLoading] = useState(false);
  const { toasts, pushToast, dismissToast } = useToastQueue();
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const [editing, setEditing] = useState<BankQuestion | null>(null);
  const [detail, setDetail] = useState<BankQuestion | null>(null);
  const [openSwipeId, setOpenSwipeId] = useState<string | null>(null);

  const load = useCallback(async (t: string, off: number, size: number) => {
    setLoading(true);
    try {
      const res = await bankApi.listQuestions({
        topic: t || undefined,
        limit: size,
        offset: off,
      });
      setQuestions(res.questions || []);
      setTotal(res.total ?? 0);
    } catch (err: unknown) {
      pushToast({ message: toErrorMessage(err, 'Error al cargar preguntas'), tone: 'error' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(topic, offset, pageSize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topic, offset, pageSize, load, reloadKey]);

  const handleOpenDetail = async (q: BankQuestion) => {
    setDetail(q);
    // Refresh the detail from GET /quiz/questions/{id} so edits made
    // elsewhere (or generated content) never show stale.
    try {
      const fresh = await bankApi.getQuestion(q.id);
      setQuestions((prev) => prev.map((x) => (x.id === q.id ? fresh : x)));
      setDetail(fresh);
    } catch (err: unknown) {
      pushToast({ message: toErrorMessage(err, 'Error al actualizar el detalle'), tone: 'error' });
    }
  };

  const handleFaceTap = (q: BankQuestion) => {
    if (selectable) {
      onToggleSelect?.(q.id);
      return;
    }
    void handleOpenDetail(q);
  };

  const handleDeleteCommit = async (id: string) => {
    setConfirmDelete(null);
    setOpenSwipeId(null);
    try {
      await bankApi.deleteQuestion(id);
      pushToast({ message: 'Pregunta eliminada.' });
      if (detail?.id === id) setDetail(null);
      // A deleted question must not stay counted as selected.
      if (selectable && selectedIds.includes(id)) onToggleSelect?.(id);
      load(topic, offset, pageSize);
    } catch (err: unknown) {
      pushToast({ message: toErrorMessage(err, 'Error al eliminar'), tone: 'error' });
    }
  };

  const handleArmDelete = (id: string) => {
    // Swipe tap only arms; the row swaps to a HoldButton that commits.
    setConfirmDelete(id);
  };

  const handleDisarmDelete = useCallback(() => {
    setConfirmDelete(null);
  }, []);

  const handleSavedEdit = (id: string) => {
    setEditing(null);
    setOpenSwipeId(null);
    pushToast({ message: `Pregunta actualizada (${id}).` });
    load(topic, offset, pageSize);
  };

  return (
    <div className={listStyles.container} id="bank">
      <div className={listStyles.rowb}>
        <b>Banco de preguntas</b>
        <span id="bankCount">
          {selectable ? `${selectedIds.length} elegidas · ${total}` : total}
        </span>
      </div>

      <div className={formStyles.addForm}>
        <select
          id="bankTopic"
          className={`${formStyles.addInput} ${formStyles.fill}`}
          value={topic}
          onChange={(e) => {
            setTopic(e.target.value);
            setOffset(0);
          }}
          aria-label="Tema"
        >
          <option value="">Todos los temas</option>
          {topics.map((t) => (
            <option key={t.name} value={t.name}>
              {t.label || getTopicLabel(t.name)}
            </option>
          ))}
        </select>
      </div>

      <ToastViewport toasts={toasts} onDismiss={(id) => dismissToast(id)} />

      {loading ? (
        <DataList
          id="bankList"
          ariaLabel="Banco de preguntas"
          busy
          isEmpty={false}
        >
          {Array.from({ length: pageSize }, (_, i) => (
            <div
              key={`sk-${i}`}
              role="listitem"
              data-testid="bank-skeleton"
              className={styles.skeletonRow}
            >
              <Skeleton className={styles.skeletonText} />
              <Skeleton className={styles.skeletonTag} />
            </div>
          ))}
        </DataList>
      ) : (
        <DataList
          id="bankList"
          ariaLabel="Banco de preguntas"
          isEmpty={questions.length === 0}
          emptyText="No hay preguntas para este filtro."
        >
          {questions.map((q) => (
            <BankQuestionRow
              key={q.id}
              question={q}
              selectable={selectable}
              selected={selectedIds.includes(q.id)}
              confirmArmed={confirmDelete === q.id}
              swipeOpen={openSwipeId === q.id}
              onToggleSelect={(id) => onToggleSelect?.(id)}
              onFaceTap={handleFaceTap}
              onOpenDetail={(row) => void handleOpenDetail(row)}
              onEdit={(row) => setEditing(row)}
              onArmDelete={handleArmDelete}
              onCommitDelete={(id) => void handleDeleteCommit(id)}
              onDisarmDelete={handleDisarmDelete}
              onOpenChange={(next) => {
                setOpenSwipeId(next ? q.id : null);
                // Disarm this row on close; disarm any other armed row
                // when opening a different one so confirm never leaks.
                if (!next) {
                  if (confirmDelete === q.id) setConfirmDelete(null);
                } else if (confirmDelete && confirmDelete !== q.id) {
                  setConfirmDelete(null);
                }
              }}
            />
          ))}
        </DataList>
      )}

      <Pager
        id="bankPager"
        offset={offset}
        pageSize={pageSize}
        total={total}
        pageSizeOptions={PAGE_SIZE_OPTIONS}
        onOffsetChange={setOffset}
        onPageSizeChange={setPageSize}
        disabled={loading}
      />

      {isAdmin && <SchemaViewer onError={(message) => pushToast({ message, tone: 'error' })} />}

      <QuestionEditSheet
        question={editing}
        onClose={() => setEditing(null)}
        onSaved={handleSavedEdit}
      />
      <QuestionDetailSheet
        question={detail}
        onClose={() => setDetail(null)}
      />
    </div>
  );
};
