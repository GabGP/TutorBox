import { requestApi } from '../../shared/api/httpClient';
import type { ClickerAssignment, ClickerDevice } from './clickers.types';

/** Path of one clicker under `/staff/devices` (requestApi adds the base path). */
function devicePath(deviceId: string): string {
  return `/staff/devices/${encodeURIComponent(deviceId)}`;
}

/**
 * API client for the teacher's clicker fleet (`/staff/devices`).
 * Deliberately has no secret call: this screen never issues or shows a
 * clicker secret.
 */
export const clickersApi = {
  /** Lists every clicker, in the order the server sorts them (by device id). */
  async listDevices(): Promise<ClickerDevice[]> {
    const res = await requestApi<{ devices: ClickerDevice[] }>('GET', '/staff/devices');
    return res.devices || [];
  },

  /** Adds a clicker by its hardware label. 409 when already registered. */
  async registerDevice(deviceId: string): Promise<ClickerDevice> {
    return requestApi<ClickerDevice>('POST', '/staff/devices', { device_id: deviceId });
  },

  /**
   * Gives the clicker to a student. The server moves the student: any other
   * clicker that student held is left unassigned. `userId` may be a numeric
   * string or a number; the body always carries a number.
   */
  async assignDevice(deviceId: string, userId: string): Promise<ClickerAssignment> {
    return requestApi<ClickerAssignment>('POST', `${devicePath(deviceId)}/assign`, {
      user_id: Number(userId),
    });
  },

  /** Takes the student off the clicker. */
  async unassignDevice(deviceId: string): Promise<{ detail: string }> {
    return requestApi<{ detail: string }>('POST', `${devicePath(deviceId)}/unassign`);
  },

  /** Removes the clicker from the fleet. */
  async deleteDevice(deviceId: string): Promise<{ detail: string }> {
    return requestApi<{ detail: string }>('DELETE', devicePath(deviceId));
  },
};
