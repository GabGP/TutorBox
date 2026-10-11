import React, { useEffect } from 'react';
import { Eye, Pencil, Trash2 } from 'lucide-react';
import utils from '../../shared/styles/utils.module.css';
import { HoldButton } from '../../shared/ui/HoldButton/HoldButton';
import { HOLD_LONG_MS } from '../../shared/ui/HoldButton/holdDurations';
import { SwipeRow } from '../../shared/ui/SwipeRow/SwipeRow';
import styles from './clickers.module.css';
import { ClickerFaceBody } from './ClickerFaceBody';
import type { ClickerDevice } from './clickers.types';

export interface ClickerRowProps {
  device: ClickerDevice;
  /** This row's delete is armed: the strip gives way to the hold confirm. */
  confirmArmed: boolean;
  swipeOpen: boolean;
  onOpenInfo: (device: ClickerDevice) => void;
  onOpenEdit: (device: ClickerDevice) => void;
  onArmDelete: (deviceId: string) => void;
  onCommitDelete: (deviceId: string) => void;
  onDisarmDelete: () => void;
  onOpenChange: (open: boolean) => void;
}

/**
 * One clicker row: the swipe strip (Info, Editar, Eliminar) or, once delete
 * is armed, a press-and-hold confirm with a Cancelar affordance. Both states
 * share the two-line face (see ClickerFaceBody), so the row keeps its height.
 * Tapping the id opens the edit sheet. Escape disarms.
 */
export const ClickerRow: React.FC<ClickerRowProps> = ({
  device,
  confirmArmed,
  swipeOpen,
  onOpenInfo,
  onOpenEdit,
  onArmDelete,
  onCommitDelete,
  onDisarmDelete,
  onOpenChange,
}) => {
  const deviceId = device.device_id;

  useEffect(() => {
    if (!confirmArmed) return undefined;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onDisarmDelete();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [confirmArmed, onDisarmDelete]);

  return (
    <div role="listitem">
      <div className={utils.grow}>
        {confirmArmed ? (
          <div className={styles.faceFrame}>
            <ClickerFaceBody
              device={device}
              armed
              onOpenEdit={onOpenEdit}
              confirm={
                <>
                  <HoldButton
                    holdTime={HOLD_LONG_MS}
                    size="sm"
                    className={styles.confirmHold}
                    ariaLabel={`Mantén para eliminar clicker ${deviceId}`}
                    backgroundColor="var(--bad-bg, #FFE9E7)"
                    fillColor="var(--bad, #B3261E)"
                    textColor="var(--bad-ink, #5F1710)"
                    fillTextColor="#ffffff"
                    doneLabel="Eliminado"
                    onHold={() => onCommitDelete(deviceId)}
                  >
                    Mantén para eliminar
                  </HoldButton>
                  <button
                    type="button"
                    className={styles.cancelBtn}
                    onClick={onDisarmDelete}
                    aria-label={`Cancelar eliminación clicker ${deviceId}`}
                  >
                    Cancelar
                  </button>
                </>
              }
            />
          </div>
        ) : (
          <SwipeRow
            ariaLabel={`Clicker ${deviceId}`}
            open={swipeOpen}
            onOpenChange={onOpenChange}
            actions={[
              {
                key: 'info',
                label: 'Info',
                ariaLabel: `Ver detalle clicker ${deviceId}`,
                icon: <Eye aria-hidden />,
                onActivate: () => onOpenInfo(device),
              },
              {
                key: 'edit',
                label: 'Editar',
                ariaLabel: `Editar clicker ${deviceId}`,
                icon: <Pencil aria-hidden />,
                onActivate: () => onOpenEdit(device),
              },
              {
                key: 'delete',
                label: 'Eliminar',
                icon: <Trash2 aria-hidden />,
                tone: 'danger',
                onActivate: () => onArmDelete(deviceId),
              },
            ]}
          >
            <ClickerFaceBody device={device} onOpenEdit={onOpenEdit} />
          </SwipeRow>
        )}
      </div>
    </div>
  );
};
