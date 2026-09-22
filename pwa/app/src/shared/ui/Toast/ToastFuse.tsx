import React from 'react';
import type { ToastFuse as FuseEdge } from './toast.types';
import styles from './Toast.module.css';

export interface ToastFuseProps {
  fuse: FuseEdge;
  duration: number;
  held: boolean;
}

/** Burning timer line. Remount (via key) re-arms it with `duration`. */
export const ToastFuse: React.FC<ToastFuseProps> = ({ fuse, duration, held }) => {
  if (fuse === 'none' || duration <= 0) return null;
  return (
    <i
      key={duration}
      className={`${styles.fuse} ${fuse === 'top' ? styles.fuseTop : ''}${held ? ` ${styles.fuseHeld}` : ''}`}
      aria-hidden="true"
      style={{ animationDuration: `${duration}ms` }}
    />
  );
};
