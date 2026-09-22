import React from 'react';
import { Check } from 'lucide-react';
import {
  getSubconceptLabel,
  getTopicLabel,
} from '../../shared/taxonomy/labels';
import sharedForms from '../../shared/styles/forms.module.css';
import listStyles from '../../shared/styles/lists.module.css';
import utils from '../../shared/styles/utils.module.css';
import { ToastViewport } from '../../shared/ui/Toast/ToastViewport';
import { DistractorEditor } from './DistractorEditor';
import { OptionEditor } from './OptionEditor';
import formStyles from './QuestionForm.module.css';
import { BankQuestion } from './bankApi';
import { useQuestionFormState } from './useQuestionFormState';

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
 * Field state lives in useQuestionFormState; option and distractor groups
 * render through OptionEditor and DistractorEditor.
 */
export const QuestionForm: React.FC<QuestionFormProps> = ({
  initial,
  onSaved,
  onCancel,
}) => {
  const form = useQuestionFormState(initial, onSaved);
  const {
    topics,
    editingId,
    fTopic,
    fSubconcept,
    fText,
    fOptions,
    fCorrect,
    fDistractors,
    distractorKeys,
    subconceptOptions,
    misconceptionOptions,
    validation,
    toasts,
    dismissToast,
    saving,
  } = form;

  return (
    <div className={formStyles.form} id={editingId ? 'bankEdit' : 'bankCreate'}>
      <div className={listStyles.rowb}>
        <b>{editingId ? 'Editar pregunta' : 'Nueva pregunta'}</b>
        {onCancel && (
          <button
            type="button"
            className={sharedForms.toggleLink}
            onClick={onCancel}
          >
            Cancelar
          </button>
        )}
      </div>
      <ToastViewport toasts={toasts} onDismiss={(id) => dismissToast(id)} />
      <div className={formStyles.row}>
        <select
          className={`${formStyles.input} ${formStyles.grow}`}
          value={fTopic}
          onChange={(e) => form.handleTopicChange(e.target.value)}
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
          onChange={(e) => form.setFSubconcept(e.target.value)}
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
        onChange={(e) => form.setFText(e.target.value)}
      />
      <OptionEditor
        options={fOptions}
        correct={fCorrect}
        editingId={editingId}
        onCorrectChange={form.setFCorrect}
        onOptionChange={form.setOptionText}
      />
      <DistractorEditor
        distractorKeys={distractorKeys}
        distractors={fDistractors}
        misconceptionOptions={misconceptionOptions}
        onMiscChange={form.setDistractorMisc}
        onExplanationChange={form.setDistractorExplanation}
      />
      {validation && (
        <div className={sharedForms.alert} id="bankValidation">
          {validation.map((v, i) => (
            // eslint-disable-next-line react/no-array-index-key
            <div key={i} className={utils.rowInline6}>
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
          onClick={form.handleValidate}
          disabled={saving}
        >
          Validar
        </button>
        <button
          type="button"
          className={formStyles.button}
          onClick={form.handleSave}
          disabled={saving}
        >
          {editingId ? 'Guardar cambios' : 'Guardar'}
        </button>
      </div>
    </div>
  );
};
