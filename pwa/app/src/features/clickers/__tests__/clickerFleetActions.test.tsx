import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../../../shared/api/httpClient';
import { advanceHold, setupHoldTimers, teardownHoldTimers } from '../../../test/holdTimers';
import { ClickerFleetSheet } from '../ClickerFleetSheet';
import { ClickerFleetView } from '../ClickerFleetView';
import { clickerRow, flushRequests, installFakeFleet } from './clickerFixture';

function armDelete(deviceId: string) {
  fireEvent.click(within(clickerRow(deviceId)).getByRole('button', { name: 'Eliminar' }));
}

function holdToDelete(deviceId: string) {
  const holdButton = screen.getByRole('button', { name: `Mantén para eliminar clicker ${deviceId}` });
  fireEvent.pointerDown(holdButton, { pointerId: 1 });
  advanceHold(2000);
}

/** Opens a row's strip with a short left drag, as a teacher swiping it would. */
function swipeOpen(deviceId: string) {
  const face = screen.getByLabelText(`Clicker ${deviceId}`);
  fireEvent.pointerDown(face, { clientX: 250, pointerId: 1 });
  fireEvent.pointerMove(face, { clientX: 200 });
  fireEvent.pointerUp(face, { clientX: 200 });
}

function pressEscape() {
  fireEvent.keyDown(document.body, { key: 'Escape' });
}

describe('ClickerFleetView row actions', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('opens the edit sheet from the face and from the Editar action', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    fireEvent.click(await screen.findByRole('button', { name: 'ESP32-B7' }));
    expect(await screen.findByRole('dialog', { name: 'Editar clicker ESP32-B7' })).toBeInTheDocument();
    fireEvent.keyDown(document.body, { key: 'Escape' });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    fireEvent.click(within(clickerRow('ESP32-A4CF12')).getByRole('button', { name: 'Editar clicker ESP32-A4CF12' }));
    expect(screen.getByRole('dialog', { name: 'Editar clicker ESP32-A4CF12' })).toBeInTheDocument();
  });

  it('cancelling an armed delete keeps the row and sends nothing', async () => {
    const fleet = installFakeFleet();
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-B7' });
    armDelete('ESP32-B7');
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar eliminación clicker ESP32-B7' }));
    expect(screen.getByRole('button', { name: 'ESP32-B7' })).toBeInTheDocument();
    expect(within(clickerRow('ESP32-B7')).getByRole('button', { name: 'Eliminar' })).toBeInTheDocument();
    expect(fleet.requests.some((request) => request.method === 'DELETE')).toBe(false);
  });

  it('holding the armed row for 2000ms deletes the clicker and toasts', async () => {
    const fleet = installFakeFleet();
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-B7' });
    armDelete('ESP32-B7');
    setupHoldTimers();
    try {
      holdToDelete('ESP32-B7');
      await flushRequests();
      expect(fleet.requests).toContainEqual(
        expect.objectContaining({ method: 'DELETE', path: '/staff/devices/ESP32-B7' })
      );
      expect(screen.getByText('Clicker ESP32-B7 eliminado.')).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'ESP32-B7' })).not.toBeInTheDocument();
      expect(screen.getByText('1 de 1 con alumno')).toBeInTheDocument();
    } finally {
      teardownHoldTimers();
    }
  });

  it('a 404 on delete says the clicker is already gone', async () => {
    const fleet = installFakeFleet();
    fleet.failNext('DELETE', '/staff/devices/ESP32-B7', new ApiError('', 404));
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-B7' });
    armDelete('ESP32-B7');
    setupHoldTimers();
    try {
      holdToDelete('ESP32-B7');
      await flushRequests();
      expect(screen.getByText('Ese clicker ya no existe.')).toBeInTheDocument();
    } finally {
      teardownHoldTimers();
    }
  });

  it('other delete failures toast the delete error', async () => {
    const fleet = installFakeFleet();
    fleet.failNext('DELETE', '/staff/devices/ESP32-B7', new ApiError('', 500));
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-B7' });
    armDelete('ESP32-B7');
    setupHoldTimers();
    try {
      holdToDelete('ESP32-B7');
      await flushRequests();
      expect(screen.getByText('Error al eliminar clicker')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'ESP32-B7' })).toBeInTheDocument();
    } finally {
      teardownHoldTimers();
    }
  });

  it('opening another row disarms the first row delete', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-B7' });
    armDelete('ESP32-A4CF12');
    expect(screen.getByRole('button', { name: 'Mantén para eliminar clicker ESP32-A4CF12' })).toBeInTheDocument();
    swipeOpen('ESP32-B7');
    expect(screen.queryByRole('button', { name: 'Mantén para eliminar clicker ESP32-A4CF12' })).not.toBeInTheDocument();
    expect(within(clickerRow('ESP32-A4CF12')).getByRole('button', { name: 'Eliminar' })).toBeInTheDocument();
  });

  it('Escape disarms an armed delete', async () => {
    const fleet = installFakeFleet();
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-B7' });
    armDelete('ESP32-B7');
    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    });
    expect(screen.queryByRole('button', { name: 'Mantén para eliminar clicker ESP32-B7' })).not.toBeInTheDocument();
    expect(fleet.requests.some((request) => request.method === 'DELETE')).toBe(false);
  });

  it('a committed delete closes the sheet that shows that clicker', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    fireEvent.click(await screen.findByRole('button', { name: 'ESP32-B7' }));
    expect(screen.getByRole('dialog', { name: 'Editar clicker ESP32-B7' })).toBeInTheDocument();
    armDelete('ESP32-B7');
    setupHoldTimers();
    try {
      holdToDelete('ESP32-B7');
      await flushRequests();
      expect(screen.queryByRole('dialog', { name: 'Editar clicker ESP32-B7' })).not.toBeInTheDocument();
    } finally {
      teardownHoldTimers();
    }
  });
});

