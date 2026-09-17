import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ttsApi } from '../speechApi';
import { useTTSLifecycle } from '../useTTSLifecycle';

describe('useTTSLifecycle Hook', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('initializes in unloaded state', () => {
    const { result } = renderHook(() => useTTSLifecycle());
    expect(result.current.isLoaded).toBe(false);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.activeEngine).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('checks status correctly', async () => {
    vi.spyOn(ttsApi, 'getStatus').mockResolvedValue({
      engine: 'piper',
      loaded: true,
      model_id: 'es-voice',
    });

    const { result } = renderHook(() => useTTSLifecycle());

    await act(async () => {
      const loaded = await result.current.checkStatus('piper', 'es');
      expect(loaded).toBe(true);
    });

    expect(result.current.isLoaded).toBe(true);
    expect(result.current.activeEngine).toBe('piper');
  });

  it('preloadIfUnloaded does nothing if already loaded', async () => {
    vi.spyOn(ttsApi, 'getStatus').mockResolvedValue({
      engine: 'piper',
      loaded: true,
      model_id: 'es-voice',
    });
    const loadSpy = vi.spyOn(ttsApi, 'load');

    const { result } = renderHook(() => useTTSLifecycle());

    await act(async () => {
      const success = await result.current.preloadIfUnloaded('es', 'piper');
      expect(success).toBe(true);
    });

    expect(loadSpy).not.toHaveBeenCalled();
    expect(result.current.isLoaded).toBe(true);
  });

  it('preloadIfUnloaded calls load if not currently loaded', async () => {
    vi.spyOn(ttsApi, 'getStatus').mockResolvedValue({
      engine: 'piper',
      loaded: false,
      model_id: 'es-voice',
    });
    const loadSpy = vi.spyOn(ttsApi, 'load').mockResolvedValue({
      engine: 'piper',
      loaded: true,
      model_id: 'es-voice',
      load_ms: 150,
    });

    const { result } = renderHook(() => useTTSLifecycle());

    await act(async () => {
      const success = await result.current.preloadIfUnloaded('es', 'piper');
      expect(success).toBe(true);
    });

    expect(loadSpy).toHaveBeenCalledWith({ lang: 'es', engine: 'piper', voice: undefined });
    expect(result.current.isLoaded).toBe(true);
    expect(result.current.activeEngine).toBe('piper');
  });

  it('unloadIfLoaded calls unload when currently loaded', async () => {
    vi.spyOn(ttsApi, 'getStatus').mockResolvedValue({
      engine: 'piper',
      loaded: true,
      model_id: 'es-voice',
    });
    const unloadSpy = vi.spyOn(ttsApi, 'unload').mockResolvedValue({
      engine: 'piper',
      loaded: false,
    });

    const { result } = renderHook(() => useTTSLifecycle());

    await act(async () => {
      const success = await result.current.unloadIfLoaded('piper');
      expect(success).toBe(true);
    });

    expect(unloadSpy).toHaveBeenCalledWith({ engine: 'piper' });
    expect(result.current.isLoaded).toBe(false);
  });

  it('unloadIfLoaded does not call unload if already unloaded', async () => {
    vi.spyOn(ttsApi, 'getStatus').mockResolvedValue({
      engine: 'piper',
      loaded: false,
      model_id: 'es-voice',
    });
    const unloadSpy = vi.spyOn(ttsApi, 'unload');

    const { result } = renderHook(() => useTTSLifecycle());

    await act(async () => {
      const success = await result.current.unloadIfLoaded('piper');
      expect(success).toBe(true);
    });

    expect(unloadSpy).not.toHaveBeenCalled();
    expect(result.current.isLoaded).toBe(false);
  });

  it('handles load errors gracefully without throwing', async () => {
    vi.spyOn(ttsApi, 'getStatus').mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useTTSLifecycle());

    await act(async () => {
      const success = await result.current.preloadIfUnloaded('es');
      expect(success).toBe(false);
    });

    expect(result.current.error).toBe('Network error');
    expect(result.current.isLoading).toBe(false);
  });
});
