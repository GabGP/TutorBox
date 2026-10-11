import { fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { advanceHold, setupHoldTimers, teardownHoldTimers } from '../../../test/holdTimers';
import { ClickerFleetView } from '../ClickerFleetView';
import { clickerRow, flushRequests, installFakeFleet, type FakeFleet } from './clickerFixture';

/** Removes a clicker from the fake server only, as if another teacher had deleted it. */
function deleteOnServer(fleet: FakeFleet, deviceId: string) {
  const index = fleet.devices.findIndex((device) => device.device_id === deviceId);
  if (index < 0) throw new Error(`El servidor no tiene ${deviceId}`);
  fleet.devices.splice(index, 1);
}

describe('ClickerFleetView when the server no longer has a clicker', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('a 404 on Quitar alumno toasts it and removes the stale row', async () => {
    const fleet = installFakeFleet();
    render(<ClickerFleetView />);
    fireEvent.click(await screen.findByRole('button', { name: 'ESP32-A4CF12' }));
    deleteOnServer(fleet, 'ESP32-A4CF12');
    fireEvent.click(screen.getByRole('button', { name: 'Quitar alumno' }));
    expect(await screen.findByText('Ese clicker ya no existe.')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'ESP32-A4CF12' })).not.toBeInTheDocument();
    expect(screen.getByText('0 de 1 con alumno')).toBeInTheDocument();
  });

  it('a 404 on delete toasts it and removes the stale row', async () => {
    const fleet = installFakeFleet();
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-B7' });
    fireEvent.click(within(clickerRow('ESP32-B7')).getByRole('button', { name: 'Eliminar' }));
    deleteOnServer(fleet, 'ESP32-B7');
    setupHoldTimers();
    try {
      const holdButton = screen.getByRole('button', { name: 'Mantén para eliminar clicker ESP32-B7' });
      fireEvent.pointerDown(holdButton, { pointerId: 1 });
      advanceHold(2000);
      await flushRequests();
    } finally {
      teardownHoldTimers();
    }
    expect(screen.getByText('Ese clicker ya no existe.')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'ESP32-B7' })).not.toBeInTheDocument();
    expect(screen.getByText('1 de 1 con alumno')).toBeInTheDocument();
  });
});

describe('ClickerFleetView toasts', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('after two quick successes only the latest toast is present', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-B7' });

    fireEvent.change(screen.getByLabelText('Código del clicker'), { target: { value: 'ESP32-C3' } });
    fireEvent.click(screen.getByRole('button', { name: 'Agregar' }));
    expect(await screen.findByText('Clicker ESP32-C3 agregado.')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Código del clicker'), { target: { value: 'ESP32-C4' } });
    fireEvent.click(screen.getByRole('button', { name: 'Agregar' }));
    expect(await screen.findByText('Clicker ESP32-C4 agregado.')).toBeInTheDocument();
    expect(screen.queryByText('Clicker ESP32-C3 agregado.')).not.toBeInTheDocument();
  });
});
