import React, { useState } from 'react';
import { Check, Minus, Plus } from 'lucide-react';
import { OPTION_LETTERS } from '../../shared/constants/options';
import { toErrorMessage } from '../../shared/lib/errors';
import { getMisconceptionLabel } from '../../shared/taxonomy/labels';
import styles from './BankQuestionInlineEditor.module.css';
import { BankQuestion, bankApi } from './bankApi';

export interface BankQuestionInlineEditorProps {
  question: BankQuestion;
  selected: boolean;
  onToggleSelect: (id: string) => void;
  onSaved: (saved: BankQuestion) => void;
  onError: (message: string) => void;
}

function explanationsOf(question: BankQuestion): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [k, d] of Object.entries(question.distractors || {})) {
    out[k] = d.explanation;
  }
  return out;
}

/**
 * Expanded bank row in the quiz-prep picker: the four options, each with
 * its distractor explanation, edited in place and saved straight back to
 * the bank (`PUT /quiz/questions/{id}`). The correct letter, taxonomy and
 * misconception slugs are kept as stored — the full edit sheet covers
 * those. Selection for the match is an explicit toggle, not a checkbox.
 */
export const BankQuestionInlineEditor: React.FC<BankQuestionInlineEditorProps> = ({
  question,
  selected,
  onToggleSelect,
  onSaved,
  onError,
}) => {
  const [options, setOptions] = useState<Record<string, string>>(() => ({
    ...question.options,
  }));
  const [explanations, setExplanations] = useState<Record<string, string>>(() =>
    explanationsOf(question)
  );
  const [saving, setSaving] = useState(false);

  const original = explanationsOf(question);
  const dirty = OPTION_LETTERS.some(
    (k) =>
      (options[k] ?? '') !== (question.options[k] ?? '') ||
      (explanations[k] ?? '') !== (original[k] ?? '')
  );

  const handleSave = async () => {
    setSaving(true);
    try {
      const distractors: BankQuestion['distractors'] = {};
      for (const [k, d] of Object.entries(question.distractors || {})) {
        distractors[k] = { ...d, explanation: explanations[k] ?? d.explanation };
      }
      const saved = await bankApi.updateQuestion(question.id, {
        id: question.id,
        topic: question.topic,
        subconcept: question.subconcept,
        question_text: question.question_text,
        options: { ...options },
        correct_option: question.correct_option,
        distractors,
      });
      onSaved(saved);
    } catch (err: unknown) {
      onError(toErrorMessage(err, 'Error al guardar'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={styles.panel} id={`bankInline-${question.id}`}>
      {OPTION_LETTERS.map((k) => {
        const isCorrect = k === question.correct_option;
        const misc = question.distractors[k]?.misconception;
        return (
          <div
            key={k}
            className={`${styles.option} ${isCorrect ? styles.optionCorrect : ''}`}
          >
            <div className={styles.head}>
              <span className={styles.letter} aria-hidden="true">
                {k}
              </span>
              <input
                className={styles.input}
                aria-label={`Opción ${k}`}
                placeholder={`Opción ${k}`}
                value={options[k] ?? ''}
                onChange={(e) =>
                  setOptions((prev) => ({ ...prev, [k]: e.target.value }))
                }
              />
              {isCorrect && (
                <span className={styles.correctBadge} title="Respuesta correcta">
                  <Check size={18} aria-hidden />
                </span>
              )}
            </div>
            {isCorrect ? (
              <p className={styles.note}>Respuesta correcta</p>
            ) : (
              <>
                {misc && (
                  <p className={styles.note}>{getMisconceptionLabel(misc)}</p>
                )}
                <textarea
                  className={`${styles.input} ${styles.textarea}`}
                  aria-label={`Explicación ${k}`}
                  placeholder={`Por qué se equivocan en ${k}`}
                  maxLength={500}
                  value={explanations[k] ?? ''}
                  onChange={(e) =>
                    setExplanations((prev) => ({ ...prev, [k]: e.target.value }))
                  }
                />
              </>
            )}
          </div>
        );
      })}
      <div className={styles.actions}>
        <button
          type="button"
          className={`${styles.button} ${selected ? styles.buttonOn : ''}`}
          aria-pressed={selected}
          onClick={() => onToggleSelect(question.id)}
        >
          {selected ? <Minus size={18} aria-hidden /> : <Plus size={18} aria-hidden />}
          {selected ? 'Quitar del juego' : 'Usar en el juego'}
        </button>
        <button
          type="button"
          className={`${styles.button} ${styles.buttonPrimary}`}
          onClick={() => void handleSave()}
          disabled={!dirty || saving}
        >
          {saving ? 'Guardando…' : 'Guardar'}
        </button>
      </div>
    </div>
  );
};
