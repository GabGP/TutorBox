import { afterEach, describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { ApiError } from '../../../shared/api/httpClient';
import { presenceApi } from '../presenceApi';
import { MIXED_CLASS } from './presenceFixture';

describe('presenceApi', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('sendHeartbeat posts to the heartbeat path with no body', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({});
    await presenceApi.sendHeartbeat();
    expect(spy).toHaveBeenCalledWith('POST', '/presence/heartbeat');
  });

  it('sendHeartbeat accepts the 204 answer with an empty body', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })));
    await expect(presenceApi.sendHeartbeat()).resolves.toBeUndefined();
    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/presence/heartbeat',
      expect.objectContaining({ method: 'POST' })
    );
  });

  it('sendHeartbeat rejects when the server refuses, so the caller can ignore it', async () => {
    vi.spyOn(httpClient, 'requestApi').mockRejectedValue(new ApiError('Sin conexión', 0));
    await expect(presenceApi.sendHeartbeat()).rejects.toThrow('Sin conexión');
  });

  it('getClassPresence reads the class list and returns it unchanged', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue(MIXED_CLASS);
    await expect(presenceApi.getClassPresence()).resolves.toEqual(MIXED_CLASS);
    expect(spy).toHaveBeenCalledWith('GET', '/presence/class');
  });
});
