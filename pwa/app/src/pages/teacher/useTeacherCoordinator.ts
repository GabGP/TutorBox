import { useCallback, useEffect, useRef, useState } from 'react';
import { useQuestionGenerator } from '../../features/question-generator/useQuestionGenerator';
import { TopicModel } from '../../features/question-generator/generator.types';
import { generatorApi } from '../../features/question-generator/generatorApi';
import { SessionReport } from '../../features/session-engine/session.types';
import { sessionApi } from '../../features/session-engine/sessionApi';
import { useSessionEngine } from '../../features/session-engine/useSessionEngine';
import { unlockAudio } from '../../shared/lib/sound';
import { StoredRoundHistory, storage } from '../../shared/lib/storage';

export type TeacherWizardStep = 'topic' | 'count' | 'lobby';

interface UseTeacherCoordinatorOptions {
  enabled?: boolean;
}

/**
 * Custom React hook for coordinating the teacher quiz master workflow.
 * Manages wizard progression (topic -> question count -> lobby), initiates LLM generation,
 * orchestrates session transitions (start, close, reveal, next), and aggregates round history.
 *
 * @param {string | null} initialSid - Optional cached teacher session ID.
 * @param {UseTeacherCoordinatorOptions} [options={}] - Hook options (e.g. enable gating).
 * @returns {object} Full teacher coordinator state, session models, telemetry, and progression actions.
 */
export function useTeacherCoordinator(
  initialSid: string | null,
  { enabled = true }: UseTeacherCoordinatorOptions = {}
) {
  const [sid, setSid] = useState<string | null>(initialSid);
  const [wizard, setWizard] = useState<TeacherWizardStep>('topic');
  const [topic, setTopic] = useState('');
  const [count, setCount] = useState(10);
  const [topics, setTopics] = useState<TopicModel[]>([]);
  const [history, setHistory] = useState<StoredRoundHistory[]>([]);
  const [report, setReport] = useState<SessionReport | null>(null);

  const { session, setSession, refresh, error: sessionErr } = useSessionEngine({
    targetSessionId: sid,
    enabled: enabled && Boolean(sid),
  });

  const { progress, isGenerating, error: genError, startGeneration, cancelGeneration } =
    useQuestionGenerator();

  const closingRef = useRef<string | null>(null);

  useEffect(() => {
    if (sid && sessionErr?.status === 404) {
      storage.clearTeacherSessionId();
      setSid(null);
      setSession(null);
    }
  }, [sid, sessionErr, setSession]);

  useEffect(() => {
    if (enabled) {
      generatorApi.getTopics().then(setTopics).catch(() => {});
    }
  }, [enabled]);

  useEffect(() => {
    if (sid) setHistory(storage.getRoundHistory(sid));
  }, [sid]);

  // Handle auto clock-out and history persistence
  useEffect(() => {
    const round = session?.current_round;
    if (
      sid &&
      round &&
      round.status === 'open' &&
      round.time_remaining != null &&
      round.time_remaining <= 0
    ) {
      if (closingRef.current !== round.round_id) {
        closingRef.current = round.round_id;
        sessionApi.closeRound(sid).then(refresh).catch(() => {});
      }
    }
    if (sid && round && round.status === 'revealed' && round.result && round.question) {
      setHistory((prev) => {
        if (prev.some((h) => h.round_id === round.round_id)) return prev;
        const item: StoredRoundHistory = {
          round_id: round.round_id, text: round.question!.question_text,
          options: round.question!.options, tally: round.result!.tally, explanations: round.result!.explanations,
        };
        const next = [...prev, item];
        storage.setRoundHistory(sid, next);
        return next;
      });
    }
    if (sid && session?.status === 'completed' && !report) {
      sessionApi.getSessionReport(sid).then(setReport).catch(() => {});
    }
  }, [session, sid, report, refresh]);

  const advancePrimary = useCallback(async () => {
    if (!session) {
      if (wizard === 'topic') return setWizard('count');
      if (wizard === 'count') {
        setWizard('lobby');
        const ids = await startGeneration(topic, count, topics);
        if (!ids) {
          setWizard((cur) => (cur === 'lobby' ? 'count' : cur));
          return;
        }
        const newSession = await sessionApi.createSession({
          title: `Pilas ${new Date().toLocaleDateString('es')}`,
          topic: topic || 'mixto', question_ids: ids, duration_seconds: 20,
        });
        setSid(newSession.id);
        storage.setTeacherSessionId(newSession.id);
        setSession(newSession);
      }
      return;
    }

    if (session.status === 'lobby') {
      const started = await sessionApi.startSession(session.id);
      setSession(started);
    } else if (session.status === 'active') {
      const r = session.current_round;
      if (r?.status === 'open' || r?.status === 'closed') {
        unlockAudio();
        await sessionApi.revealRound(session.id);
        const updated = await sessionApi.getSessionById(session.id);
        setSession(updated);
      } else if (r?.status === 'revealed') {
        const next = await sessionApi.nextRound(session.id);
        setSession(next);
      }
    } else if (session.status === 'completed') {
      resetSession();
    }
  }, [session, wizard, topic, count, topics, startGeneration, setSession]);

  const resetSession = useCallback(() => {
    cancelGeneration();
    setSid(null);
    setSession(null);
    setReport(null);
    setHistory([]);
    setWizard('topic');
    storage.clearTeacherSessionId();
  }, [cancelGeneration, setSession]);

  return {
    sid, wizard, setWizard, topic, setTopic, count, setCount,
    topics, session, progress, isGenerating, genError, history,
    report, advancePrimary, resetSession,
  };
}
