import React, { useRef } from 'react';
import { Check, CircleX, TriangleAlert, X } from 'lucide-react';
import { useFuseTimer } from './useFuseTimer';
import { useSwipeDismiss } from './useSwipeDismiss';
import { useToastExit, type ToastExit } from './useToastExit';
import { ToastFuse } from './ToastFuse';
import type { ToastItemProps } from './toast.types';
import styles from './Toast.module.css';

const TONE_ICON = { success: Check, warn: TriangleAlert, error: CircleX } as const;

/**
 * Single floating toast (SwipeToast port, dependency-free): exit machine,
 * fuse timer and swipe physics around the icon/title/description/action
 * card. Cross-hook calls go through refs to keep callbacks stable.
 */
export const ToastItemView: React.FC<ToastItemProps> = ({
  toast,
  swipeDistance = 40,
  settleBounce = 0.2,
  slideMs = 400,
  pauseOnHover = true,
  closeButton = true,
  dismissible = true,
  onExit,
}) => {
  const duration = toast.duration ?? 4000;
  const tone = toast.tone ?? 'success';
  const fuse = toast.fuse ?? 'bottom';
  const exitRef = useRef<ToastExit | null>(null);
  const fuseRef = useRef<{ pause: () => void; resume: () => void } | null>(null);

  const { dragY, swiping, snapStyle, bindSwipe, isDragging } = useSwipeDismiss({
    swipeDistance,
    settleBounce,
    disabled: !dismissible,
    onSwipe: () => exitRef.current?.commitSwipe(),
    onDragEnd: () => {
      const ex = exitRef.current;
      if (!ex) return;
      if (ex.phase === 'open' && !ex.leaving) fuseRef.current?.resume();
      ex.consumePending();
    },
  });

  const exit = useToastExit({
    slideMs,
    toastId: toast.id,
    dismissible,
    isDragging,
    holdFuse: () => fuseRef.current?.pause(),
    releaseFuse: () => fuseRef.current?.resume(),
    onExit,
  });
  exitRef.current = exit;

  const { pauseFuse, resumeFuse, fuseHeld } = useFuseTimer(
    duration,
    exit.phase === 'open' && !exit.leaving,
    () => exitRef.current?.close('timeout')
  );
  fuseRef.current = { pause: pauseFuse, resume: resumeFuse };

  const open = exit.phase === 'open' && !exit.leaving;
  const ToneIcon = TONE_ICON[tone];
  const endPress = (e: React.PointerEvent, end: (ev: React.PointerEvent) => void) => {
    end(e);
    if (exit.phase === 'open' && !exit.leaving) resumeFuse();
  };

  return (
    <div
      className={`${styles.toast} ${styles[tone]}${open ? '' : ` ${styles.exiting}`}${exit.instant ? ` ${styles.instant}` : ''}`}
      role={tone === 'error' ? 'alert' : 'status'}
      aria-live={tone === 'error' ? 'assertive' : 'polite'}
      aria-atomic="true"
      tabIndex={0}
      data-phase={exit.phase}
      data-fuse={duration > 0 ? fuse : 'none'}
      data-dismissible={dismissible ? 'true' : 'false'}
      data-swiping={swiping ? '' : undefined}
      onPointerDown={(e) => {
        if (exit.leaving) return;
        exit.markPointer();
        if (exit.phase === 'closing') exit.rescue();
        pauseFuse();
        bindSwipe.onPointerDown(e);
      }}
      onPointerMove={bindSwipe.onPointerMove}
      onPointerUp={(e) => endPress(e, bindSwipe.onPointerUp)}
      onPointerCancel={(e) => endPress(e, bindSwipe.onPointerCancel)}
      onPointerEnter={(e) => {
        if (pauseOnHover && e.pointerType === 'mouse') pauseFuse();
      }}
      onPointerLeave={(e) => {
        if (e.pointerType === 'mouse' && open) resumeFuse();
      }}
      onFocus={pauseFuse}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget) && open) resumeFuse();
      }}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') exit.markKeyboard();
        if (e.key === 'Escape' && dismissible) {
          e.stopPropagation();
          exit.close('escape');
        }
      }}
      style={{
        ['--toast-slide' as string]: `${slideMs}ms`,
        ...(swiping || exit.leaving
          ? { transform: exit.leaving ? `translateY(calc(${dragY}px + 120%))` : `translateY(${dragY}px)` }
          : undefined),
        ...snapStyle,
      }}
    >
      <span className={styles.icon} aria-hidden="true">
        {toast.icon ?? <ToneIcon size={18} />}
      </span>
      <span className={styles.body}>
        <span className={styles.title}>{toast.message}</span>
        {toast.description ? <span className={styles.desc}>{toast.description}</span> : null}
      </span>
      {toast.actionLabel ? (
        <button
          type="button"
          className={styles.action}
          onClick={() => {
            toast.onAction?.();
            exit.close('action');
          }}
        >
          {toast.actionLabel}
        </button>
      ) : null}
      {closeButton && dismissible ? (
        <button
          type="button"
          className={styles.close}
          aria-label="Descartar aviso"
          onClick={() => exit.close('close')}
        >
          <X size={12} aria-hidden />
        </button>
      ) : null}
      <ToastFuse fuse={fuse} duration={duration} held={fuseHeld} />
    </div>
  );
};
