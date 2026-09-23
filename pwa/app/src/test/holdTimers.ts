import { act } from '@testing-library/react';
import { vi } from 'vitest';

/**
 * Scoped fake-timer + requestAnimationFrame mocks for HoldButton tests.
 * HoldButton completes off performance.now deltas delivered through rAF,
 * so suites install these only around the hold interaction (global fake
 * timers stall Testing Library waitFor used by async data loads).
 * Always pair setupHoldTimers with teardownHoldTimers (try/finally).
 */

let holdNow = 0;
let holdRafId = 0;
const holdRafCallbacks = new Map<number, FrameRequestCallback>();

function flushHoldRaf() {
  const pending = [...holdRafCallbacks.values()];
  holdRafCallbacks.clear();
  act(() => {
    pending.forEach((callback) => callback(holdNow));
  });
}

/** Moves mocked time forward and delivers pending hold frames. */
export function advanceHold(milliseconds: number) {
  act(() => {
    holdNow += milliseconds;
    vi.advanceTimersByTime(milliseconds);
  });
  flushHoldRaf();
}

/** Installs fake timers, a controllable clock, and stubbed rAF. */
export function setupHoldTimers() {
  holdNow = 0;
  holdRafId = 0;
  holdRafCallbacks.clear();
  vi.useFakeTimers();
  vi.spyOn(performance, 'now').mockImplementation(() => holdNow);
  vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => {
    holdRafId += 1;
    holdRafCallbacks.set(holdRafId, callback);
    return holdRafId;
  });
  vi.stubGlobal('cancelAnimationFrame', (id: number) => {
    holdRafCallbacks.delete(id);
  });
}

/** Restores real timers and unstubs globals. */
export function teardownHoldTimers() {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  vi.useRealTimers();
}
