import { beforeEach, describe, expect, it } from 'vitest';
import { storage } from '../storage';

describe('Typed Storage Adapter', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('stores and retrieves authentication token', () => {
    expect(storage.getToken()).toBeNull();
    storage.setToken('session-token-123');
    expect(storage.getToken()).toBe('session-token-123');
    storage.clearToken();
    expect(storage.getToken()).toBeNull();
  });

  it('stores and clears teacher session ID', () => {
    expect(storage.getTeacherSessionId()).toBeNull();
    storage.setTeacherSessionId('sess-teacher-99');
    expect(storage.getTeacherSessionId()).toBe('sess-teacher-99');
    storage.clearTeacherSessionId();
    expect(storage.getTeacherSessionId()).toBeNull();
  });

  it('stores last student session ID', () => {
    expect(storage.getLastStudentSessionId()).toBeNull();
    storage.setLastStudentSessionId('sess-last-42');
    expect(storage.getLastStudentSessionId()).toBe('sess-last-42');
  });

  it('handles student votes with safe JSON fallbacks', () => {
    expect(storage.getStudentVotes('s1')).toEqual({ votes: {}, hits: {} });

    storage.setStudentVotes('s1', {
      votes: { r1: 'A' },
      hits: { r1: true },
    });
    expect(storage.getStudentVotes('s1')).toEqual({
      votes: { r1: 'A' },
      hits: { r1: true },
    });

    localStorage.setItem('tb_votes_s2', 'invalid-json{');
    expect(storage.getStudentVotes('s2')).toEqual({ votes: {}, hits: {} });
  });

  it('handles round history with safe JSON fallbacks', () => {
    expect(storage.getRoundHistory('s1')).toEqual([]);

    const historyItem = {
      round_id: 'r1',
      text: '¿Cuánto es 2 + 2?',
      options: { A: '4', B: '5', C: '3', D: '22' },
      tally: {
        counts: { A: 10, B: 0, C: 0, D: 0 },
        total_votes: 10,
        correct_option: 'A',
        correct_count: 10,
        correct_percentage: 100,
      },
      explanations: {},
    };

    storage.setRoundHistory('s1', [historyItem]);
    expect(storage.getRoundHistory('s1')).toEqual([historyItem]);

    localStorage.setItem('tb_hist_s2', '{broken-json');
    expect(storage.getRoundHistory('s2')).toEqual([]);
  });
});
