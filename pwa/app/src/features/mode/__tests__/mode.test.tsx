import { act, fireEvent, render, renderHook, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { ApiError } from '../../../shared/api/httpClient';
import { StudentModeCard } from '../ModeCards';
import { ModePicker } from '../ModePicker';
import { modeApi } from '../modeApi';
import { useApplianceMode } from '../useApplianceMode';

afterEach(() => vi.restoreAllMocks());

describe('modeApi', () => {
  it('reads the mode without a token and sets it with one', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({ mode: 'apps' });
    expect(await modeApi.getMode()).toBe('apps');
    expect(spy).toHaveBeenCalledWith('GET', '/mode', undefined, false);
    await modeApi.setMode('tutor');
    expect(spy).toHaveBeenLastCalledWith('PUT', '/mode', { mode: 'tutor' });
  });
});

describe('useApplianceMode', () => {
  it('follows the mode the teacher picked', async () => {
    vi.spyOn(modeApi, 'getMode').mockResolvedValue('tutor');
    const { result } = renderHook(() => useApplianceMode({ pollingIntervalMs: 50 }));
    expect(result.current.mode).toBeNull();
    await waitFor(() => expect(result.current.mode).toBe('tutor'));
  });

  it('shows the backend reason when a switch is refused mid-game', async () => {
    vi.spyOn(modeApi, 'getMode').mockResolvedValue('quiz');
    vi.spyOn(modeApi, 'setMode').mockRejectedValue(
      new ApiError('Conflicto', 409, 'Termina el juego antes de cambiar de modo.')
    );
    const { result } = renderHook(() => useApplianceMode({ enabled: false }));
    await act(() => result.current.setMode('apps'));
    expect(result.current.error).toBe('Termina el juego antes de cambiar de modo.');
    expect(result.current.mode).toBeNull();
  });
});

describe('ModePicker', () => {
  it('marks the active mode and reports a new choice', () => {
    const onChange = vi.fn();
    render(<ModePicker mode="quiz" saving={false} error={null} onChange={onChange} />);
    expect(screen.getByRole('button', { name: /Quiz/ })).toHaveAttribute('aria-pressed', 'true');
    fireEvent.click(screen.getByRole('button', { name: /Llevar a casa/ }));
    expect(onChange).toHaveBeenCalledWith('apps');
  });

  it('treats an unknown mode (still loading) as the quiz', () => {
    render(<ModePicker mode={null} saving={false} error={null} onChange={vi.fn()} />);
    expect(screen.getByRole('button', { name: /Quiz/ })).toHaveAttribute('aria-pressed', 'true');
  });
});

describe('StudentModeCard', () => {
  it('sends take-home students to the download page', () => {
    render(<StudentModeCard mode="apps" />);
    expect(screen.getByRole('link', { name: 'Descargar la app' })).toHaveAttribute('href', '/descargas/');
  });

  it('tells students the tutor is coming soon', () => {
    render(<StudentModeCard mode="tutor" />);
    expect(screen.getByText('El tutor llega pronto')).toBeInTheDocument();
  });
});
