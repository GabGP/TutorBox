import { afterEach, describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { systemHealthApi } from '../systemHealthApi';
import { FULL_SNAPSHOT, RELEASE_REPORT } from './systemHealthFixture';

describe('systemHealthApi', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('reads one sample from the staff health path', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue(FULL_SNAPSHOT);

    await expect(systemHealthApi.getSnapshot()).resolves.toEqual(FULL_SNAPSHOT);
    expect(spy).toHaveBeenCalledWith('GET', '/system/health');
  });

  it('posts to the release path and returns the report', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue(RELEASE_REPORT);

    await expect(systemHealthApi.freeMemory()).resolves.toEqual(RELEASE_REPORT);
    expect(spy).toHaveBeenCalledWith('POST', '/system/free-memory');
  });
});
