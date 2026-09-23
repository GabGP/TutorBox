import { useCallback, useState } from 'react';
import { useQuestionGenerator } from '../../features/question-generator/useQuestionGenerator';
import { useTopics } from '../../shared/taxonomy/useTopics';
import { SessionModel } from '../../features/session-engine/session.types';
import { sessionApi } from '../../features/session-engine/sessionApi';
import { useSessionEngine } from '../../features/session-engine/useSessionEngine';
import { ttsApi } from '../../features/speech/speechApi';
import { SpeechLanguage } from '../../features/speech/speech.types';
import { useTTSLifecycle } from '../../features/speech/useTTSLifecycle';
import { unlockAudio } from '../../shared/lib/sound';
import { storage } from '../../shared/lib/storage';
import { useSessionSideEffects, useVanishedSessionEffect } from './useSessionSideEffects';
import { useWizardSelection } from './useWizardSelection';

export type { QuestionSource, TeacherWizardStep } from './useWizardSelection';

interface UseTeacherCoordinatorOptions {
  enabled?: boolean;
  voiceLang?: SpeechLanguage;
}

/** Titles new matches `Pilas <es-date>` with the standard 20s round clock. */
async function createMatchSession(
  topic: string,
  questionIds: string[]
): Promise<SessionModel> {
  const created = await sessionApi.createSession({
    title: `Pilas ${new Date().toLocaleDateString('es')}`,
    topic: topic || 'mixto',
    question_ids: questionIds,
    duration_seconds: 20,
  });
  storage.setTeacherSessionId(created.id);
  return created;
}

/**
 * Single-resident-engine policy: when the teacher saved a voice preference
 * for this language, make sure THAT engine is the one loaded (evicting
 * others); otherwise fall back to engine defaults. Never blocks game start
 * on TTS failures.
 */
async function ensureLobbyVoice(
  voiceLang: SpeechLanguage,
  preloadIfUnloaded: (
    lang: SpeechLanguage,
    engine?: string,
    voice?: string
  ) => Promise<unknown>
): Promise<void> {
  try {
    const pref = storage.getVoicePreference();
    const usePref = pref?.lang === voiceLang ? pref : undefined;
    if (usePref?.engine) {
      const st = await ttsApi.getStatus(usePref.engine, voiceLang).catch(() => null);
      if (!st?.loaded) {
        await ttsApi.unload({}).catch(() => undefined);
        await preloadIfUnloaded(voiceLang, usePref.engine, usePref.voice);
      }
    } else {
      void preloadIfUnloaded(voiceLang);
    }
  } catch {
    // Game starts even if voice setup fails.
  }
}

/**
 * Teacher quiz-master orchestration: wizard selection (useWizardSelection),
 * session engine plus reactive side effects (useSessionSideEffects),
 * question generation, and the primary-action state machine over session
 * status.
 *
 * @param {string | null} initialSid - Optional cached teacher session ID.
 * @param {UseTeacherCoordinatorOptions} [options={}] - Hook options (e.g. enable gating).
 * @returns {object} Full teacher coordinator state, session models, telemetry, and progression actions.
 */
export function useTeacherCoordinator(
  initialSid: string | null,
  { enabled = true, voiceLang = 'es' }: UseTeacherCoordinatorOptions = {}
) {
  const [sid, setSid] = useState<string | null>(initialSid);
  const {
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
  } = useWizardSelection();
  const { topics } = useTopics({ enabled });

  const { session, setSession, error: sessionErr } = useSessionEngine({
    targetSessionId: sid ?? undefined,
    enabled: enabled && Boolean(sid),
  });

  const { progress, isGenerating, error: genError, startGeneration, cancelGeneration } =
    useQuestionGenerator();

  const { preloadIfUnloaded, unloadIfLoaded } = useTTSLifecycle();

  useVanishedSessionEffect(sid, sessionErr?.status, setSid, setSession);
  const { history, setHistory, report, setReport } = useSessionSideEffects({
    sid,
    session,
    setSession,
    unloadIfLoaded,
  });

  const resetSession = useCallback(() => {
    void unloadIfLoaded();
    cancelGeneration();
    setSid(null);
    setSession(null);
    setReport(null);
    setHistory([]);
    resetSelection();
    storage.clearTeacherSessionId();
  }, [cancelGeneration, setSession, setHistory, setReport, resetSelection, unloadIfLoaded]);

  const pregenerate = useCallback(async () => {
    const ids = await startGeneration(topic, count, topics);
    if (ids) {
      ensureBankIds(ids);
    }
    return ids;
  }, [topic, count, topics, startGeneration, ensureBankIds]);

  const advancePrimary = useCallback(async () => {
    if (!session) {
      if (wizard === 'topic') return setWizard('count');
      if (wizard === 'count') {
        if (source === 'bank') {
          if (bankIds.length === 0) return;
          const picked = await createMatchSession(topic, bankIds);
          setSid(picked.id);
          setSession(picked);
          return;
        }
        setWizard('lobby');
        const ids = await startGeneration(topic, count, topics);
        if (!ids) {
          setWizard((cur) => (cur === 'lobby' ? 'count' : cur));
          return;
        }
        const newSession = await createMatchSession(topic, ids);
        setSid(newSession.id);
        setSession(newSession);
      }
      return;
    }

    if (session.status === 'lobby') {
      await ensureLobbyVoice(voiceLang, preloadIfUnloaded);
      const started = await sessionApi.startSession(session.id);
      setSession(started);
    } else if (session.status === 'active') {
      const r = session.current_round;
      if (r?.status === 'open') {
        unlockAudio();
        try {
          const closed = await sessionApi.closeRound(session.id);
          setSession(closed);
        } catch {
          const updated = await sessionApi.getSessionById(session.id);
          setSession(updated);
        }
      } else if (r?.status === 'closed') {
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
  }, [
    session,
    wizard,
    topic,
    count,
    topics,
    voiceLang,
    source,
    bankIds,
    startGeneration,
    setSession,
    preloadIfUnloaded,
    resetSession,
  ]);

  return {
    sid,
    wizard,
    setWizard,
    topic,
    setTopic,
    count,
    setCount,
    topics,
    session,
    progress,
    isGenerating,
    genError,
    history,
    report,
    source,
    setSource,
    bankIds,
    toggleBankId,
    ensureBankIds,
    pregenerate,
    advancePrimary,
    resetSession,
  };
}
