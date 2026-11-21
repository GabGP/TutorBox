import { afterEach, describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { generatorApi } from '../generatorApi';

afterEach(() => vi.restoreAllMocks());

describe('generatorApi quiz model calls', () => {
  it('asks the server to load the quiz model before a batch', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({ action: 'loaded' });

    await expect(generatorApi.loadQuizModel()).resolves.toEqual({ action: 'loaded' });

    expect(spy).toHaveBeenCalledWith('POST', '/quiz/model/load');
  });

  it('asks the server to unload the quiz model when the batch ends', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({ action: 'unloaded' });

    await expect(generatorApi.unloadQuizModel()).resolves.toEqual({ action: 'unloaded' });

    expect(spy).toHaveBeenCalledWith('POST', '/quiz/model/unload');
  });
});
