import { useCallback, useEffect, useState } from 'react';
import { toErrorMessage } from '../../shared/lib/errors';
import type { ToastPush } from '../../shared/ui/Toast/toast.types';
import { useToastQueue } from '../../shared/ui/Toast/useToastQueue';
import { rosterApi } from '../roster/rosterApi';
import type { RosterStudent } from '../roster/roster.types';
import { clickersApi } from './clickersApi';
import { studentKey } from './clickerStudentOptions';
import {
  assignErrorMessage,
  CLICKER_LOAD_ERROR,
  deleteErrorMessage,
  registerErrorMessage,
  unassignErrorMessage,
} from './clickerErrors';
import type { ClickerDevice } from './clickers.types';

/**
 * Teacher clicker fleet state. Loads the devices and the students once, then
 * runs each mutation: success or failure both reload the device list, so a
 * moved student's old clicker shows its new state. A failure pushes an error
 * toast and rethrows (as useRosterManager does) so the caller can keep its
 * sheet open.
 *
 * @returns {object} Devices, students, loading flag, toasts and the four mutations.
 */
export function useClickerFleet() {
  const [devices, setDevices] = useState<ClickerDevice[]>([]);
  const [students, setStudents] = useState<RosterStudent[]>([]);
  const [loading, setLoading] = useState(true);
  const { toasts, pushToast: queueToast, dismissToast, clearToasts } = useToastQueue();

  // Only the latest message shows: each new toast replaces the one before it,
  // so a burst of successes cannot cover the list. useToastQueue(1) would not
  // do this: its cap is slice(-(limit - 1)), and slice(-0) keeps every toast.
  const pushToast = useCallback(
    (toast: ToastPush) => {
      clearToasts();
      return queueToast(toast);
    },
    [clearToasts, queueToast]
  );

  const fail = useCallback(
    (message: string) => pushToast({ message, tone: 'error' }),
    [pushToast]
  );

  const refreshDevices = useCallback(async () => {
    try {
      setDevices(await clickersApi.listDevices());
    } catch (err: unknown) {
      fail(toErrorMessage(err, CLICKER_LOAD_ERROR));
    }
  }, [fail]);

  useEffect(() => {
    let active = true;
    Promise.all([clickersApi.listDevices(), rosterApi.getStudents()])
      .then(([loadedDevices, loadedStudents]) => {
        if (!active) return;
        setDevices(loadedDevices);
        setStudents(loadedStudents);
      })
      .catch((err: unknown) => {
        if (active) fail(toErrorMessage(err, CLICKER_LOAD_ERROR));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [fail]);

  /** Runs one mutation, toasts its outcome and reloads the device list. */
  const runMutation = async (
    request: () => Promise<unknown>,
    successMessage: string,
    mapError: (err: unknown) => string
  ) => {
    try {
      await request();
    } catch (err: unknown) {
      const message = mapError(err);
      fail(message);
      await refreshDevices();
      throw new Error(message);
    }
    pushToast({ message: successMessage });
    await refreshDevices();
  };

  const registerClicker = (deviceId: string) =>
    runMutation(
      () => clickersApi.registerDevice(deviceId),
      `Clicker ${deviceId} agregado.`,
      registerErrorMessage
    );

  const assignStudent = (deviceId: string, student: RosterStudent) =>
    runMutation(
      () => clickersApi.assignDevice(deviceId, studentKey(student)),
      `${deviceId} asignado a ${student.username}.`,
      assignErrorMessage
    );

  const unassignStudent = (deviceId: string) =>
    runMutation(
      () => clickersApi.unassignDevice(deviceId),
      `${deviceId} quedó sin alumno.`,
      unassignErrorMessage
    );

  const deleteClicker = (deviceId: string) =>
    runMutation(
      () => clickersApi.deleteDevice(deviceId),
      `Clicker ${deviceId} eliminado.`,
      deleteErrorMessage
    );

  return {
    devices,
    students,
    loading,
    toasts,
    dismissToast,
    registerClicker,
    assignStudent,
    unassignStudent,
    deleteClicker,
  };
}
