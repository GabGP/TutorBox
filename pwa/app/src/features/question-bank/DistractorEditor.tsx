import React from 'react';
import { getMisconceptionLabel } from '../../shared/taxonomy/labels';
import formStyles from './QuestionForm.module.css';
import type { DraftDistractor } from './useQuestionFormState';

export interface DistractorEditorProps {
  distractorKeys: string[];
  distractors: Record<string, DraftDistractor>;
  misconceptionOptions: string[];
  onMiscChange: (key: string, misconception: string) => void;
  onExplanationChange: (key: string, explanation: string) => void;
}

/**
 * Distractor misconception editor: per-letter diagnosed-error selector
 * (or free text when the taxonomy has none) plus the why-they-err note.
 */
export const DistractorEditor: React.FC<DistractorEditorProps> = ({
  distractorKeys,
  distractors,
  misconceptionOptions,
  onMiscChange,
  onExplanationChange,
}) => (
  <fieldset className={formStyles.group}>
    <legend className={formStyles.legend}>
      Errores frecuentes <span className={formStyles.hint}>— solo distractoras</span>
    </legend>
    {distractorKeys.map((k) => {
      const currentMisc = distractors[k]?.misconception || '';
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
                onChange={(e) => onMiscChange(k, e.target.value)}
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
                onChange={(e) => onMiscChange(k, e.target.value)}
              />
            )}
            <input
              className={`${formStyles.input} ${formStyles.explain}`}
              maxLength={500}
              placeholder={`Por qué se equivocan en ${k}`}
              value={distractors[k]?.explanation || ''}
              onChange={(e) => onExplanationChange(k, e.target.value)}
            />
          </div>
        </div>
      );
    })}
  </fieldset>
);
