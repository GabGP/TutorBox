import { act, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../../../shared/api/httpClient';
import { ClickerFleetView } from '../ClickerFleetView';
import { CLICKER_REFRESH_INTERVAL_MS } from '../useClickerFleet';
import { clickerRow, flushRequests, installFakeFleet } from './clickerFixture';

/** 13 Oct 2026, 12:00 UTC: the clock the timestamps below are read against. */
const NOW_ISO = '2026-10-13T12:00:00Z';

/** Moves the fake clock forward and lets the reload it starts land. */
async function advanceFleetClock(milliseconds: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(milliseconds);
  });
}

describe('ClickerFleetView while the sheet stays open', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(NOW_ISO));
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('shows a clicker that switches on, with no action from the teacher', async () => {
    const fleet = installFakeFleet();
    render(<ClickerFleetView />);
    await flushRequests();
    expect(screen.queryByRole('button', { name: 'ESP32-N1' })).not.toBeInTheDocument();

    // The clicker connects to the appliance: the server now lists it, unassigned.
    fleet.devices.push({
      device_id: 'ESP32-N1',
      assigned_user_id: null,
      assigned_username: null,
      created_at: '2026-10-13 11:58:00',
      secret_issued_at: '2026-10-13 11:58:00',
    });
    await advanceFleetClock(CLICKER_REFRESH_INTERVAL_MS);

    expect(screen.getByRole('button', { name: 'ESP32-N1' })).toBeInTheDocument();
    expect(within(clickerRow('ESP32-N1')).getByText('Nuevo')).toBeInTheDocument();
    expect(screen.getByText('1 de 3 con alumno')).toBeInTheDocument();
    const faceLabels = screen
      .getAllByLabelText(/^Clicker /)
      .map((face) => face.getAttribute('aria-label'));
    expect(faceLabels[0]).toBe('Clicker ESP32-N1');
  });

  it('keeps the list out of the busy state during a periodic reload', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    await flushRequests();
    expect(screen.getByRole('list', { name: 'Clickers' })).not.toHaveAttribute('aria-busy');

    await advanceFleetClock(CLICKER_REFRESH_INTERVAL_MS);
    expect(screen.getByRole('list', { name: 'Clickers' })).not.toHaveAttribute('aria-busy');
  });

  it('keeps the rows and shows no error when a periodic reload fails', async () => {
    const fleet = installFakeFleet();
    render(<ClickerFleetView />);
    await flushRequests();

    fleet.failNext('GET', '/staff/devices', new ApiError('', 500));
    await advanceFleetClock(CLICKER_REFRESH_INTERVAL_MS);

    expect(screen.getByRole('button', { name: 'ESP32-A4CF12' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'ESP32-B7' })).toBeInTheDocument();
    expect(screen.queryByText('Error al cargar clickers')).not.toBeInTheDocument();
  });
});
