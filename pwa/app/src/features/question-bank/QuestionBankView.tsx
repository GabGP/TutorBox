import React, { useCallback, useEffect, useState } from 'react';
import { Eye, Pencil, Trash2 } from 'lucide-react';
import { DataList } from '../../shared/ui/DataList/DataList';
import { Pagination } from '../../shared/ui/Pagination/Pagination';
import { Skeleton } from '../../shared/ui/Skeleton/Skeleton';
import { SwipeRow } from '../../shared/ui/SwipeRow/SwipeRow';
import { generatorApi } from '../question-generator/generatorApi';
import { TopicModel } from '../question-generator/generator.types';
import { getTopicLabel } from '../../shared/taxonomy/labels';
import formStyles from '../../shared/styles/forms.module.css';
import listStyles from '../../shared/styles/lists.module.css';
import { BankQuestion, bankApi } from './bankApi';
import { QuestionDetailSheet } from './QuestionDetailSheet';
import { QuestionEditSheet } from './QuestionEditSheet';

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
  const [topics, setTopics] = useState<TopicModel[]>([]);
  const [topic, setTopic] = useState(initialTopic);
  const [questions, setQuestions] = useState<BankQuestion[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const [editing, setEditing] = useState<BankQuestion | null>(null);
  const [detail, setDetail] = useState<BankQuestion | null>(null);
  const [openSwipeId, setOpenSwipeId] = useState<string | null>(null);
  const [schema, setSchema] = useState<string | null>(null);

  useEffect(() => {
    generatorApi
      .getTopics()
      .then((t) => setTopics(Array.isArray(t) ? t : []))
      .catch(() => {});
  }, []);

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
      const e = err as { message?: string };
      setError(e.message || 'Error al cargar preguntas');
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
    } catch {
      // Keep list data on network errors
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
      const e = err as { message?: string };
      setError(e.message || 'Error al eliminar');
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

  const toggleSchema = async () => {
    if (schema !== null) {
      setSchema(null);
      return;
    }
    try {
      const s = await bankApi.getSchema();
      setSchema(JSON.stringify(s, null, 2));
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Error al cargar esquema');
    }
  };

  const page = Math.floor(offset / pageSize) + 1;
  const pages = Math.max(1, Math.ceil(total / pageSize));

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
          className={formStyles.addInput}
          style={{ flex: 1 }}
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
              style={{
                padding: '10px 12px',
                display: 'flex',
                gap: '10px',
                alignItems: 'center',
              }}
            >
              <Skeleton style={{ flex: 1, height: '18px' }} />
              <Skeleton
                style={{ width: '64px', height: '22px', borderRadius: '12px' }}
              />
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
              style={
                selectable
                  ? {
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      paddingLeft: '12px',
                    }
                  : undefined
              }
            >
              {selectable && (
                <input
                  type="checkbox"
                  checked={selectedIds.includes(q.id)}
                  onChange={() => onToggleSelect?.(q.id)}
                  aria-label={`Elegir pregunta ${q.id}`}
                  style={{ flex: '0 0 auto' }}
                />
              )}
              <div style={{ flex: 1, minWidth: 0 }}>
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
                  className={listStyles.studentName}
                  onClick={() => handleFaceTap(q)}
                  style={{
                    cursor: 'pointer',
                    textAlign: 'left',
                    minWidth: 0,
                  }}
                >
                  {q.question_text}
                </button>
                <span
                  className={listStyles.roleTag}
                  style={{ minWidth: '84px', textAlign: 'center' }}
                >
                  {getTopicLabel(q.topic)}
                </span>
              </SwipeRow>
              </div>
            </div>
          ))}
        </DataList>
      )}

      <Pagination
        id="bankPager"
        page={page}
        pages={pages}
        pageSize={pageSize}
        pageSizeOptions={PAGE_SIZE_OPTIONS}
        onPrev={() => setOffset((o) => Math.max(0, o - pageSize))}
        onNext={() => setOffset((o) => o + pageSize)}
        onFirst={() => setOffset(0)}
        onLast={() => setOffset((pages - 1) * pageSize)}
        onPageSizeChange={(size) => {
          setPageSize(size);
          setOffset(0);
        }}
        disabled={loading}
      />

      {isAdmin && (
        <details>
          <summary
            style={{ color: 'var(--p)', fontWeight: 600, cursor: 'pointer' }}
            onClick={toggleSchema}
          >
            Contrato JSON de preguntas
          </summary>
          {schema && (
            <>
              <p style={{ fontSize: '13px', color: 'var(--mute2)', margin: '8px 0' }}>
                Esquema oficial que debe cumplir cada pregunta del banco (el generador
                y la validación lo usan para aceptar o rechazar preguntas).
              </p>
              <pre
                style={{
                  whiteSpace: 'pre-wrap',
                  fontSize: '12px',
                  background: 'var(--chip)',
                  borderRadius: '16px',
                  padding: '12px',
                }}
              >
                {schema}
              </pre>
            </>
          )}
        </details>
      )}

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
