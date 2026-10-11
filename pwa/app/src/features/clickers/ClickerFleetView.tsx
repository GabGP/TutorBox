import React, { useCallback, useEffect, useState } from 'react';
import listStyles from '../../shared/styles/lists.module.css';
import { DataList } from '../../shared/ui/DataList/DataList';
import { Skeleton } from '../../shared/ui/Skeleton/Skeleton';
import { ToastViewport } from '../../shared/ui/Toast/ToastViewport';
import { ClickerAddForm } from './ClickerAddForm';
import { ClickerEditSheet } from './ClickerEditSheet';
import { ClickerInfoSheet } from './ClickerInfoSheet';
import { ClickerRow } from './ClickerRow';
import styles from './clickers.module.css';
import type { ClickerDevice } from './clickers.types';
import { useClickerFleet } from './useClickerFleet';

const SKELETON_ROWS = 3;

/**
 * Teacher clicker list: the count of clickers that hold a student, the add
 * form, swipe rows (Info, Editar, Eliminar with hold-to-confirm), and the
 * Info and Editar sheets. Owns which row is open or armed and which clicker
 * the sheets show, so an armed delete never leaks to another row.
 * Escape closes the innermost layer first (a sheet, then an armed delete),
 * never the Clickers sheet behind it.
 * Failures float as error toasts, so the list never shifts.
 */
export const ClickerFleetView: React.FC = () => {
  const {
    devices,
    students,
    loading,
    toasts,
    dismissToast,
    registerClicker,
    assignStudent,
    unassignStudent,
    deleteClicker,
  } = useClickerFleet();
  const [openSwipeId, setOpenSwipeId] = useState<string | null>(null);
  const [armedDeleteId, setArmedDeleteId] = useState<string | null>(null);
  const [infoDevice, setInfoDevice] = useState<ClickerDevice | null>(null);
  const [editDevice, setEditDevice] = useState<ClickerDevice | null>(null);

  const withStudent = devices.filter((device) => device.assigned_user_id !== null).length;

  // The Sheet component closes on any Escape (it listens on window too), so
  // without this an Escape meant for a nested sheet or an armed delete would
  // also close the Clickers sheet behind it. Capture phase runs first.
  useEffect(() => {
    if (editDevice === null && infoDevice === null && armedDeleteId === null) return undefined;
    const onEscape = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      event.stopImmediatePropagation();
      if (editDevice !== null) setEditDevice(null);
      else if (infoDevice !== null) setInfoDevice(null);
      else setArmedDeleteId(null);
    };
    window.addEventListener('keydown', onEscape, true);
    return () => window.removeEventListener('keydown', onEscape, true);
  }, [editDevice, infoDevice, armedDeleteId]);

  const handleDisarmDelete = useCallback(() => setArmedDeleteId(null), []);

  /** Opening a row disarms any other row's delete; closing a row disarms its own. */
  const handleSwipeOpenChange = (deviceId: string, open: boolean) => {
    setOpenSwipeId(open ? deviceId : null);
    setArmedDeleteId((armed) => {
      const armedElsewhere = open ? armed !== deviceId : armed === deviceId;
      return armedElsewhere ? null : armed;
    });
  };

  const handleDeleteCommit = async (deviceId: string) => {
    setArmedDeleteId(null);
    setOpenSwipeId(null);
    // Close a sheet that shows the clicker being deleted.
    setInfoDevice((shown) => (shown?.device_id === deviceId ? null : shown));
    setEditDevice((shown) => (shown?.device_id === deviceId ? null : shown));
    try {
      await deleteClicker(deviceId);
    } catch {
      // The hook already showed the error toast.
    }
  };

  return (
    <div className={`${listStyles.container} ${styles.fleet}`} id="clickerFleet">
      <div className={listStyles.rowb}>
        <b>Clickers</b>
        <span id="clickersCount">{`${withStudent} de ${devices.length} con alumno`}</span>
      </div>

      <ClickerAddForm onRegister={registerClicker} />

      <ToastViewport toasts={toasts} onDismiss={(id) => dismissToast(id)} />

      {loading ? (
        <DataList id="clickersList" ariaLabel="Clickers" busy isEmpty={false}>
          {Array.from({ length: SKELETON_ROWS }, (_, index) => (
            <div key={`clicker-skeleton-${index}`} role="listitem" className={styles.skeletonRow}>
              <Skeleton className={styles.skeletonId} />
              <Skeleton className={styles.skeletonTags} />
            </div>
          ))}
        </DataList>
      ) : (
        <DataList
          id="clickersList"
          ariaLabel="Clickers"
          isEmpty={devices.length === 0}
          emptyText="Todavía no hay clickers. Agregue uno con el código de su etiqueta."
        >
          {devices.map((device) => (
            <ClickerRow
              key={device.device_id}
              device={device}
              confirmArmed={armedDeleteId === device.device_id}
              swipeOpen={openSwipeId === device.device_id}
              onOpenInfo={(row) => setInfoDevice(row)}
              onOpenEdit={(row) => setEditDevice(row)}
              onArmDelete={(deviceId) => setArmedDeleteId(deviceId)}
              onCommitDelete={(deviceId) => void handleDeleteCommit(deviceId)}
              onDisarmDelete={handleDisarmDelete}
              onOpenChange={(open) => handleSwipeOpenChange(device.device_id, open)}
            />
          ))}
        </DataList>
      )}

      <ClickerInfoSheet device={infoDevice} onClose={() => setInfoDevice(null)} />
      <ClickerEditSheet
        device={editDevice}
        devices={devices}
        students={students}
        onClose={() => setEditDevice(null)}
        onAssign={assignStudent}
        onUnassign={unassignStudent}
      />
    </div>
  );
};
