import React, { useEffect, useState } from 'react';
import { Check } from 'lucide-react';
import { generatorApi } from '../question-generator/generatorApi';
import { TopicModel } from '../question-generator/generator.types';
import {
  getMisconceptionLabel,
  getSubconceptLabel,
  getTopicLabel,
} from '../question-generator/TopicSelector';
import rosterStyles from '../roster/roster.module.css';
import formStyles from './QuestionForm.module.css';
import { BankQuestion, BankQuestionCreate, bankApi } from './bankApi';

const OPTION_KEYS = ['A', 'B', 'C', 'D'] as const;

interface DraftDistractor {
  misconception: string;
  explanation: string;
}

export interface QuestionFormProps {
  /** Null = create mode; set = edit mode. */
  initial: BankQuestion | null;
  onSaved: (id: string, edited: boolean) => void;
  onCancel?: () => void;
}

/**
 * Manual question editor: topic/subconcept/text/options/correct/distractors
 * with a standalone `POST /quiz/validate` pre-check before saving.
 * Used inline (Crear tab) and inside the edit sheet — same behaviour.
 */
export const QuestionForm: React.FC<QuestionFormProps> = ({
  initial,
  onSaved,
  onCancel,
}) => {
  const [topics, setTopics] = useState<TopicModel[]>([]);
  const [fTopic, setFTopic] = useState(initial?.topic || '');
  const [fSubconcept, setFSubconcept] = useState(initial?.subconcept || '');
  const [fText, setFText] = useState(initial?.question_text || '');
  const [fOptions, setFOptions] = useState<Record<string, string>>(
    initial ? { ...initial.options } : { A: '', B: '', C: '', D: '' }
  );
  const [fCorrect, setFCorrect] = useState<string>(
    initial?.correct_option || 'A'
  );
  const [fDistractors, setFDistractors] = useState<
    Record<string, DraftDistractor>
  >(() => {
    const d: Record<string, DraftDistractor> = {};
    for (const [k, v] of Object.entries(initial?.distractors || {})) {
      d[k] = { misconception: v.misconception, explanation: v.explanation };
    }
    return d;
  });
  const [validation, setValidation] = useState<string[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const editingId = initial?.id || null;

  useEffect(() => {
    generatorApi
      .getTopics()
      .then((t) => setTopics(Array.isArray(t) ? t : []))
      .catch(() => {});
  }, []);

  // Keep create and edit in sync: when the edited question changes
  // (or we switch between Crear/null and Editar/question), reset all
  // fields so both modes always start from the same treatment.
  useEffect(() => {
    setFTopic(initial?.topic || '');
    setFSubconcept(initial?.subconcept || '');
    setFText(initial?.question_text || '');
    setFOptions(
      initial ? { ...initial.options } : { A: '', B: '', C: '', D: '' }
    );
    setFCorrect(initial?.correct_option || 'A');
    const d: Record<string, DraftDistractor> = {};
    for (const [k, v] of Object.entries(initial?.distractors || {})) {
      d[k] = { misconception: v.misconception, explanation: v.explanation };
    }
    setFDistractors(d);
    setValidation(null);
    setError(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initial?.id]);

  const distractorKeys = OPTION_KEYS.filter((k) => k !== fCorrect);

  // Taxonomy-driven options: subconcepts of the chosen topic, and the
  // diagnosed misconception slugs of the chosen subconcept.
  const subconceptOptions =
    topics.find((t) => t.name === fTopic)?.subconcepts ?? [];
  const misconceptionOptions =
    subconceptOptions.find((s) => s.name === fSubconcept)?.misconceptions ??
    [];

  const handleTopicChange = (name: string) => {
    setFTopic(name);
    const subs =
      topics.find((t) => t.name === name)?.subconcepts ?? [];
    if (!subs.some((s) => s.name === fSubconcept)) setFSubconcept('');
  };

  const buildDraft = (): BankQuestion => {
    const distractors: Record<string, DraftDistractor> = {};
    for (const k of distractorKeys) {
      distractors[k] = fDistractors[k] || { misconception: '', explanation: '' };
    }
    return {
      id: editingId || 'manual-draft',
      topic: fTopic,
      subconcept: fSubconcept,
      question_text: fText,
      options: { ...fOptions },
      correct_option: fCorrect,
      distractors: distractors as BankQuestion['distractors'],
    };
  };

  const handleValidate = async () => {
    setValidation(null);
    setError(null);
    try {
      const res = await bankApi.validateQuestion(buildDraft());
      setValidation(
        res.is_valid ? ['Válida: cálculo y distractores correctos'] : res.errors
      );
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Error al validar');
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload: BankQuestionCreate = { ...buildDraft(), id: editingId };
      const saved = editingId
        ? await bankApi.updateQuestion(editingId, payload)
        : await bankApi.createQuestion(payload);
      onSaved(saved.id, Boolean(editingId));
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={formStyles.form} id={editingId ? 'bankEdit' : 'bankCreate'}>
      <div className={rosterStyles.rowb}>
        <b>{editingId ? 'Editar pregunta' : 'Nueva pregunta'}</b>
        {onCancel && (
          <button
            type="button"
            className={rosterStyles.toggleLink}
            onClick={onCancel}
          >
            Cancelar
          </button>
        )}
      </div>
      {error && <div className={rosterStyles.errorBanner}>{error}</div>}
      <div className={formStyles.row}>
        <select
          className={`${formStyles.input} ${formStyles.grow}`}
          value={fTopic}
          onChange={(e) => handleTopicChange(e.target.value)}
          aria-label="Tema"
        >
          <option value="">Tema…</option>
          {fTopic && !topics.some((t) => t.name === fTopic) && (
            <option value={fTopic}>{getTopicLabel(fTopic)}</option>
          )}
          {topics.map((t) => (
            <option key={t.name} value={t.name}>
              {t.label || getTopicLabel(t.name)}
            </option>
          ))}
        </select>
        <select
          className={`${formStyles.input} ${formStyles.grow}`}
          value={fSubconcept}
          onChange={(e) => setFSubconcept(e.target.value)}
          aria-label="Subconcepto"
        >
          <option value="">Subconcepto…</option>
          {fSubconcept &&
            !subconceptOptions.some((s) => s.name === fSubconcept) && (
              <option value={fSubconcept}>
                {getSubconceptLabel(fSubconcept) || fSubconcept}
              </option>
            )}
          {subconceptOptions.map((s) => (
            <option key={s.name} value={s.name}>
              {getSubconceptLabel(s.name) || s.name}
            </option>
          ))}
        </select>
      </div>
      <textarea
        className={`${formStyles.input} ${formStyles.textarea}`}
        maxLength={500}
        placeholder="Enunciado"
        value={fText}
        onChange={(e) => setFText(e.target.value)}
      />
      <fieldset className={formStyles.group}>
        <legend className={formStyles.legend}>
          Opciones <span className={formStyles.hint}>— marca la correcta</span>
        </legend>
        {OPTION_KEYS.map((k) => {
          const isCorrect = fCorrect === k;
          return (
            <div
              className={`${formStyles.option} ${isCorrect ? formStyles.optionCorrect : ''}`}
              key={k}
            >
              <label className={formStyles.pick} title="Marca la correcta">
                <input
                  type="radio"
                  className={formStyles.radio}
                  name={`correcta-${editingId ?? 'nueva'}`}
                  checked={isCorrect}
                  onChange={() => setFCorrect(k)}
                  aria-label={`Correcta ${k}`}
                />
                <span className={formStyles.letter} aria-hidden="true">
                  {k}
                </span>
              </label>
              <input
                className={`${formStyles.input} ${formStyles.grow}`}
                placeholder={`Opción ${k}`}
                aria-label={`Opción ${k}`}
                value={fOptions[k]}
                onChange={(e) =>
                  setFOptions((prev) => ({ ...prev, [k]: e.target.value }))
                }
              />
              {isCorrect && (
                <span className={formStyles.correctBadge} title="Respuesta correcta">
                  <Check size={18} aria-hidden />
                </span>
              )}
            </div>
          );
        })}
      </fieldset>
      <fieldset className={formStyles.group}>
        <legend className={formStyles.legend}>
          Errores frecuentes <span className={formStyles.hint}>— solo distractoras</span>
        </legend>
      {distractorKeys.map((k) => {
        const currentMisc = fDistractors[k]?.misconception || '';
        const setMisc = (misconception: string) =>
          setFDistractors((prev) => ({
            ...prev,
            [k]: {
              misconception,
              explanation: prev[k]?.explanation || '',
            },
          }));
        return (
        <div className={formStyles.distractor} key={`d-${k}`}>
          <div className={formStyles.distractorHead} aria-hidden="true">
            <span className={formStyles.letterSm}>{k}</span>
          </div>
          <div className={formStyles.row}>
          {misconceptionOptions.length > 0 ? (
            <select
              className={`${formStyles.input} ${formStyles.misc}`}
              value={currentMisc}
              onChange={(e) => setMisc(e.target.value)}
              aria-label={`Error ${k}`}
            >
              <option value="">Error {k}…</option>
              {currentMisc && !misconceptionOptions.includes(currentMisc) && (
                <option value={currentMisc}>
                  {getMisconceptionLabel(currentMisc)}
                </option>
              )}
              {misconceptionOptions.map((m) => (
                <option key={m} value={m}>
                  {getMisconceptionLabel(m)}
                </option>
              ))}
            </select>
          ) : (
            <input
              className={`${formStyles.input} ${formStyles.misc}`}
              maxLength={100}
              placeholder={`Error ${k}`}
              aria-label={`Error ${k}`}
              value={currentMisc}
              onChange={(e) => setMisc(e.target.value)}
            />
          )}
          <input
            className={`${formStyles.input} ${formStyles.explain}`}
            maxLength={500}
            placeholder={`Por qué se equivocan en ${k}`}
            value={fDistractors[k]?.explanation || ''}
            onChange={(e) =>
              setFDistractors((prev) => ({
                ...prev,
                [k]: {
                  misconception: prev[k]?.misconception || '',
                  explanation: e.target.value,
                },
              }))
            }
          />
        </div>
        </div>
        );
      })}
      </fieldset>
      {validation && (
        <div className={rosterStyles.alert} id="bankValidation">
          {validation.map((v, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {v.startsWith('Válida:') ? <Check size={16} aria-hidden /> : null}
              <span>{v}</span>
            </div>
          ))}
        </div>
      )}
      <div className={formStyles.actions}>
        <button
          type="button"
          className={formStyles.button}
          onClick={handleValidate}
          disabled={saving}
        >
          Validar
        </button>
        <button
          type="button"
          className={formStyles.button}
          onClick={handleSave}
          disabled={saving}
        >
          {editingId ? 'Guardar cambios' : 'Guardar'}
        </button>
      </div>
    </div>
  );
};
