import { useCallback, useEffect, useRef, useState } from 'react';
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

/** How often the device list reloads while the sheet is open and the page is visible. */
export const CLICKER_REFRESH_INTERVAL_MS = 5000;

/**
 * Teacher clicker fleet state. Loads the devices and the students once, then
 * reloads the device list every CLICKER_REFRESH_INTERVAL_MS while the page is
 * visible, so a clicker that switches on shows up by itself. Each mutation
 * runs: success or failure both reload the device list, so a moved student's
 * old clicker shows its new state. A failure pushes an error toast and rethrows
 * (as useRosterManager does) so the caller can keep its sheet open. A failed
 * periodic reload is silent: the list stays and the next reload tries again.
 *
 * @returns {object} Devices, students, loading flag, toasts and the four mutations.
 */
export function useClickerFleet() {
  const [devices, setDevices] = useState<ClickerDevice[]>([]);
  const [students, setStudents] = useState<RosterStudent[]>([]);
  const [loading, setLoading] = useState(true);
  const { toasts, pushToast: queueToast, dismissToast, clearToasts } = useToastQueue();

  // Every device-list request takes the next number. An answer replaces the list
  // only when no newer request has already replaced it, so an older periodic
  // answer cannot overwrite a list that a mutation just reloaded.
  const requestCount = useRef(0);
  const shownRequest = useRef(0);
  // Turns false on unmount, so a late answer never touches state again.
  const isMounted = useRef(false);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

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

  /** Shows a device-list answer, unless a newer one is shown already or the sheet has closed. */
  const showDeviceList = useCallback((requestId: number, loaded: ClickerDevice[]) => {
    if (!isMounted.current || requestId <= shownRequest.current) return;
    shownRequest.current = requestId;
    setDevices(loaded);
  }, []);

  /**
   * Reloads the device list. A silent reload (the periodic one) shows no error
   * and keeps the list on screen; any other failure toasts the usual message.
   */
  const refreshDevices = useCallback(
    async ({ silent = false }: { silent?: boolean } = {}) => {
      requestCount.current += 1;
      const requestId = requestCount.current;
      try {
        showDeviceList(requestId, await clickersApi.listDevices());
      } catch (err: unknown) {
        if (!silent && isMounted.current) fail(toErrorMessage(err, CLICKER_LOAD_ERROR));
      }
    },
    [fail, showDeviceList]
  );

  useEffect(() => {
    requestCount.current += 1;
    const requestId = requestCount.current;
    Promise.all([clickersApi.listDevices(), rosterApi.getStudents()])
      .then(([loadedDevices, loadedStudents]) => {
        if (!isMounted.current) return;
        showDeviceList(requestId, loadedDevices);
        setStudents(loadedStudents);
      })
      .catch((err: unknown) => {
        if (isMounted.current) fail(toErrorMessage(err, CLICKER_LOAD_ERROR));
      })
      .finally(() => {
        if (isMounted.current) setLoading(false);
      });
  }, [fail, showDeviceList]);

  // Periodic reload while the sheet is open and the page is visible. Coming back
  // to the page reloads at once, because a phone that was locked may have
  // stopped its timer. The loading flag is never raised here.
  useEffect(() => {
    const reloadWhileVisible = () => {
      if (document.visibilityState === 'visible') void refreshDevices({ silent: true });
    };
    const timer = setInterval(reloadWhileVisible, CLICKER_REFRESH_INTERVAL_MS);
    document.addEventListener('visibilitychange', reloadWhileVisible);
    return () => {
      clearInterval(timer);
      document.removeEventListener('visibilitychange', reloadWhileVisible);
    };
  }, [refreshDevices]);

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
