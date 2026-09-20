import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as soundModule from '../../../shared/lib/sound';
import { speechApi } from '../speechApi';
import { useSpeechPlayback } from '../useSpeechPlayback';

describe('useSpeechPlayback Hook', () => {
  let mockPlayer: {
    src: string;
    currentTime: number;
    play: () => Promise<void>;
    pause: () => void;
    onended: (() => void) | null;
    onerror: (() => void) | null;
  };

  beforeEach(() => {
    mockPlayer = {
      src: '',
      currentTime: 0,
      play: vi.fn().mockResolvedValue(undefined),
      pause: vi.fn(),
      onended: null,
      onerror: null,
    };
    vi.spyOn(soundModule, 'getAudioPlayer').mockReturnValue(mockPlayer as unknown as HTMLAudioElement);
    vi.spyOn(soundModule, 'unlockAudio').mockImplementation(() => {});
    vi.spyOn(soundModule, 'stopAudio').mockImplementation(() => {});
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:test-audio-url');
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
  });

  it('initializes in idle state', () => {
    const { result } = renderHook(() => useSpeechPlayback('s1'));
    expect(result.current.state).toBe('idle');
    expect(result.current.message).toBe('');
    expect(result.current.currentRound).toBe(-1);
  });

  it('fetches speech audio and sets playing state on success', async () => {
    vi.spyOn(speechApi, 'getSpeechBlobUrl').mockResolvedValue('blob:test-audio-url');

    const { result } = renderHook(() => useSpeechPlayback('s1', 'es'));

    await act(async () => {
      await result.current.speak(0);
    });

    expect(speechApi.getSpeechBlobUrl).toHaveBeenCalledWith('s1', 'es');
    expect(mockPlayer.src).toBe('blob:test-audio-url');
    expect(result.current.state).toBe('playing');
    expect(result.current.message).toBe('Leyendo la explicación en voz alta…');
    expect(result.current.currentRound).toBe(0);

    // Test onended callback
    act(() => {
      mockPlayer.onended?.();
    });
    expect(result.current.state).toBe('done');
    expect(result.current.message).toBe('Explicación leída.');
  });

  it('re-fetches the same round after the saved voice changes', async () => {
    localStorage.removeItem('tb_voice');
    vi.spyOn(speechApi, 'getSpeechBlobUrl').mockResolvedValue('blob:test-audio-url');

    const { result, rerender } = renderHook(() => useSpeechPlayback('s1', 'es'));

    await act(async () => {
      await result.current.speak(0);
    });
    expect(speechApi.getSpeechBlobUrl).toHaveBeenCalledTimes(1);
    expect(result.current.state).toBe('playing');

    // Simulate audio finishing -> state becomes done
    act(() => {
      mockPlayer.onended?.();
    });
    expect(result.current.state).toBe('done');

    // Change voice in storage and rerender
    localStorage.setItem(
      'tb_voice',
      JSON.stringify({ lang: 'es', engine: 'piper', voice: 'voz-x' })
    );
    act(() => {
      rerender();
    });
    expect(result.current.state).toBe('idle');
    expect(result.current.message).toBe('');

    await act(async () => {
      await result.current.speak(0);
    });
    expect(speechApi.getSpeechBlobUrl).toHaveBeenCalledTimes(2);
    localStorage.removeItem('tb_voice');
  });

  it('dedupes concurrent speak calls into a single fetch', async () => {
    let resolveFetch!: (url: string) => void;
    const gate = new Promise<string>((resolve) => {
      resolveFetch = resolve;
    });
    vi.spyOn(speechApi, 'getSpeechBlobUrl').mockReturnValue(gate);

    const { result } = renderHook(() => useSpeechPlayback('s1', 'es'));

    let p1!: Promise<void>;
    let p2!: Promise<void>;
    act(() => {
      p1 = result.current.speak(0);
      p2 = result.current.speak(0);
    });
    expect(speechApi.getSpeechBlobUrl).toHaveBeenCalledTimes(1);

    await act(async () => {
      resolveFetch('blob:test-audio-url');
      await p1;
      await p2;
    });
    expect(result.current.state).toBe('playing');
  });

  it('replays cached audio blob synchronously on subsequent call without re-fetching', async () => {
    vi.spyOn(speechApi, 'getSpeechBlobUrl').mockResolvedValue('blob:test-audio-url');

    const { result } = renderHook(() => useSpeechPlayback('s1', 'es'));

    await act(async () => {
      await result.current.speak(0);
    });

    expect(speechApi.getSpeechBlobUrl).toHaveBeenCalledTimes(1);

    // Call speak again for the same round
    await act(async () => {
      await result.current.speak(0);
    });

    expect(speechApi.getSpeechBlobUrl).toHaveBeenCalledTimes(1);
    expect(mockPlayer.currentTime).toBe(0);
    expect(result.current.state).toBe('playing');
  });

  it('handles autoplay policy blocks by setting blocked state', async () => {
    vi.spyOn(speechApi, 'getSpeechBlobUrl').mockResolvedValue('blob:test-audio-url');
    mockPlayer.play = vi.fn().mockRejectedValue(new Error('NotAllowedError'));

    const { result } = renderHook(() => useSpeechPlayback('s1', 'es'));

    await act(async () => {
      await result.current.speak(0);
    });

    expect(result.current.state).toBe('blocked');
    expect(result.current.message).toBe('Toque “Escuchar” para reproducir la explicación.');
  });

  it('handles 503 voice unavailable for Spanish and Kiche', async () => {
    vi.spyOn(speechApi, 'getSpeechBlobUrl').mockRejectedValue({ status: 503 });

    const { result: esResult } = renderHook(() => useSpeechPlayback('s1', 'es'));
    await act(async () => {
      await esResult.current.speak(0);
    });
    expect(esResult.current.state).toBe('error');
    expect(esResult.current.message).toBe('Este aparato no tiene voz instalada (espeak-ng).');

    const { result: qucResult } = renderHook(() => useSpeechPlayback('s1', 'quc'));
    await act(async () => {
      await qucResult.current.speak(0);
    });
    expect(qucResult.current.state).toBe('error');
    expect(qucResult.current.message).toBe("Todavía no hay voz en k'iche'; lea la explicación en voz alta.");
  });

  it('prefetches speech audio blob in background and plays synchronously on speak', async () => {
    vi.spyOn(speechApi, 'getSpeechBlobUrl').mockResolvedValue('blob:prefetched-audio-url');

    const { result } = renderHook(() => useSpeechPlayback('s1', 'es'));

    await act(async () => {
      await result.current.prefetch(0);
    });

    expect(speechApi.getSpeechBlobUrl).toHaveBeenCalledWith('s1', 'es');
    expect(result.current.state).toBe('idle');

    await act(async () => {
      await result.current.speak(0);
    });

    expect(speechApi.getSpeechBlobUrl).toHaveBeenCalledTimes(1);
    expect(mockPlayer.src).toBe('blob:prefetched-audio-url');
    expect(result.current.state).toBe('playing');
  });

  it('silently ignores errors during background prefetch', async () => {
    vi.spyOn(speechApi, 'getSpeechBlobUrl').mockRejectedValue({ status: 409 });

    const { result } = renderHook(() => useSpeechPlayback('s1', 'es'));

    await act(async () => {
      await result.current.prefetch(0);
    });

    expect(result.current.state).toBe('idle');
    expect(result.current.message).toBe('');
  });

  it('prefetches across consecutive rounds and plays cached audio without refetching', async () => {
    vi.spyOn(speechApi, 'getSpeechBlobUrl')
      .mockResolvedValueOnce('blob:round-0-url')
      .mockResolvedValueOnce('blob:round-1-url');

    const { result } = renderHook(() => useSpeechPlayback('s1', 'es'));

    await act(async () => {
      await result.current.speak(0);
    });
    expect(mockPlayer.src).toBe('blob:round-0-url');

    await act(async () => {
      await result.current.prefetch(1);
    });
    expect(speechApi.getSpeechBlobUrl).toHaveBeenCalledTimes(2);

    await act(async () => {
      await result.current.speak(1);
    });
    expect(speechApi.getSpeechBlobUrl).toHaveBeenCalledTimes(2);
    expect(mockPlayer.src).toBe('blob:round-1-url');
  });

  it('shares in-flight prefetch promise when speak is invoked before prefetch completes', async () => {
    let resolveApi: (url: string) => void = () => {};
    const delayedPromise = new Promise<string>((resolve) => {
      resolveApi = resolve;
    });
    vi.spyOn(speechApi, 'getSpeechBlobUrl').mockReturnValue(delayedPromise);

    const { result } = renderHook(() => useSpeechPlayback('s1', 'es'));

    await act(async () => {
      void result.current.prefetch(2);
    });
    expect(speechApi.getSpeechBlobUrl).toHaveBeenCalledTimes(1);

    let speakPromise!: Promise<void>;
    act(() => {
      speakPromise = result.current.speak(2);
    });
    expect(speechApi.getSpeechBlobUrl).toHaveBeenCalledTimes(1);

    await act(async () => {
      resolveApi('blob:in-flight-url');
      await speakPromise;
    });

    expect(speechApi.getSpeechBlobUrl).toHaveBeenCalledTimes(1);
    expect(mockPlayer.src).toBe('blob:in-flight-url');
  });

  it('stops playback and resets state on stopPlayback', async () => {
    vi.spyOn(speechApi, 'getSpeechBlobUrl').mockResolvedValue('blob:test-audio-url');

    const { result } = renderHook(() => useSpeechPlayback('s1', 'es'));

    await act(async () => {
      await result.current.speak(0);
    });

    act(() => {
      result.current.stopPlayback();
    });

    expect(result.current.state).toBe('idle');
    expect(result.current.message).toBe('');
    expect(soundModule.stopAudio).toHaveBeenCalled();
  });
});
