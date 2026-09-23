import { useCallback, useState } from 'react';

export type TeacherWizardStep = 'topic' | 'count' | 'lobby';
export type QuestionSource = 'generate' | 'bank';

/**
 * Wizard selection state for the teacher setup flow (topic -> count -> lobby)
 * plus the question source and hand-picked bank ids. Pure selection state —
 * session creation and generation live in the coordinator.
 */
export function useWizardSelection() {
  const [wizard, setWizard] = useState<TeacherWizardStep>('topic');
  const [topic, setTopic] = useState('');
  const [count, setCount] = useState(10);
  const [source, setSource] = useState<QuestionSource>('generate');
  const [bankIds, setBankIds] = useState<string[]>([]);

  const toggleBankId = useCallback((id: string) => {
    setBankIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }, []);

  const ensureBankIds = useCallback((ids: string[]) => {
    setBankIds((prev) => [...new Set([...prev, ...ids])]);
  }, []);

  const resetSelection = useCallback(() => {
    setWizard('topic');
    setSource('generate');
    setBankIds([]);
  }, []);

  return {
    wizard,
    setWizard,
    topic,
    setTopic,
    count,
    setCount,
    source,
    setSource,
    bankIds,
    toggleBankId,
    ensureBankIds,
    resetSelection,
  };
}
