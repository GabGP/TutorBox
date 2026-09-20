import { render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { RoundModel, SessionModel } from '../../../features/session-engine/session.types';
import { TeacherLiveRounds } from '../TeacherLiveRounds';

function revealedRound(index = 0): RoundModel {
  return {
    round_id: `r${index}`,
    round_index: index,
    duration_seconds: 20,
    time_remaining: 0,
    status: 'revealed',
    votes_cast: 10,
    question: {
      id: 'q1',
      question_text: '¿Cuánto es 1 + 1?',
      options: { A: '2', B: '3', C: '4', D: '5' },
    },
    result: {
      tally: {
        counts: { A: 2, B: 7, C: 1, D: 0 },
        total_votes: 10,
        correct_option: 'A',
        correct_count: 2,
        correct_percentage: 20,
      },
      decision: {
        should_speak: true,
        dominant_distractor: 'B',
        dominant_percentage: 70,
        explanation: 'Sumaron dos veces.',
      },
      explanations: { B: 'Sumaron dos veces.' },
    },
  };
}

const session: SessionModel = {
  id: 's1',
  title: 'Test',
  topic: 'arithmetic',
  status: 'active',
  question_count: 3,
  current_round_index: 0,
  created_at: '',
};

function renderReveal(
  round: RoundModel,
  voicePlayed: boolean,
  onPlaySpeech: () => void
) {
  return render(
    <TeacherLiveRounds
      step="reveal"
      session={{ ...session, current_round: round }}
      round={round}
      voiceDone={-1}
      voicePlayed={voicePlayed}
      voiceLang="es"
      speechState="idle"
      speechMessage=""
      onPlaySpeech={onPlaySpeech}
      onSkipSpeech={vi.fn()}
    />
  );
}

describe('TeacherLiveRounds autoplay', () => {
  it('auto-plays once when speech was never played', () => {
    const onPlaySpeech = vi.fn();
    renderReveal(revealedRound(0), false, onPlaySpeech);
    expect(onPlaySpeech).toHaveBeenCalledTimes(1);
  });

  it('does not replay after remount when the round already played', () => {
    const onPlaySpeech = vi.fn();
    const round = revealedRound(0);
    const first = renderReveal(round, false, onPlaySpeech);
    expect(onPlaySpeech).toHaveBeenCalledTimes(1);
    first.unmount();

    // Coming back (e.g. closing settings remounts this view).
    renderReveal(round, true, onPlaySpeech);
    expect(onPlaySpeech).toHaveBeenCalledTimes(1);
  });

  it('auto-plays a new round after an earlier one played', () => {
    const onPlaySpeech = vi.fn();
    const first = renderReveal(revealedRound(0), false, onPlaySpeech);
    expect(onPlaySpeech).toHaveBeenCalledTimes(1);
    first.unmount();

    // Next round starts unplayed: autoplay fires again.
    renderReveal(revealedRound(1), false, onPlaySpeech);
    expect(onPlaySpeech).toHaveBeenCalledTimes(2);
  });

  it('stays silent when should_speak is false', () => {
    const onPlaySpeech = vi.fn();
    const round: RoundModel = {
      ...revealedRound(0),
      result: {
        ...revealedRound(0).result!,
        decision: {
          should_speak: false,
          dominant_distractor: '',
          dominant_percentage: 0,
          explanation: '',
        },
      },
    };
    renderReveal(round, false, onPlaySpeech);
    expect(onPlaySpeech).not.toHaveBeenCalled();
  });
});
