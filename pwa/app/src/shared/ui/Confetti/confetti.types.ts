export type ParticleMode = 'celebration' | 'reflection';

export interface ConfettiCanvasProps {
  mode?: ParticleMode;
  active?: boolean;
  durationMs?: number;
  className?: string;
  id?: string;
}
