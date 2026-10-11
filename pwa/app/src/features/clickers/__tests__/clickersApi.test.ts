import { afterEach, describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { clickersApi } from '../clickersApi';

describe('clickersApi', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('listDevices gets the fleet and returns the server order', async () => {
    const devices = [
      { device_id: 'B', assigned_user_id: null, assigned_username: null, created_at: 'x', secret_issued_at: null },
    ];
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({ devices });
    await expect(clickersApi.listDevices()).resolves.toEqual(devices);
    expect(spy).toHaveBeenCalledWith('GET', '/staff/devices');
  });

  it('listDevices answers an empty list when the payload has no devices', async () => {
    vi.spyOn(httpClient, 'requestApi').mockResolvedValue({});
    await expect(clickersApi.listDevices()).resolves.toEqual([]);
  });

  it('registerDevice posts the hardware label as device_id', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({ device_id: 'ESP32-C3' });
    await clickersApi.registerDevice('ESP32-C3');
    expect(spy).toHaveBeenCalledWith('POST', '/staff/devices', { device_id: 'ESP32-C3' });
  });

  it('assignDevice posts a numeric user_id even when given a string id', async () => {
    const spy = vi
      .spyOn(httpClient, 'requestApi')
      .mockResolvedValue({ device_id: 'ESP32-A4CF12', assigned_user_id: 12, assigned_username: 'ana' });
    await clickersApi.assignDevice('ESP32-A4CF12', '12');
    expect(spy).toHaveBeenCalledWith('POST', '/staff/devices/ESP32-A4CF12/assign', { user_id: 12 });
  });

  it('unassignDevice posts to the unassign path with no body', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({ detail: 'ok' });
    await clickersApi.unassignDevice('ESP32-B7');
    expect(spy).toHaveBeenCalledWith('POST', '/staff/devices/ESP32-B7/unassign');
  });

  it('deleteDevice sends DELETE to the device path', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({ detail: 'ok' });
    await clickersApi.deleteDevice('ESP32-B7');
    expect(spy).toHaveBeenCalledWith('DELETE', '/staff/devices/ESP32-B7');
  });
});
