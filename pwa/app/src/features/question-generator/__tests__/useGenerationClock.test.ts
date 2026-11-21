import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { GenerationProgress } from '../generator.types';
import { useGenerationClock } from '../useGenerationClock';

const T0 = new Date('2026-11-21T06:00:00Z').getTime();

function progress(extra: Partial<GenerationProgress> = {}): GenerationProgress {
  return { done: 0, total: 3, failed: 0, ids: [], eta: 10, currentIndex: 1, ...extra };
}

describe('useGenerationClock', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(T0);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('goes on from the batch start when the card mounts again after a tab switch', () => {
    const running = progress({ startedAtMs: T0, questionStartedAtMs: T0 + 20_000, currentIndex: 2 });
    const first = renderHook(() => useGenerationClock(running, false));
    act(() => {
      vi.advanceTimersByTime(30_000);
    });
    expect(first.result.current.elapsedSeconds).toBe(30);
    first.unmount();

    // Ten seconds on another tab, then back: the clock does not start from zero.
    vi.setSystemTime(T0 + 40_000);
    const second = renderHook(() => useGenerationClock(running, false));

    expect(second.result.current.elapsedSeconds).toBe(40);
    expect(second.result.current.questionStartSecond).toBe(20);
  });

  it('stays at the batch length once the batch has ended', () => {
    const finished = progress({ done: 3, startedAtMs: T0, finishedAtMs: T0 + 75_000 });
    vi.setSystemTime(T0 + 300_000);

    const { result } = renderHook(() => useGenerationClock(finished, true));
    act(() => {
      vi.advanceTimersByTime(5_000);
    });

    expect(result.current.elapsedSeconds).toBe(75);
  });

  it('counts from when the card mounted for a progress without batch times', () => {
    const { result, rerender } = renderHook(({ value }) => useGenerationClock(value, false), {
      initialProps: { value: progress() },
    });
    act(() => {
      vi.advanceTimersByTime(12_000);
    });
    expect(result.current.elapsedSeconds).toBe(12);

    rerender({ value: progress({ currentIndex: 2, done: 1 }) });
    act(() => {
      vi.advanceTimersByTime(1_000);
    });

    // The new question started 12 s in; the next tick shows it.
    expect(result.current.questionStartSecond).toBe(12);
    expect(result.current.elapsedSeconds).toBe(13);
  });
});
