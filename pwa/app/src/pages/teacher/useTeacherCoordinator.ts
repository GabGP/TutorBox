import { useCallback, useState } from 'react';
import { useQuestionGenerator } from '../../features/question-generator/useQuestionGenerator';
import { useQuizModelLifecycle } from '../../features/question-generator/useQuizModelLifecycle';
import { NO_NOTICES, type NoticeSink } from '../../features/model-residency/residencyNotices';
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

export type { TeacherWizardStep } from './useWizardSelection';

interface UseTeacherCoordinatorOptions {
  enabled?: boolean;
  voiceLang?: SpeechLanguage;
  /** Toast queue for the quiz model's load and unload messages. */
  notices?: NoticeSink;
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
 * Ends a lobby or started match on the server, so students and the screen
 * leave it too. A match the server already ended (409) or lost (404) has
 * nothing left to end, so the error is ignored.
 */
async function abandonRunningMatch(session: SessionModel | null): Promise<void> {
  if (!session || (session.status !== 'lobby' && session.status !== 'active')) return;
  try {
    await sessionApi.abandonSession(session.id);
  } catch {
    // Nothing left to cancel on the server; the console moves on anyway.
  }
}

/**
 * Teacher quiz-master orchestration: wizard selection (useWizardSelection),
 * session engine plus reactive side effects (useSessionSideEffects),
 * question generation, and the primary-action state machine over session
 * status.
 *
 * @param {string | null} initialSid - Optional cached teacher session ID.
 * @param {UseTeacherCoordinatorOptions} [options={}] - Hook options (enable gating, voice, toasts).
 * @returns {object} Full teacher coordinator state, session models, telemetry, and progression actions.
 */
export function useTeacherCoordinator(
  initialSid: string | null,
  { enabled = true, voiceLang = 'es', notices = NO_NOTICES }: UseTeacherCoordinatorOptions = {}
) {
  const [sid, setSid] = useState<string | null>(initialSid);
  const {
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
  } = useWizardSelection();
  const { topics } = useTopics({ enabled });

  const { session, setSession, error: sessionErr } = useSessionEngine({
    targetSessionId: sid ?? undefined,
    enabled: enabled && Boolean(sid),
  });

  const quizModel = useQuizModelLifecycle(notices);
  const {
    progress,
    isGenerating,
    isPaused: isGenerationPaused,
    error: genError,
    startGeneration,
    stopGeneration,
    resumeGeneration,
    cancelGeneration,
    clearProgress: clearGenerationResult,
  } = useQuestionGenerator(quizModel);

  const { preloadIfUnloaded, unloadIfLoaded } = useTTSLifecycle();

  useVanishedSessionEffect(sid, sessionErr?.status, setSid, setSession);
  const { history, setHistory, report, setReport } = useSessionSideEffects({
    sid,
    session,
    setSession,
    unloadIfLoaded,
  });

  /** Drops the match from this console; the wizard selection is left as it is. */
  const clearMatch = useCallback(() => {
    void unloadIfLoaded();
    cancelGeneration();
    setSid(null);
    setSession(null);
    setReport(null);
    setHistory([]);
    storage.clearTeacherSessionId();
  }, [cancelGeneration, setSession, setHistory, setReport, unloadIfLoaded]);

  const resetSession = useCallback(() => {
    clearMatch();
    resetSelection();
  }, [clearMatch, resetSelection]);

  /**
   * Cancelar in the lobby or mid-game: the server ends the match first, so
   * students and the screen leave it too, then the console starts over.
   */
  const cancelMatch = useCallback(async () => {
    await abandonRunningMatch(session);
    resetSession();
  }, [session, resetSession]);

  /**
   * Back arrow in the lobby: the match that has not started ends on the
   * server, and the console returns to the bank pick with the same topic and
   * questions still chosen, ready to build the match again.
   */
  const backToBankPick = useCallback(async () => {
    const lobbyTopic = session?.topic;
    await abandonRunningMatch(session);
    clearMatch();
    if (lobbyTopic) setTopic(lobbyTopic);
    setWizard('count');
  }, [session, clearMatch, setTopic, setWizard]);

  /** Cancelar in Generar: the questions already saved stay chosen. */
  const cancelBankGeneration = useCallback(() => {
    const alreadySavedIds = progress?.ids ?? [];
    cancelGeneration();
    if (alreadySavedIds.length > 0) ensureBankIds(alreadySavedIds);
  }, [progress, cancelGeneration, ensureBankIds]);

  const generateIntoBank = useCallback(async () => {
    const ids = await startGeneration(topic, count, topics);
    if (ids) {
      ensureBankIds(ids);
    }
    return ids;
  }, [topic, count, topics, startGeneration, ensureBankIds]);

  const advancePrimary = useCallback(async () => {
    if (!session) {
      if (wizard === 'topic') return setWizard('count');
      if (wizard === 'count' && bankIds.length > 0) {
        const picked = await createMatchSession(topic, bankIds);
        setSid(picked.id);
        setSession(picked);
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
    voiceLang,
    bankIds,
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
    isGenerationPaused,
    stopGeneration,
    resumeGeneration,
    clearGenerationResult,
    genError,
    history,
    report,
    bankIds,
    toggleBankId,
    ensureBankIds,
    generateIntoBank,
    cancelBankGeneration,
    advancePrimary,
    cancelMatch,
    backToBankPick,
    resetSession,
  };
}
