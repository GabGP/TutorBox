import React, { useCallback, useEffect, useState } from 'react';
import { Eye, Pencil, Trash2 } from 'lucide-react';
import { DataList } from '../../shared/ui/DataList/DataList';
import { Pager } from '../../shared/ui/Pager/Pager';
import { Skeleton } from '../../shared/ui/Skeleton/Skeleton';
import { SwipeRow } from '../../shared/ui/SwipeRow/SwipeRow';
import { usePagination } from '../../shared/lib/pagination';
import { toErrorMessage } from '../../shared/lib/errors';
import { useTopics } from '../../shared/taxonomy/useTopics';
import { getTopicLabel } from '../../shared/taxonomy/labels';
import formStyles from '../../shared/styles/forms.module.css';
import listStyles from '../../shared/styles/lists.module.css';
import utils from '../../shared/styles/utils.module.css';
import styles from './QuestionBankView.module.css';
import { BankQuestion, bankApi } from './bankApi';
import { QuestionDetailSheet } from './QuestionDetailSheet';
import { QuestionEditSheet } from './QuestionEditSheet';
import { SchemaViewer } from './SchemaViewer';

const DEFAULT_PAGE_SIZE = 5;
const PAGE_SIZE_OPTIONS = [5, 10, 20, 50];

/**
 * Question-bank browser: topic filter, swipe rows with Info/Edit/Delete
 * actions, detail in a floating sheet (refreshed from the server on open),
 * two-tap delete, and an edit affordance opening the floating edit sheet.
 * Optional select mode (checkboxes + tap-to-toggle) lets the quiz-prep
 * flow build a match from hand-picked questions. Creation lives in the
 * Crear tab; the JSON contract viewer is admin-only.
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
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const [editing, setEditing] = useState<BankQuestion | null>(null);
  const [detail, setDetail] = useState<BankQuestion | null>(null);
  const [openSwipeId, setOpenSwipeId] = useState<string | null>(null);

  const load = useCallback(async (t: string, off: number, size: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await bankApi.listQuestions({
        topic: t || undefined,
        limit: size,
        offset: off,
      });
      setQuestions(res.questions || []);
      setTotal(res.total ?? 0);
    } catch (err: unknown) {
      setError(toErrorMessage(err, 'Error al cargar preguntas'));
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
      setError(toErrorMessage(err, 'Error al actualizar el detalle'));
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
      setNotice('Pregunta eliminada.');
      if (detail?.id === id) setDetail(null);
      // A deleted question must not stay counted as selected.
      if (selectable && selectedIds.includes(id)) onToggleSelect?.(id);
      load(topic, offset, pageSize);
    } catch (err: unknown) {
      setError(toErrorMessage(err, 'Error al eliminar'));
    }
  };

  const handleDelete = async (id: string) => {
    if (confirmDelete !== id) {
      setConfirmDelete(id);
      return;
    }
    await handleDeleteCommit(id);
  };

  const handleSavedEdit = (id: string) => {
    setEditing(null);
    setOpenSwipeId(null);
    setNotice(`Pregunta actualizada (${id}).`);
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

      {error && (
        <div className={formStyles.errorBanner} id="bankErr">
          {error}
        </div>
      )}
      {notice && (
        <div className={formStyles.alert} id="bankNote">
          {notice}
        </div>
      )}

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
            <div
              key={q.id}
              role="listitem"
              className={selectable ? styles.selectRow : undefined}
            >
              {selectable && (
                <input
                  type="checkbox"
                  checked={selectedIds.includes(q.id)}
                  onChange={() => onToggleSelect?.(q.id)}
                  aria-label={`Elegir pregunta ${q.id}`}
                  className={styles.selectCheck}
                />
              )}
              <div className={utils.grow}>
              <SwipeRow
                ariaLabel={`Pregunta ${q.id}`}
                open={openSwipeId === q.id}
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
                actions={[
                  {
                    key: 'info',
                    label: 'Info',
                    ariaLabel: `Ver detalle pregunta ${q.id}`,
                    icon: <Eye aria-hidden />,
                    onActivate: () => {
                      void handleOpenDetail(q);
                    },
                  },
                  {
                    key: 'edit',
                    label: 'Editar',
                    ariaLabel: `Editar pregunta ${q.id}`,
                    icon: <Pencil aria-hidden />,
                    onActivate: () => setEditing(q),
                  },
                  {
                    key: 'delete',
                    label: confirmDelete === q.id ? '¿Confirmar?' : 'Eliminar',
                    icon: <Trash2 aria-hidden />,
                    tone: 'danger',
                    onActivate: () => void handleDelete(q.id),
                  },
                ]}
              >
                <button
                  type="button"
                  className={`${listStyles.studentName} ${styles.faceButton}`}
                  onClick={() => handleFaceTap(q)}
                >
                  {q.question_text}
                </button>
                <span
                  className={`${listStyles.roleTag} ${styles.topicTag}`}
                >
                  {getTopicLabel(q.topic)}
                </span>
              </SwipeRow>
              </div>
            </div>
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

      {isAdmin && <SchemaViewer onError={setError} />}

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