describe('ClickerFleetSheet Escape ordering', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('Escape cancels an armed delete and keeps the Clickers sheet open', async () => {
    const onClose = vi.fn();
    installFakeFleet();
    render(<ClickerFleetSheet onClose={onClose} />);
    await screen.findByRole('button', { name: 'ESP32-B7' });
    armDelete('ESP32-B7');
    pressEscape();
    expect(screen.queryByRole('button', { name: 'Mantén para eliminar clicker ESP32-B7' })).not.toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
    pressEscape();
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('Escape closes the edit sheet first, then the Clickers sheet', async () => {
    const onClose = vi.fn();
    installFakeFleet();
    render(<ClickerFleetSheet onClose={onClose} />);
    fireEvent.click(await screen.findByRole('button', { name: 'ESP32-B7' }));
    expect(screen.getByRole('dialog', { name: 'Editar clicker ESP32-B7' })).toBeInTheDocument();
    pressEscape();
    expect(screen.queryByRole('dialog', { name: 'Editar clicker ESP32-B7' })).not.toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
    pressEscape();
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

describe('clicker feature requests', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('never requests a secret route across a full flow', async () => {
    const fleet = installFakeFleet();
    render(<ClickerFleetSheet onClose={vi.fn()} />);
    await screen.findByRole('button', { name: 'ESP32-B7' });

    fireEvent.change(screen.getByLabelText('Código del clicker'), { target: { value: 'ESP32-C3' } });
    fireEvent.click(screen.getByRole('button', { name: 'Agregar' }));
    await screen.findByText('Clicker ESP32-C3 agregado.');

    fireEvent.click(within(clickerRow('ESP32-B7')).getByRole('button', { name: 'Ver detalle clicker ESP32-B7' }));
    expect(screen.getByRole('dialog', { name: 'Detalle clicker ESP32-B7' })).toBeInTheDocument();
    pressEscape();

    fireEvent.click(within(clickerRow('ESP32-B7')).getByRole('button', { name: 'Editar clicker ESP32-B7' }));
    fireEvent.change(screen.getByLabelText('Alumno del clicker'), { target: { value: '2' } });
    fireEvent.click(screen.getByRole('button', { name: 'Asignar' }));
    await screen.findByText('ESP32-B7 asignado a beto.');

    fireEvent.click(await screen.findByRole('button', { name: 'ESP32-B7' }));
    fireEvent.click(screen.getByRole('button', { name: 'Quitar alumno' }));
    await screen.findByText('ESP32-B7 quedó sin alumno.');

    armDelete('ESP32-C3');
    setupHoldTimers();
    try {
      holdToDelete('ESP32-C3');
      await flushRequests();
    } finally {
      teardownHoldTimers();
    }
    await screen.findByText('Clicker ESP32-C3 eliminado.');

    expect(fleet.requests.length).toBeGreaterThan(0);
    for (const request of fleet.requests) {
      expect(request.path).not.toContain('/secret');
      expect(request.path.startsWith('/staff/')).toBe(true);
    }
  });
});
