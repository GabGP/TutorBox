import React, { useCallback, useEffect, useState } from 'react';
import { generatorApi } from '../question-generator/generatorApi';
import { TopicModel } from '../question-generator/generator.types';
import rosterStyles from '../roster/roster.module.css';
import { BankQuestion, bankApi } from './bankApi';
import { QuestionEditSheet } from './QuestionEditSheet';

const PAGE_SIZE = 20;
const OPTION_KEYS = ['A', 'B', 'C', 'D'] as const;

/**
 * Question-bank browser: topic filter, tappable rows with inline detail
 * (refreshed from the server on expand), two-tap delete, and an edit
 * affordance opening the floating edit sheet. Optional select mode
 * (checkboxes) lets the quiz-prep flow build a match from hand-picked
 * questions. Creation lives in the Crear tab; the JSON contract viewer
 * is admin-only.
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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const [editing, setEditing] = useState<BankQuestion | null>(null);
  const [schema, setSchema] = useState<string | null>(null);

  useEffect(() => {
    generatorApi
      .getTopics()
      .then((t) => setTopics(Array.isArray(t) ? t : []))
      .catch(() => {});
  }, []);

  const load = useCallback(async (t: string, off: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await bankApi.listQuestions({
        topic: t || undefined,
        limit: PAGE_SIZE,
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
    load(topic, offset);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topic, offset, load, reloadKey]);

  const handleExpand = async (q: BankQuestion) => {
    if (expanded === q.id) {
      setExpanded(null);
      return;
    }
    setExpanded(q.id);
    // Refresh the row from GET /quiz/questions/{id} so edits made
    // elsewhere (or generated content) never show stale.
    try {
      const fresh = await bankApi.getQuestion(q.id);
      setQuestions((prev) => prev.map((x) => (x.id === q.id ? fresh : x)));
    } catch {
      // Keep list data on network errors
    }
  };

  const handleDelete = async (id: string) => {
    if (confirmDelete !== id) {
      setConfirmDelete(id);
      return;
    }
    setConfirmDelete(null);
    try {
      await bankApi.deleteQuestion(id);
      setNotice('Pregunta eliminada.');
      if (expanded === id) setExpanded(null);
      load(topic, offset);
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Error al eliminar');
    }
  };

  const handleSavedEdit = (id: string) => {
    setEditing(null);
    setNotice(`Pregunta actualizada (${id}).`);
    load(topic, offset);
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

  const page = Math.floor(offset / PAGE_SIZE) + 1;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className={rosterStyles.container} id="bank">
      <div className={rosterStyles.rowb}>
        <b>Banco de preguntas</b>
        <span id="bankCount">
          {selectable ? `${selectedIds.length} elegidas · ${total}` : total}
        </span>
      </div>

      <div className={rosterStyles.addForm}>
        <select
          id="bankTopic"
          className={rosterStyles.addInput}
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
              {t.label || t.name}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className={rosterStyles.errorBanner} id="bankErr">
          {error}
        </div>
      )}
      {notice && (
        <div className={rosterStyles.alert} id="bankNote">
          {notice}
        </div>
      )}

      <div className={rosterStyles.rosterList} id="bankList">
        {loading ? (
          <div style={{ color: 'var(--mute)' }}>Cargando…</div>
        ) : questions.length === 0 ? (
          <div style={{ color: 'var(--mute)' }}>
            No hay preguntas para este filtro.
          </div>
        ) : (
          questions.map((q) => (
            <div key={q.id} className={rosterStyles.rosterItem}>
              {selectable && (
                <input
                  type="checkbox"
                  checked={selectedIds.includes(q.id)}
                  onChange={() => onToggleSelect?.(q.id)}
                  aria-label={`Elegir pregunta ${q.id}`}
                />
              )}
              <span
                className={rosterStyles.studentName}
                onClick={() => handleExpand(q)}
                style={{ cursor: 'pointer' }}
              >
                {q.question_text}
              </span>
              <span className={rosterStyles.roleTag}>{q.topic}</span>
              <button
                type="button"
                className={rosterStyles.resetBtn}
                aria-label={`Editar pregunta ${q.id}`}
                onClick={() => setEditing(q)}
              >
                ✏️
              </button>
              <button
                type="button"
                className={rosterStyles.deleteBtn}
                onClick={() => handleDelete(q.id)}
              >
                {confirmDelete === q.id ? '¿Confirmar?' : 'Eliminar'}
              </button>
              {expanded === q.id && (
                <div style={{ flexBasis: '100%', fontSize: '14px' }}>
                  {OPTION_KEYS.map((k) => (
                    <div key={k}>
                      <b>
                        {k}
                        {k === q.correct_option ? ' ✔' : ''}:
                      </b>{' '}
                      {q.options[k]}
                      {k !== q.correct_option && q.distractors[k] && (
                        <span style={{ color: 'var(--mute2)' }}>
                          {' '}
                          — {q.distractors[k].explanation}
                        </span>
                      )}
                    </div>
                  ))}
                  <div style={{ color: 'var(--mute2)', marginTop: '4px' }}>
                    {q.subconcept} · {q.source || ''}{' '}
                    {q.sympy_verified ? '· verificada' : ''}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <div className={rosterStyles.pagerRow}>
        <button
          type="button"
          className={rosterStyles.submitAdd}
          disabled={offset === 0}
          onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
        >
          ← Anterior
        </button>
        <span className={rosterStyles.pagerLabel}>
          {page}/{pages}
        </span>
        <button
          type="button"
          className={rosterStyles.submitAdd}
          disabled={offset + PAGE_SIZE >= total}
          onClick={() => setOffset((o) => o + PAGE_SIZE)}
        >
          Siguiente →
        </button>
      </div>

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
    </div>
  );
};
