import { useCallback, useState } from 'react';

export type TeacherWizardStep = 'topic' | 'count';

/**
 * Wizard selection state for the teacher setup flow (topic -> bank pick; the
 * lobby follows once a session exists) plus the hand-picked bank ids. Pure
 * selection state — session creation and generation live in the coordinator.
 */
export function useWizardSelection() {
  const [wizard, setWizard] = useState<TeacherWizardStep>('topic');
  const [topic, setTopic] = useState('');
  const [count, setCount] = useState(10);
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
    setBankIds([]);
  }, []);

  return {
    wizard,
    setWizard,
    topic,
    setTopic,
    count,
    setCount,
    bankIds,
    toggleBankId,
    ensureBankIds,
    resetSelection,
  };
}
