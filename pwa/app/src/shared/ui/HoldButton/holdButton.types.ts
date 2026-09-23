import type React from 'react';

export type HoldButtonSize = 'sm' | 'md' | 'lg';
export type HoldButtonFillDirection = 'right' | 'up';
export type HoldButtonPhase = 'idle' | 'holding' | 'done';

/**
 * Public contract for the TutorBox HoldButton.
 * Mirrors ReactBits HoldButton behavior (press-and-hold confirm with
 * liquid fill, wave meniscus, glow, done blur-in) but defaults to
 * TutorBox design tokens instead of ReactBits dark/purple.
 */
export interface HoldButtonProps {
  children?: React.ReactNode;
  doneLabel?: React.ReactNode;
  icon?: React.ReactNode;
  doneIcon?: React.ReactNode;
  size?: HoldButtonSize;
  radius?: number;
  fillDirection?: HoldButtonFillDirection;
  holdTime?: number;
  releaseTime?: number;
  pressScale?: number;
  wave?: boolean;
  waveAmplitude?: number;
  glow?: boolean;
  resetAfter?: number;
  disabled?: boolean;
  className?: string;
  id?: string;
  ariaLabel?: string;
  backgroundColor?: string;
  fillColor?: string;
  textColor?: string;
  fillTextColor?: string;
  onHold?: () => void;
  onTap?: () => void;
  onPhaseChange?: (phase: HoldButtonPhase) => void;
}
