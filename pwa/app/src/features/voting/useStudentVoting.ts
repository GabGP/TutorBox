import { useCallback, useEffect, useRef, useState } from 'react';
import type { OptionLetter } from '../../shared/constants/options';
import { storage } from '../../shared/lib/storage';
import { votingApi } from './votingApi';

/**
 * Custom React hook for managing student voting actions and score tracking.
 * Records latency timestamps, invokes tactile haptic feedback, submits single votes per round,
 * enforces first-press client locking, and persists round hits to localStorage.
 *
 * @param {string | null} sessionId - Currently active session ID.
 * @param {string | null} roundId - Currently active round ID.
 * @returns {object} Vote records, hits dictionary, vote submission method, and cumulative score.
 */
export function useStudentVoting(
  sessionId: string | null,
  roundId: string | null,
  onUnauthorized?: () => void
) {
  const [votes, setVotes] = useState<Record<string, OptionLetter>>({});
  const [hits, setHits] = useState<Record<string, boolean>>({});
  const [pendingVote, setPendingVote] = useState<OptionLetter | null>(null);

  const shownAtRef = useRef<number>(performance.now());
  const currentRoundRef = useRef<string | null>(roundId);

  const persistVotes = useCallback(
    (nextVotes: Record<string, OptionLetter>) => {
      // Only called on paths where sessionId is already guarded non-null.
      setVotes(nextVotes);
      storage.setStudentVotes(sessionId as string, { votes: nextVotes, hits });
    },
    [sessionId, hits]
  );

  // Sync stored votes and hits when session ID changes
  useEffect(() => {
    if (!sessionId) {
      setVotes({});
      setHits({});
      return;
    }
    const stored = storage.getStudentVotes(sessionId);
    setVotes(stored.votes || {});
    setHits(stored.hits || {});
  }, [sessionId]);

  // Track question display timestamp for response latency profiling
  useEffect(() => {
    if (roundId && roundId !== currentRoundRef.current) {
      shownAtRef.current = performance.now();
      currentRoundRef.current = roundId;
      setPendingVote(null);
    }
  }, [roundId]);

  const castVote = useCallback(
    async (option: OptionLetter) => {
      if (!sessionId || !roundId || pendingVote || votes[roundId]) {
        return;
      }

      setPendingVote(option);
      if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
        try {
          navigator.vibrate?.(15);
        } catch {
          // Ignore vibration permissions error
        }
      }

      const responseTimeMs = Math.round(performance.now() - shownAtRef.current);

      try {
        await votingApi.submitVote(sessionId, {
          selected_option: option,
          transport_type: 'web',
          response_time_ms: responseTimeMs,
        });

        persistVotes({ ...votes, [roundId]: option });
      } catch (err: unknown) {
        const e = err as { status?: number };
        if (e.status === 401 && onUnauthorized) {
          onUnauthorized();
        } else if (e.status === 409) {
          // 409 = already voted or window closed: record locally so the screen advances to sent
          persistVotes({ ...votes, [roundId]: option });
        }
      } finally {
        setPendingVote(null);
      }
    },
    [sessionId, roundId, pendingVote, votes, hits, persistVotes, onUnauthorized]
  );

  const recordHit = useCallback(
    (targetRoundId: string, isHit: boolean) => {
      if (!sessionId) return;
      setHits((prevHits) => {
        if (targetRoundId in prevHits) return prevHits;
        const updated = { ...prevHits, [targetRoundId]: isHit };
        storage.setStudentVotes(sessionId, { votes, hits: updated });
        return updated;
      });
    },
    [sessionId, votes]
  );

  const score = Object.values(hits).filter(Boolean).length;
  // Single cast at the source: the JSON-backed record may lack the key.
  const roundVote = roundId
    ? ((votes[roundId] as OptionLetter | undefined) ?? null)
    : null;
  const currentVote: OptionLetter | null = roundVote ?? pendingVote;

  return {
    votes,
    hits,
    pendingVote,
    currentVote,
    castVote,
    recordHit,
    score,
  };
}
