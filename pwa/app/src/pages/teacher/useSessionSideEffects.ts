import { useEffect, useRef, useState } from 'react';
import {
  SessionModel,
  SessionReport,
} from '../../features/session-engine/session.types';
import { sessionApi } from '../../features/session-engine/sessionApi';
import { StoredRoundHistory, storage } from '../../shared/lib/storage';

interface UseSessionSideEffectsOptions {
  sid: string | null;
  session: SessionModel | null;
  setSession: (session: SessionModel | null) => void;
  unloadIfLoaded: () => Promise<unknown>;
}

/**
 * Reactive session side effects for the teacher flow: clears vanished
 * sessions (404), reloads persisted round history per session, auto-closes
 * expired rounds, persists revealed rounds to history, and unloads TTS +
 * fetches the report on completion. Owns the history/report states.
 */
export function useSessionSideEffects({
  sid,
  session,
  setSession,
  unloadIfLoaded,
}: UseSessionSideEffectsOptions) {
  const [history, setHistory] = useState<StoredRoundHistory[]>([]);
  const [report, setReport] = useState<SessionReport | null>(null);
  const closingRef = useRef<string | null>(null);

  useEffect(() => {
    if (sid) setHistory(storage.getRoundHistory(sid));
  }, [sid]);

  // Handle auto clock-out, history persistence, and TTS unload on completion
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
        sessionApi.closeRound(sid).then(setSession).catch(() => {});
      }
    }
    if (sid && round && round.status === 'revealed' && round.result && round.question) {
      setHistory((prev) => {
        if (prev.some((h) => h.round_id === round.round_id)) return prev;
        const item: StoredRoundHistory = {
          round_id: round.round_id,
          text: round.question!.question_text,
          options: round.question!.options,
          tally: round.result!.tally,
          explanations: round.result!.explanations,
        };
        const next = [...prev, item];
        storage.setRoundHistory(sid, next);
        return next;
      });
    }
    if (sid && session?.status === 'completed') {
      void unloadIfLoaded();
      if (!report) {
        sessionApi.getSessionReport(sid).then(setReport).catch(() => {});
      }
    }
  }, [session, sid, report, setSession, unloadIfLoaded]);

  return { history, setHistory, report, setReport };
}

/**
 * Clears a vanished (404) teacher session. Kept separate so the coordinator
 * wires the engine error to sid cleanup in one place.
 */
export function useVanishedSessionEffect(
  sid: string | null,
  status: number | undefined,
  setSid: (sid: string | null) => void,
  setSession: (session: SessionModel | null) => void
) {
  useEffect(() => {
    if (sid && status === 404) {
      storage.clearTeacherSessionId();
      setSid(null);
      setSession(null);
    }
  }, [sid, status, setSid, setSession]);
}
