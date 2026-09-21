import React from 'react';
import { Check } from 'lucide-react';
import { OPTION_LETTERS } from '../../shared/constants/options';
import formStyles from './QuestionForm.module.css';

export interface OptionEditorProps {
  options: Record<string, string>;
  correct: string;
  editingId: string | null;
  onCorrectChange: (key: string) => void;
  onOptionChange: (key: string, text: string) => void;
}

/**
 * Multiple-choice option editor: per-letter text inputs with a radio-group
 * correct-answer picker.
 */
export const OptionEditor: React.FC<OptionEditorProps> = ({
  options,
  correct,
  editingId,
  onCorrectChange,
  onOptionChange,
}) => (
  <fieldset className={formStyles.group}>
    <legend className={formStyles.legend}>
      Opciones <span className={formStyles.hint}>— marca la correcta</span>
    </legend>
    {OPTION_LETTERS.map((k) => {
      const isCorrect = correct === k;
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
              onChange={() => onCorrectChange(k)}
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
            value={options[k]}
            onChange={(e) => onOptionChange(k, e.target.value)}
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
);
