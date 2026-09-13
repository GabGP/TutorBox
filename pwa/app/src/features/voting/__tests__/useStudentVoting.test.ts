import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useStudentVoting } from '../useStudentVoting';
import { votingApi } from '../votingApi';

vi.mock('../votingApi', () => ({
  votingApi: {
    submitVote: vi.fn(),
  },
}));

describe('useStudentVoting Hook', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('records votes optimistically and calls votingApi', async () => {
    vi.mocked(votingApi.submitVote).mockResolvedValue({
      vote_id: 'v1',
      round_id: 'r1',
      selected_option: 'B',
      recorded_at: new Date().toISOString(),
    });

    const { result } = renderHook(() => useStudentVoting('s1', 'r1'));

    await act(async () => {
      await result.current.castVote('B');
    });

    expect(votingApi.submitVote).toHaveBeenCalledWith(
      's1',
      expect.objectContaining({
        selected_option: 'B',
        transport_type: 'web',
      })
    );
    expect(result.current.votes['r1']).toBe('B');
    expect(result.current.currentVote).toBe('B');
  });

  it('records hits and computes score accurately', () => {
    const { result } = renderHook(() => useStudentVoting('s1', 'r1'));

    act(() => {
      result.current.recordHit('r1', true);
      result.current.recordHit('r2', false);
      result.current.recordHit('r3', true);
    });

    expect(result.current.score).toBe(2);
  });

  it('recovers from 409 Conflict by recording vote locally so student advances', async () => {
    vi.mocked(votingApi.submitVote).mockRejectedValue({
      status: 409,
      detail: 'Vote already cast in this round.',
    });

    const { result } = renderHook(() => useStudentVoting('s1', 'r1'));

    await act(async () => {
      await result.current.castVote('C');
    });

    expect(result.current.votes['r1']).toBe('C');
    expect(result.current.currentVote).toBe('C');
  });
});
