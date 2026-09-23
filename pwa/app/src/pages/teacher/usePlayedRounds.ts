import { useCallback, useEffect, useState } from 'react';
import { getSpeechVoiceKey } from '../../features/speech/speechApi';
import type { SpeechLanguage } from '../../features/speech/speech.types';

/**
 * Autoplay guard for teacher speech: remembers which round indexes already
 * spoke (survives remounts such as opening/closing settings) and the
 * manually-skipped round. Resets when the session or the saved voice changes
 * so a new voice re-runs through the preparation stage.
 */
export function usePlayedRounds(sid: string | null, voiceLang: SpeechLanguage) {
  const [playedRounds, setPlayedRounds] = useState<number[]>([]);
  const [voiceDone, setVoiceDone] = useState(-1);
  const activeVoiceKey = getSpeechVoiceKey(voiceLang);
  const [prevVoiceKey, setPrevVoiceKey] = useState(activeVoiceKey);

  const reset = useCallback(() => {
    setPlayedRounds([]);
    setVoiceDone(-1);
  }, []);

  // When the saved voice changes, allow this round to speak again with the
  // new voice: clear the played guard so autoplay re-runs through the
  // preparation (loading) stage instead of jumping straight to replay.
  useEffect(() => {
    if (prevVoiceKey !== activeVoiceKey) {
      setPrevVoiceKey(activeVoiceKey);
      reset();
    }
  }, [activeVoiceKey, prevVoiceKey, reset]);

  useEffect(() => {
    setPlayedRounds([]);
  }, [sid]);

  const markPlayed = useCallback((roundIndex: number) => {
    setPlayedRounds((prev) =>
      prev.includes(roundIndex) ? prev : [...prev, roundIndex]
    );
  }, []);

  const hasPlayed = useCallback(
    (roundIndex: number) => playedRounds.includes(roundIndex),
    [playedRounds]
  );

  /** Reconciles an externally computed voice key (e.g. settings close). */
  const reconcileVoiceKey = useCallback(
    (key: string) => {
      if (prevVoiceKey !== key) {
        setPrevVoiceKey(key);
        reset();
      }
    },
    [prevVoiceKey, reset]
  );

  return {
    playedRounds,
    voiceDone,
    setVoiceDone,
    markPlayed,
    hasPlayed,
    reconcileVoiceKey,
    reset,
  };
}
