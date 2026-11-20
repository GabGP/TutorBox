import { render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ClickerFleetView } from '../ClickerFleetView';
import { clickerRow, installFakeFleet } from './clickerFixture';

const FAST_POLL_MS = 20;

function countClassListRequests(requests: { method: string; path: string }[]): number {
  return requests.filter((request) => request.method === 'GET' && request.path === '/presence/class').length;
}

describe('ClickerFleetView live status', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows each clicker status as the lobby does, and how many are connected', async () => {
    const fleet = installFakeFleet();
    fleet.setClickerStatus('ESP32-A4CF12', { status: 'online', seconds_ago: 1, signal: 'good', battery_pct: 80 });
    render(<ClickerFleetView presencePollingIntervalMs={FAST_POLL_MS} />);

    const row = await waitFor(() => clickerRow('ESP32-A4CF12'));
    expect(await within(row).findByRole('img', { name: 'Conectado' })).toBeInTheDocument();
    expect(within(row).getByRole('img', { name: 'Señal buena' })).toBeInTheDocument();
    expect(screen.getByText('· 1 conectados')).toBeInTheDocument();
    // A clicker nobody holds has no live status: the server only tracks assigned ones.
    expect(within(clickerRow('ESP32-B7')).queryByRole('img')).toBeNull();
  });

  it('follows the clicker as it drops', async () => {
    const fleet = installFakeFleet();
    fleet.setClickerStatus('ESP32-A4CF12', { status: 'online', seconds_ago: 1, signal: 'good' });
    render(<ClickerFleetView presencePollingIntervalMs={FAST_POLL_MS} />);
    await screen.findByRole('img', { name: 'Conectado' });

    fleet.setClickerStatus('ESP32-A4CF12', { status: 'dropped', seconds_ago: 14 });

    expect(await screen.findByRole('img', { name: 'Se cayó hace 14 s' })).toBeInTheDocument();
    expect(screen.getByText('· 0 conectados')).toBeInTheDocument();
  });

  it('stops asking for the status once the Clickers sheet closes', async () => {
    const fleet = installFakeFleet();
    const { unmount } = render(<ClickerFleetView presencePollingIntervalMs={FAST_POLL_MS} />);
    await waitFor(() => expect(countClassListRequests(fleet.requests)).toBeGreaterThanOrEqual(2));

    unmount();
    const afterClose = countClassListRequests(fleet.requests);
    await new Promise((resolve) => setTimeout(resolve, FAST_POLL_MS * 5));

    expect(countClassListRequests(fleet.requests)).toBe(afterClose);
  });
});
