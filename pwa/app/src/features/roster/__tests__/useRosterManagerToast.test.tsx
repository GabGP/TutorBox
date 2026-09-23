import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useRosterManager } from '../useRosterManager';
import { rosterApi } from '../rosterApi';

describe('useRosterManager toast migration', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('pushes delete confirmation to toasts, keeps inline pinNotice empty', async () => {
    vi.spyOn(rosterApi, 'deleteUser').mockResolvedValue(undefined);
    vi.spyOn(rosterApi, 'getStudents').mockResolvedValue([]);
    vi.spyOn(rosterApi, 'getAll').mockResolvedValue({ users: [] });

    const { result } = renderHook(() => useRosterManager({ enabled: false }));

    await act(async () => {
      await result.current.deleteStudent('u1', 'teacher1');
    });

    expect(result.current.pinNotice).toBeNull();
    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0].message).toBe('Cuenta de teacher1 eliminada.');
  });

  it('dismisses toasts without touching pinNotice', async () => {
    vi.spyOn(rosterApi, 'deleteUser').mockResolvedValue(undefined);
    vi.spyOn(rosterApi, 'getStudents').mockResolvedValue([]);
    vi.spyOn(rosterApi, 'getAll').mockResolvedValue({ users: [] });

    const { result } = renderHook(() => useRosterManager({ enabled: false }));

    await act(async () => {
      await result.current.deleteStudent('u1', 'teacher1');
    });
    const id = result.current.toasts[0].id;

    act(() => {
      result.current.dismissToast(id);
    });
    expect(result.current.toasts).toHaveLength(0);
    expect(result.current.pinNotice).toBeNull();
  });

  it('keeps PIN temporals inline (never as auto-dismiss toast)', async () => {
    vi.spyOn(rosterApi, 'resetPin').mockResolvedValue({ temporary_pin: '4321' });

    const { result } = renderHook(() => useRosterManager({ enabled: false }));

    await act(async () => {
      await result.current.resetStudentPin('u2', 'ana');
    });

    expect(result.current.pinNotice).toContain('4321');
    expect(result.current.toasts).toHaveLength(0);
  });

  it('floats mutation failures as error toasts', async () => {
    vi.spyOn(rosterApi, 'createStudent').mockRejectedValue({ status: 409 });
    vi.spyOn(rosterApi, 'getStudents').mockResolvedValue([]);
    vi.spyOn(rosterApi, 'getAll').mockResolvedValue({ users: [] });

    const { result } = renderHook(() => useRosterManager({ enabled: false }));

    await act(async () => {
      await expect(
        result.current.addStudent('ana', '1234')
      ).rejects.toThrow('Ese usuario ya existe');
    });

    expect(result.current.toasts).toHaveLength(1);
    expect(result.current.toasts[0].tone).toBe('error');
    expect(result.current.toasts[0].message).toBe('Ese usuario ya existe');
  });
});
