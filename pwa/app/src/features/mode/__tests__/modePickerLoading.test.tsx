import { act, fireEvent, render, renderHook, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { ModelResidency } from '../../model-residency/residency.types';
import { ModePicker } from '../ModePicker';
import { modeApi } from '../modeApi';
import { useApplianceMode } from '../useApplianceMode';

afterEach(() => vi.restoreAllMocks());

const LOADING = 'Cargando el modelo del tutor…';

describe('ModePicker while the tutor model loads', () => {
  it('shows a spinner with the loading text on the tutor card only', () => {
    render(<ModePicker mode="quiz" saving pendingMode="tutor" onChange={vi.fn()} />);

    expect(screen.getByRole('status', { name: LOADING })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: new RegExp(LOADING) })).toBeInTheDocument();
    expect(screen.getAllByRole('status')).toHaveLength(1);
  });

  it('disables every card while the switch is pending', () => {
    render(<ModePicker mode="quiz" saving pendingMode="tutor" onChange={vi.fn()} />);

    for (const name of [/Quiz/, /Tutor/, /Llevar a casa/]) {
      expect(screen.getByRole('button', { name })).toBeDisabled();
    }
  });

  it('shows the hint again once the switch is answered', () => {
    render(<ModePicker mode="quiz" saving={false} pendingMode={null} onChange={vi.fn()} />);

    expect(screen.queryByRole('status')).toBeNull();
    expect(screen.getByRole('button', { name: /Tutor/ })).toHaveTextContent('Chat de práctica');
  });

  it('shows no spinner for a switch to take-home mode', () => {
    render(<ModePicker mode="tutor" saving pendingMode="apps" onChange={vi.fn()} />);

    expect(screen.queryByRole('status')).toBeNull();
  });
});

describe('useApplianceMode pending mode', () => {
  it('names the mode being saved until the server answers', async () => {
    let answer!: (value: { mode: 'tutor'; model: ModelResidency }) => void;
    vi.spyOn(modeApi, 'setMode').mockReturnValue(new Promise((settle) => (answer = settle)));
    const { result } = renderHook(() => useApplianceMode({ enabled: false }));

    let pending!: Promise<unknown>;
    act(() => {
      pending = result.current.setMode('tutor');
    });
    expect(result.current.pendingMode).toBe('tutor');
    expect(result.current.saving).toBe(true);

    await act(async () => {
      answer({ mode: 'tutor', model: { model: 'm', action: 'loaded', duration_ms: 500, detail: null } });
      await pending;
    });
    expect(result.current.pendingMode).toBeNull();
    expect(result.current.saving).toBe(false);
  });

  it('is cleared when the server refuses the switch', async () => {
    vi.spyOn(modeApi, 'setMode').mockRejectedValue(new Error('refused'));
    const { result } = renderHook(() => useApplianceMode({ enabled: false }));

    await act(() => result.current.setMode('tutor'));

    expect(result.current.pendingMode).toBeNull();
  });
});

describe('ModePicker wiring', () => {
  it('still reports a choice when enabled', () => {
    const onChange = vi.fn();
    render(<ModePicker mode="quiz" saving={false} onChange={onChange} />);
    fireEvent.click(screen.getByRole('button', { name: /Tutor/ }));
    expect(onChange).toHaveBeenCalledWith('tutor');
  });
});
