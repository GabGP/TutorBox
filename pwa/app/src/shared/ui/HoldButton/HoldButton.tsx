import React, { useCallback } from 'react';
import type { HoldButtonProps } from './holdButton.types';
import { useHoldProgress } from './useHoldProgress';
import styles from './HoldButton.module.css';

/**
 * TutorBox HoldButton: press-and-hold confirm with liquid fill.
 * Replicates ReactBits HoldButton timing (linear fill over holdTime,
 * snap-back over releaseTime, wave meniscus, glow charge + done pulse,
 * ink inversion, done blur-in) styled with TutorBox tokens.
 */
export const HoldButton: React.FC<HoldButtonProps> = ({
  children = 'Mantén para confirmar',
  doneLabel = 'Confirmado',
  icon,
  doneIcon,
  size = 'md',
  radius = 14,
  fillDirection = 'right',
  holdTime = 2000,
  releaseTime = 200,
  pressScale = 0.97,
  wave = true,
  waveAmplitude = 6,
  glow = true,
  resetAfter = 1200,
  disabled = false,
  className = '',
  id,
  ariaLabel,
  backgroundColor = 'var(--panel, #F7FBFD)',
  fillColor = 'var(--p, #0B6E99)',
  textColor = 'var(--ink, #131E23)',
  fillTextColor = '#ffffff',
  onHold,
  onTap,
  onPhaseChange,
}) => {
  const { phase, progress, start, release } = useHoldProgress({
    holdTime,
    releaseTime,
    resetAfter,
    disabled,
    onHold,
    onTap,
    onPhaseChange,
  });
  const done = phase === 'done';
  const holding = phase === 'holding';
  const idleContent = (
    <>
      {icon && (
        <span className={styles.icon} aria-hidden="true">
          {icon}
        </span>
      )}
      <span>{children}</span>
    </>
  );

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.repeat) return;
      if (event.key === ' ' || event.key === 'Enter') {
        event.preventDefault();
        start();
      } else if (event.key === 'Escape') release();
    },
    [release, start]
  );

  const style = {
    '--hb-radius': `${radius}px`,
    '--hb-scale': String(pressScale),
    '--hb-progress': String(progress),
    '--hb-wave': `${waveAmplitude}px`,
    '--hb-bg': backgroundColor,
    '--hb-fill': fillColor,
    '--hb-ink': textColor,
    '--hb-fill-ink': fillTextColor,
    '--hb-hold': `${holdTime}ms`,
  } as React.CSSProperties;

  return (
    <button
      type="button"
      id={id}
      style={style}
      disabled={disabled}
      aria-label={ariaLabel ?? (typeof children === 'string' ? children : 'Mantén para confirmar')}
      aria-busy={holding}
      data-phase={phase}
      data-progress={progress.toFixed(3)}
      data-direction={fillDirection}
      className={[
        styles.root,
        styles[size],
        holding ? styles.holding : '',
        done ? styles.done : '',
        glow ? styles.glow : '',
        wave ? styles.wave : '',
        className,
      ]
        .join(' ')
        .trim()}
      onPointerDown={(event) => {
        event.currentTarget.setPointerCapture?.(event.pointerId);
        start();
      }}
      onPointerUp={release}
      onPointerLeave={release}
      onPointerCancel={release}
      onContextMenu={(event) => event.preventDefault()}
      onKeyDown={handleKeyDown}
      onKeyUp={(event) => {
        if (event.key === ' ' || event.key === 'Enter') release();
      }}
    >
      <span className={styles.fill} data-testid="hold-fill" aria-hidden="true" />
      <span className={styles.label} aria-hidden={done}>
        {idleContent}
      </span>
      <span className={styles.labelFill} aria-hidden="true">
        {idleContent}
      </span>
      {done && (
        <span className={styles.doneLabel}>
          {doneIcon && (
            <span className={styles.icon} aria-hidden="true">
              {doneIcon}
            </span>
          )}
          <span>{doneLabel}</span>
        </span>
      )}
      <span className={styles.srHint}>
        Mantén pulsado {Math.round(holdTime / 1000)} segundos para confirmar
      </span>
    </button>
  );
};
