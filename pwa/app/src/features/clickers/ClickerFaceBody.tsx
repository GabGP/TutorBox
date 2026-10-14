import React, { useRef } from 'react';
import listStyles from '../../shared/styles/lists.module.css';
import styles from './clickers.module.css';
import type { ClickerDevice } from './clickers.types';
import { hasNeverConnected, isNewClicker } from './clickerStatus';

/**
 * Horizontal travel, in px, above which a click on the id is read as the end
 * of a drag rather than a tap. A mouse drag that starts and ends on the id
 * still fires its click, and SwipeRow does not stop it, so without this the
 * edit sheet would open on top of the strip the drag just revealed. Taps stay
 * well under this (a few px of jitter at most).
 */
const DRAG_CLICK_TOLERANCE_PX = 8;

export interface ClickerFaceBodyProps {
  device: ClickerDevice;
  /** Armed delete: the id stays as text and the confirm covers the tag line. */
  armed?: boolean;
  /** Laid over the tag line while armed (hold to confirm and Cancelar). */
  confirm?: React.ReactNode;
  onOpenEdit: (device: ClickerDevice) => void;
}

/**
 * The two lines of a clicker row. Line 1 is the id: the teacher matches it
 * against the label on the case, so it is never truncated. Line 2 holds the
 * tags. The armed row reuses both lines, with the tags hidden in place and
 * the confirm laid over them, so arming a delete keeps the row height.
 */
export const ClickerFaceBody: React.FC<ClickerFaceBodyProps> = ({
  device,
  armed = false,
  confirm,
  onOpenEdit,
}) => {
  // Where the pointer went down on the id button; null when no press is pending
  // (keyboard activation, or a press already consumed by its click).
  const pressX = useRef<number | null>(null);

  const handleIdClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    const startX = pressX.current;
    pressX.current = null;
    if (startX !== null && Math.abs(event.clientX - startX) > DRAG_CLICK_TOLERANCE_PX) return;
    onOpenEdit(device);
  };

  const studentTagClass =
    device.assigned_user_id === null
      ? `${listStyles.roleTag} ${styles.tagChip} ${styles.unassignedTag}`
      : `${listStyles.roleTag} ${styles.tagChip}`;
  // Read on every render: the list reloads every few seconds, so the chip ends on time.
  const showNewChip = isNewClicker(device, Date.now());
  const showNeverConnectedChip = hasNeverConnected(device);

  return (
    <div className={styles.faceBody}>
      {armed ? (
        <span className={styles.idText}>{device.device_id}</span>
      ) : (
        <button
          type="button"
          className={styles.idButton}
          onPointerDown={(event) => {
            pressX.current = event.clientX;
          }}
          // A keypress is never a drag: clear any pending press before its click.
          onKeyDown={() => {
            pressX.current = null;
          }}
          onClick={handleIdClick}
        >
          {device.device_id}
        </button>
      )}
      <div className={styles.tagLine}>
        <div
          className={`${styles.tags} ${armed ? styles.tagsHidden : ''}`}
          aria-hidden={armed || undefined}
        >
          <span className={studentTagClass}>{device.assigned_username ?? 'Sin alumno'}</span>
          {showNewChip && (
            <span className={`${listStyles.roleTag} ${styles.tagChip} ${styles.newTag}`}>Nuevo</span>
          )}
          {showNeverConnectedChip && (
            <span className={`${listStyles.roleTag} ${styles.tagChip}`}>Sin conectar</span>
          )}
        </div>
        {armed && <div className={styles.confirmOverlay}>{confirm}</div>}
      </div>
    </div>
  );
};
