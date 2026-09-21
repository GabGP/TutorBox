import { useEffect, useState } from 'react';
import { OPTION_LETTERS } from '../../shared/constants/options';
import { toErrorMessage } from '../../shared/lib/errors';
import { useTopics } from '../../shared/taxonomy/useTopics';
import { BankQuestion, BankQuestionCreate, bankApi } from './bankApi';

export interface DraftDistractor {
  misconception: string;
  explanation: string;
}

function emptyDistractors(
  source?: Record<string, { misconception: string; explanation: string }> | null
): Record<string, DraftDistractor> {
  const d: Record<string, DraftDistractor> = {};
  for (const [k, v] of Object.entries(source || {})) {
    d[k] = { misconception: v.misconception, explanation: v.explanation };
  }
  return d;
}

/**
 * Field state behind QuestionForm: taxonomy/text/options/correct/distractor
 * draft synced from `initial`, taxonomy-driven option lists, draft building,
 * and the standalone validate + save flows.
 */
export function useQuestionFormState(
  initial: BankQuestion | null,
  onSaved: (id: string, edited: boolean) => void
) {
  const { topics } = useTopics();
  const [fTopic, setFTopic] = useState(initial?.topic || '');
  const [fSubconcept, setFSubconcept] = useState(initial?.subconcept || '');
  const [fText, setFText] = useState(initial?.question_text || '');
  const [fOptions, setFOptions] = useState<Record<string, string>>(
    initial ? { ...initial.options } : { A: '', B: '', C: '', D: '' }
  );
  const [fCorrect, setFCorrect] = useState<string>(
    initial?.correct_option || 'A'
  );
  const [fDistractors, setFDistractors] = useState<Record<string, DraftDistractor>>(() =>
    emptyDistractors(initial?.distractors)
  );
  const [validation, setValidation] = useState<string[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const editingId = initial?.id || null;

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
    setFDistractors(emptyDistractors(initial?.distractors));
    setValidation(null);
    setError(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initial?.id]);

  const distractorKeys = OPTION_LETTERS.filter((k) => k !== fCorrect);

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

  const setDistractorMisc = (key: string, misconception: string) =>
    setFDistractors((prev) => ({
      ...prev,
      [key]: {
        misconception,
        explanation: prev[key]?.explanation || '',
      },
    }));

  const setDistractorExplanation = (key: string, explanation: string) =>
    setFDistractors((prev) => ({
      ...prev,
      [key]: {
        misconception: prev[key]?.misconception || '',
        explanation,
      },
    }));

  const setOptionText = (key: string, text: string) =>
    setFOptions((prev) => ({ ...prev, [key]: text }));

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
      setError(toErrorMessage(err, 'Error al validar'));
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
      setError(toErrorMessage(err, 'Error al guardar'));
    } finally {
      setSaving(false);
    }
  };

  return {
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
    error,
    saving,
    setFTopic,
    setFSubconcept,
    setFText,
    setFCorrect,
    setOptionText,
    setDistractorMisc,
    setDistractorExplanation,
    handleTopicChange,
    handleValidate,
    handleSave,
  };
}

export type QuestionFormState = ReturnType<typeof useQuestionFormState>;
