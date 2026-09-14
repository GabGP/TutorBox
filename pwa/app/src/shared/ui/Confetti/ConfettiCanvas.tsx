import React, { useEffect, useRef } from 'react';
import { ConfettiCanvasProps } from './confetti.types';
import styles from './ConfettiCanvas.module.css';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  color: string;
  rotation: number;
  rotationSpeed: number;
  opacity: number;
}

const CELEBRATION_COLORS = ['#E21B3C', '#1368CE', '#C98A00', '#1E7B2E', '#0B6E99', '#FFD700'];
const REFLECTION_COLORS = ['#F59E0B', '#FCD34D', '#93C5FD', '#A7F3D0'];

/**
 * Lightweight hardware-accelerated 2D Canvas Particle Engine.
 * Provides celebratory confetti bursts or gentle reflection sparks with zero external dependencies.
 */
export const ConfettiCanvas: React.FC<ConfettiCanvasProps> = ({
  mode = 'celebration',
  active = true,
  durationMs = 2400,
  className = '',
  id,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (!active || typeof window === 'undefined') return;
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = canvas.parentElement?.clientWidth || window.innerWidth || 360;
    canvas.height = canvas.parentElement?.clientHeight || window.innerHeight || 640;

    const count = mode === 'celebration' ? 42 : 18;
    const colors = mode === 'celebration' ? CELEBRATION_COLORS : REFLECTION_COLORS;
    const originX = canvas.width / 2;
    const originY = mode === 'celebration' ? canvas.height * 0.45 : canvas.height * 0.65;

    const particles: Particle[] = Array.from({ length: count }, () => {
      const angle =
        mode === 'celebration'
          ? Math.random() * Math.PI * 2
          : -Math.PI / 2 + (Math.random() - 0.5) * 0.8;
      const speed = mode === 'celebration' ? 3 + Math.random() * 6 : 0.8 + Math.random() * 1.5;
      return {
        x: originX,
        y: originY,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        size: mode === 'celebration' ? 6 + Math.random() * 6 : 3 + Math.random() * 4,
        color: colors[Math.floor(Math.random() * colors.length)],
        rotation: Math.random() * 360,
        rotationSpeed: (Math.random() - 0.5) * 8,
        opacity: 1,
      };
    });

    let animationId: number;
    const startTime = performance.now();

    const render = (now: number) => {
      const elapsed = now - startTime;
      const progress = elapsed / durationMs;
      if (progress >= 1) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        return;
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (const p of particles) {
        if (mode === 'celebration') {
          p.vy += 0.15;
          p.vx *= 0.98;
        } else {
          p.vy -= 0.02;
          p.vx += (Math.random() - 0.5) * 0.1;
        }
        p.x += p.vx;
        p.y += p.vy;
        p.rotation += p.rotationSpeed;
        p.opacity = Math.max(0, 1 - progress);

        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rotation * Math.PI) / 180);
        ctx.globalAlpha = p.opacity;
        ctx.fillStyle = p.color;

        if (mode === 'celebration') {
          ctx.fillRect(-p.size / 2, -p.size / 4, p.size, p.size / 2);
        } else {
          ctx.beginPath();
          ctx.arc(0, 0, p.size / 2, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.restore();
      }
      animationId = requestAnimationFrame(render);
    };

    animationId = requestAnimationFrame(render);
    return () => {
      if (animationId) cancelAnimationFrame(animationId);
    };
  }, [active, mode, durationMs]);

  if (!active) return null;

  return (
    <canvas
      ref={canvasRef}
      id={id}
      data-testid="confetti-canvas"
      className={`${styles.canvasOverlay} ${className}`}
      aria-hidden="true"
    />
  );
};
