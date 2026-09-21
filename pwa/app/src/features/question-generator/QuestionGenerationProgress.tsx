import React from 'react';
import { Check, Circle, Hourglass, Palette, PenLine, Ruler, Save, Sparkles, Timer, TriangleAlert, X, Zap } from 'lucide-react';
import { ProgressBar } from '../../shared/ui/ProgressBar/ProgressBar';
import { ShinyText } from '../../shared/ui/ShinyText/ShinyText';
import { GenerationProgress } from './generator.types';
import { PEDAGOGICAL_STAGES, PROGRESS_ANIMATION } from './generator.constants';
import { useGenerationClock } from './useGenerationClock';
import styles from './QuestionGenerationProgress.module.css';
import { formatDuration } from '../../shared/lib/format';
import { getSubconceptLabel, getTopicLabel } from '../../shared/taxonomy/labels';

export { formatDuration } from '../../shared/lib/format';

export interface QuestionGenerationProgressProps {
  progress: GenerationProgress;
  isComplete?: boolean;
}

export const STAGE_ICONS = [PenLine, Palette, Ruler, Save] as const;

export const QuestionGenerationProgress: React.FC<QuestionGenerationProgressProps> = ({
  progress,
  isComplete: forceComplete,
}) => {
  const total = progress.total || 1;
  const isDone = Boolean(forceComplete || (progress.done >= total && total > 0));
  const { stageIndex, elapsedSeconds, currentIdx, questionStartSecond } =
    useGenerationClock(progress, isDone);

  const percent = isDone ? 100 : Math.min(100, Math.round((progress.done / total) * 100));
  const remaining = isDone ? 0 : Math.max(0, total - progress.done);
  const effectiveEta = progress.eta ?? PROGRESS_ANIMATION.DEFAULT_QUESTION_ETA_SECONDS;
  const currentQElapsed = Math.max(0, elapsedSeconds - questionStartSecond);
  const currentQRemaining = remaining > 0 ? Math.max(1, effectiveEta - currentQElapsed) : 0;
  const liveRemaining = !isDone && remaining > 0 ? currentQRemaining + Math.max(0, remaining - 1) * effectiveEta : null;
  const formattedElapsed = formatDuration(elapsedSeconds, false) || '0s', formattedEta = formatDuration(liveRemaining, true);
  const topicLabel = progress.currentTopic ? getTopicLabel(progress.currentTopic) : '', subconceptLabel = getSubconceptLabel(progress.currentSubconcept);
  const colsMobile = total <= PROGRESS_ANIMATION.MOBILE_PILL_COLS_MAX ? total : PROGRESS_ANIMATION.MOBILE_PILL_COLS_MAX;
  const colsDesktop = total <= PROGRESS_ANIMATION.DESKTOP_PILL_COLS_MAX ? total : PROGRESS_ANIMATION.DESKTOP_PILL_COLS_MAX;
  const failedCount = progress.failed || 0;
  const successCount = progress.ids.length;
  const captionText = isDone
    ? failedCount > 0
      ? `${successCount} de ${total} preguntas listas. ${failedCount} no salieron del modelo.`
      : 'Preguntas y distractores pedagógicos verificados con éxito.'
    : PEDAGOGICAL_STAGES[stageIndex];
  const StageIcon = isDone ? Check : STAGE_ICONS[stageIndex % STAGE_ICONS.length];

  return (
    <section className={styles.card} aria-label="Progreso de creación de preguntas" id="gen-progress">
      <div className={styles.header}>
        <div className={styles.orbitContainer} aria-hidden="true">
          <div className={styles.orbitTrack} />
          {!isDone && <div className={styles.orbitRing} />}
          <div className={`${styles.orbitCore} ${isDone ? styles.orbitCoreDone : ''}`}>{isDone ? <Check size={16} aria-hidden /> : <Sparkles size={16} aria-hidden />}</div>
        </div>
        <div className={styles.titles}>
          {(topicLabel || subconceptLabel) && (
            <div className={styles.badgeRow}>
              {topicLabel && <span className={styles.topicBadge}>{topicLabel}</span>}
              {subconceptLabel && <span className={styles.subconceptBadge}>{subconceptLabel}</span>}
            </div>
          )}
          {isDone ? (
            <h2 className={styles.title}>¡Preguntas listas para jugar!</h2>
          ) : (
            <ShinyText
              text="Creando las preguntas con IA..."
              as="h2"
              className={styles.title}
              speed={PROGRESS_ANIMATION.SHIMMER_SPEED_SECONDS}
            />
          )}
        </div>
      </div>
      <div className={styles.progressSection}>
        <div className={styles.progressMeta}>
          <span className={styles.questionCounter}>Pregunta <strong>{isDone ? total : currentIdx}</strong> de <strong>{total}</strong></span>
          <span className={styles.percentText}>{percent}%</span>
        </div>
        <ProgressBar value={percent} animated={!isDone} size="md" label="Progreso general" speed={PROGRESS_ANIMATION.SHIMMER_SPEED_SECONDS} />
        <div className={styles.stageCaption} aria-live="polite" aria-atomic="true">
          <span key={captionText} className={styles.stageText} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}><StageIcon size={14} aria-hidden />{captionText}</span>
        </div>
      </div>
      <div className={styles.pillsList} role="list" aria-label="Estado por pregunta" style={{ '--cols-mobile': colsMobile, '--cols-desktop': colsDesktop } as React.CSSProperties}>
        {Array.from({ length: total }, (_, i) => {
          const qNum = i + 1;
          const status = progress.statuses?.[i] ?? (isDone ? 'success' : (i < progress.done ? 'success' : i === progress.done && progress.done < total ? 'generating' : 'pending'));
          const pillClass = status === 'success' ? styles.pillDone : status === 'failed' ? styles.pillFailed : status === 'generating' ? styles.pillActive : styles.pillPending;
          const PillIcon = status === 'success' ? Check : status === 'failed' ? X : status === 'generating' ? Zap : Circle;
          return (
            <span key={qNum} role="listitem" className={`${styles.pill} ${pillClass}`} aria-label={`Pregunta ${qNum}: ${status}`}>
              <PillIcon size={12} aria-hidden /> P{qNum}
            </span>
          );
        })}
      </div>
      <div className={styles.footer}>
        <span className={styles.timerBadge} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}><Timer size={13} aria-hidden /> {isDone ? 'Tiempo total' : 'Tiempo transcurrido'}: <strong>{formattedElapsed}</strong></span>
        {progress.failed > 0 && <span className={styles.failedBadge} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}><TriangleAlert size={13} aria-hidden /> {progress.failed} pregunta(s) con error</span>}
        {formattedEta && <span className={styles.etaBadge} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}><Hourglass size={13} aria-hidden /> Restante estimado: <strong>{formattedEta}</strong></span>}
      </div>
    </section>
  );
};
