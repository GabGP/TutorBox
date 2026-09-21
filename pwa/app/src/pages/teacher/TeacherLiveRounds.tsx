import React, { useEffect } from 'react';
import { RemediationAlert } from '../../features/match-report/RemediationAlert';
import { SpeechLanguage, SpeechState } from '../../features/speech/speech.types';
import { RoundModel, SessionModel } from '../../features/session-engine/session.types';
import { CountdownRing } from '../../shared/ui/CountdownRing/CountdownRing';
import { TallyBars } from '../../shared/ui/TallyBars/TallyBars';
import utils from '../../shared/styles/utils.module.css';

export interface TeacherLiveRoundsProps {
  step: 'question' | 'reveal';
  session: SessionModel;
  round: RoundModel;
  voiceDone: number;
  /** True once this round's speech played (auto or manual). Survives remounts. */
  voicePlayed: boolean;
  voiceLang: SpeechLanguage;
  speechState: SpeechState;
  speechMessage: string;
  onPlaySpeech: () => void;
  onSkipSpeech: () => void;
}

/**
 * Teacher Live Rounds View component.
 * Displays live question administration panels: live countdown timer, incoming vote counters,
 * tally bar distributions, and pedagogical remediation speech controls during round revelation.
 *
 * @param {TeacherLiveRoundsProps} props - Component props containing active round state, tallies, and speech handlers.
 * @returns {JSX.Element | null} The rendered live round administration view.
 */
export const TeacherLiveRounds: React.FC<TeacherLiveRoundsProps> = ({
  step,
  session,
  round,
  voiceDone,
  voicePlayed,
  voiceLang,
  speechState,
  speechMessage,
  onPlaySpeech,
  onSkipSpeech,
}) => {
  const q = round.question;
  const result = round.result;
  const tally = result?.tally;
  const decision = result?.decision;

  useEffect(() => {
    if (
      step === 'reveal' &&
      decision?.should_speak &&
      voiceDone !== round.round_index &&
      !voicePlayed &&
      speechState !== 'loading' &&
      speechState !== 'playing'
    ) {
      onPlaySpeech();
    }
  }, [step, decision?.should_speak, voiceDone, voicePlayed, round.round_index, speechState, onPlaySpeech]);

  if (step === 'question' && q) {
    const isClosed = round.status === 'closed';
    const qHelp = isClosed
      ? 'Votación cerrada. Nadie más puede responder.'
      : round.time_remaining == null
      ? 'Sin cronómetro (el servidor se reinició). Termine la pregunta cuando quiera.'
      : '';

    return (
      <section id="s-question" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <CountdownRing
            id="ring"
            size={74}
            remaining={round.status === 'open' ? round.time_remaining : 0}
            duration={round.duration_seconds}
          />
          <div className={utils.grow}>
            <div style={{ fontSize: '14px', color: 'var(--mute2)', fontWeight: 500 }} id="qcounter">
              Pregunta {round.round_index + 1} de {session.question_count}
            </div>
            <div style={{ fontSize: '18px', fontWeight: 600, lineHeight: 1.3 }} id="qtext">
              {q.question_text}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', fontSize: '16px', color: 'var(--mute)' }}>
          <b style={{ fontSize: '30px', color: 'var(--p)' }} id="answered">
            {round.votes_cast}
          </b>
          <span id="answeredLbl">
            {round.votes_cast === 1 ? 'respuesta recibida' : 'respuestas recibidas'}
          </span>
        </div>
        {qHelp && <p style={{ fontSize: '15px', color: 'var(--mute2)', margin: 0 }} id="qhelp">{qHelp}</p>}
        <TallyBars id="qbars" options={q.options} counts={null} totalVotes={0} />
      </section>
    );
  }

  if (step === 'reveal' && q && tally) {
    const showSpeech = Boolean(decision?.should_speak && voiceDone !== round.round_index);

    return (
      <section id="s-reveal" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="okcard">
          <div style={{ fontSize: '14px', fontWeight: 500, letterSpacing: '0.3px' }}>RESPUESTA CORRECTA</div>
          <div style={{ fontSize: 'clamp(28px, 3vw, 36px)', fontWeight: 700 }} id="correct">
            {tally.correct_option} · {q.options[tally.correct_option]}
          </div>
        </div>

        <TallyBars id="rbars" options={q.options} counts={tally.counts} totalVotes={tally.total_votes} animate />

        {decision && (
          <RemediationAlert
            shouldShow={showSpeech}
            dominantCount={tally.counts[decision.dominant_distractor] || 0}
            totalVotes={tally.total_votes}
            dominantPercentage={decision.dominant_percentage}
            dominantOptionText={q.options[decision.dominant_distractor] || ''}
            explanation={decision.explanation}
            speechState={speechState}
            speechMessage={speechMessage}
            voiceLang={voiceLang}
            onPlay={onPlaySpeech}
            onSkip={onSkipSpeech}
          />
        )}

        <div className="card row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Aciertos en esta pregunta</span>
          <b id="hits" style={{ fontSize: '22px', color: 'var(--p)' }}>
            {tally.correct_count}/{tally.total_votes}
          </b>
        </div>
      </section>
    );
  }

  return null;
};
