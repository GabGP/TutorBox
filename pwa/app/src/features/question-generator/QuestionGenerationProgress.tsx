import React, { useEffect, useRef, useState } from 'react';
import { ProgressBar } from '../../shared/ui/ProgressBar/ProgressBar';
import { ShinyText } from '../../shared/ui/ShinyText/ShinyText';
import { GenerationProgress, PEDAGOGICAL_STAGES, PROGRESS_ANIMATION } from './generator.types';
import styles from './QuestionGenerationProgress.module.css';
import { getSubconceptLabel, getTopicLabel } from './TopicSelector';

export interface QuestionGenerationProgressProps {
  progress: GenerationProgress;
  isComplete?: boolean;
}

export function formatDuration(seconds: number | null, isEstimate = false): string {
  if (seconds == null || seconds < 0) return '';
  const prefix = isEstimate ? '~' : '';
  if (seconds < 60) return `${prefix}${seconds}s`;
  const mins = Math.floor(seconds / 60), rem = seconds % 60;
  return rem > 0 ? `${prefix}${mins} min ${rem}s` : `${prefix}${mins} min`;
}

export const QuestionGenerationProgress: React.FC<QuestionGenerationProgressProps> = ({
  progress,
  isComplete: forceComplete,
}) => {
  const [stageIndex, setStageIndex] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const startTimeRef = useRef(Date.now());
  const total = progress.total || 1;
  const isDone = Boolean(forceComplete || (progress.done >= total && total > 0));
  const currentIdx = isDone ? total : (progress.currentIndex ?? Math.min(progress.done + 1, total));
  const prevIdxRef = useRef(currentIdx), qStartRef = useRef(0);

  useEffect(() => {
    if (isDone) return;
    const stageTimer = setInterval(() => {
      setStageIndex((prev) => (prev + 1) % PEDAGOGICAL_STAGES.length);
    }, PROGRESS_ANIMATION.STAGE_SPEED_SECONDS * 1000);
    return () => clearInterval(stageTimer);
  }, [isDone]);

  useEffect(() => {
    if (prevIdxRef.current !== currentIdx) {
      prevIdxRef.current = currentIdx;
      qStartRef.current = Math.floor((Date.now() - startTimeRef.current) / 1000);
    }
  }, [currentIdx]);

  useEffect(() => {
    if (isDone) return;
    const clock = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startTimeRef.current) / 1000));
    }, 1000);
    return () => clearInterval(clock);
  }, [isDone]);

  const percent = isDone ? 100 : Math.min(100, Math.round((progress.done / total) * 100));
  const remaining = isDone ? 0 : Math.max(0, total - progress.done);
  const effectiveEta = progress.eta ?? PROGRESS_ANIMATION.DEFAULT_QUESTION_ETA_SECONDS;
  const currentQElapsed = Math.max(0, elapsedSeconds - qStartRef.current);
  const currentQRemaining = remaining > 0 ? Math.max(1, effectiveEta - currentQElapsed) : 0;
  const liveRemaining = !isDone && remaining > 0 ? currentQRemaining + Math.max(0, remaining - 1) * effectiveEta : null;
  const formattedElapsed = formatDuration(elapsedSeconds, false) || '0s', formattedEta = formatDuration(liveRemaining, true);
  const topicLabel = progress.currentTopic ? getTopicLabel(progress.currentTopic) : '', subconceptLabel = getSubconceptLabel(progress.currentSubconcept);
  const colsMobile = total <= PROGRESS_ANIMATION.MOBILE_PILL_COLS_MAX ? total : PROGRESS_ANIMATION.MOBILE_PILL_COLS_MAX;
  const colsDesktop = total <= PROGRESS_ANIMATION.DESKTOP_PILL_COLS_MAX ? total : PROGRESS_ANIMATION.DESKTOP_PILL_COLS_MAX;
  const captionText = isDone ? '✓ Preguntas y distractores pedagógicos verificados con éxito.' : PEDAGOGICAL_STAGES[stageIndex];

  return (
    <section className={styles.card} aria-label="Progreso de creación de preguntas" id="gen-progress">
      <div className={styles.header}>
        <div className={styles.orbitContainer} aria-hidden="true">
          <div className={styles.orbitTrack} />
          {!isDone && <div className={styles.orbitRing} />}
          <div className={`${styles.orbitCore} ${isDone ? styles.orbitCoreDone : ''}`}>{isDone ? '✓' : '✨'}</div>
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
          <span key={captionText} className={styles.stageText}>{captionText}</span>
        </div>
      </div>
      <div className={styles.pillsList} role="list" aria-label="Estado por pregunta" style={{ '--cols-mobile': colsMobile, '--cols-desktop': colsDesktop } as React.CSSProperties}>
        {Array.from({ length: total }, (_, i) => {
          const qNum = i + 1;
          const status = isDone ? 'success' : (progress.statuses?.[i] ?? (i < progress.done ? 'success' : i === progress.done && progress.done < total ? 'generating' : 'pending'));
          const pillClass = status === 'success' ? styles.pillDone : status === 'failed' ? styles.pillFailed : status === 'generating' ? styles.pillActive : styles.pillPending;
          const label = status === 'success' ? `✓ P${qNum}` : status === 'failed' ? `✕ P${qNum}` : status === 'generating' ? `⚡ P${qNum}` : `○ P${qNum}`;
          return (
            <span key={qNum} role="listitem" className={`${styles.pill} ${pillClass}`} aria-label={`Pregunta ${qNum}: ${status}`}>
              {label}
            </span>
          );
        })}
      </div>
      <div className={styles.footer}>
        <span className={styles.timerBadge}>⏱️ {isDone ? 'Tiempo total' : 'Tiempo transcurrido'}: <strong>{formattedElapsed}</strong></span>
        {progress.failed > 0 && <span className={styles.failedBadge}>⚠️ {progress.failed} pregunta(s) con error</span>}
        {formattedEta && <span className={styles.etaBadge}>⏳ Restante estimado: <strong>{formattedEta}</strong></span>}
      </div>
    </section>
  );
};
