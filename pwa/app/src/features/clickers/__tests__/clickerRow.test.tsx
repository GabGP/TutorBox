import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { advanceHold, setupHoldTimers, teardownHoldTimers } from '../../../test/holdTimers';
import { ClickerRow, type ClickerRowProps } from '../ClickerRow';
import type { ClickerDevice } from '../clickers.types';

const assignedDevice: ClickerDevice = {
  device_id: 'ESP32-A4CF12',
  assigned_user_id: 1,
  assigned_username: 'ana',
  created_at: '2026-08-29 14:00:00',
  secret_issued_at: '2026-08-30 09:15:00',
};

const idleDevice: ClickerDevice = {
  device_id: 'ESP32-B7',
  assigned_user_id: null,
  assigned_username: null,
  created_at: '2026-08-29 14:05:00',
  secret_issued_at: null,
};

function renderRow(device: ClickerDevice, overrides: Partial<ClickerRowProps> = {}) {
  const handlers = {
    onOpenInfo: vi.fn(),
    onOpenEdit: vi.fn(),
    onArmDelete: vi.fn(),
    onCommitDelete: vi.fn(),
    onDisarmDelete: vi.fn(),
    onOpenChange: vi.fn(),
  };
  render(
    <ClickerRow
      device={device}
      confirmArmed={false}
      swipeOpen={false}
      {...handlers}
      {...overrides}
    />
  );
  return handlers;
}

describe('ClickerRow face', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('tapping the id opens the edit sheet for that clicker', () => {
    const { onOpenEdit } = renderRow(assignedDevice);
    fireEvent.click(screen.getByRole('button', { name: 'ESP32-A4CF12' }));
    expect(onOpenEdit).toHaveBeenCalledWith(assignedDevice);
  });

  it('labels the row with the clicker id', () => {
    renderRow(assignedDevice);
    expect(screen.getByLabelText('Clicker ESP32-A4CF12')).toBeInTheDocument();
  });

  it('shows the student username as a tag', () => {
    renderRow(assignedDevice);
    expect(screen.getByText('ana')).toBeInTheDocument();
    expect(screen.queryByText('Sin alumno')).not.toBeInTheDocument();
  });

  it('shows Sin alumno when the clicker holds no student', () => {
    renderRow(idleDevice);
    expect(screen.getByText('Sin alumno')).toBeInTheDocument();
  });

  it('marks a clicker never set up over Bluetooth with Sin configurar', () => {
    renderRow(idleDevice);
    expect(screen.getByText('Sin configurar')).toBeInTheDocument();
  });

  it('omits Sin configurar once a secret was issued', () => {
    renderRow(assignedDevice);
    expect(screen.queryByText('Sin configurar')).not.toBeInTheDocument();
  });

  it('treats a device without secret_issued_at (older backend) like one never set up', () => {
    const olderBackendDevice: ClickerDevice = {
      device_id: 'ESP32-LEGACY',
      assigned_user_id: 1,
      assigned_username: 'ana',
      created_at: '2026-08-29 14:00:00',
    };
    renderRow(olderBackendDevice);
    expect(screen.getByText('Sin configurar')).toBeInTheDocument();
  });

  it('offers Info, Editar and Eliminar in that order, with clicker-specific names', () => {
    renderRow(assignedDevice);
    const names = screen
      .getAllByRole('button')
      .map((button) => button.getAttribute('aria-label') ?? button.textContent);
    expect(names).toEqual([
      'Ver detalle clicker ESP32-A4CF12',
      'Editar clicker ESP32-A4CF12',
      'Eliminar',
      'ESP32-A4CF12',
    ]);
  });

  it('routes each swipe action to its own handler', () => {
    const { onOpenInfo, onOpenEdit, onArmDelete } = renderRow(assignedDevice);
    fireEvent.click(screen.getByRole('button', { name: 'Ver detalle clicker ESP32-A4CF12' }));
    expect(onOpenInfo).toHaveBeenCalledWith(assignedDevice);
    fireEvent.click(screen.getByRole('button', { name: 'Editar clicker ESP32-A4CF12' }));
    expect(onOpenEdit).toHaveBeenCalledWith(assignedDevice);
    fireEvent.click(screen.getByRole('button', { name: 'Eliminar' }));
    expect(onArmDelete).toHaveBeenCalledWith('ESP32-A4CF12');
  });
});

describe('ClickerRow armed delete', () => {
  afterEach(() => {
    teardownHoldTimers();
    vi.restoreAllMocks();
  });

  it('swaps the strip for the hold confirm and Cancelar', () => {
    renderRow(assignedDevice, { confirmArmed: true });
    expect(screen.getByRole('button', { name: 'Mantén para eliminar clicker ESP32-A4CF12' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancelar eliminación clicker ESP32-A4CF12' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Eliminar' })).not.toBeInTheDocument();
  });

  it('keeps the id readable while armed, so the teacher sees what is being deleted', () => {
    renderRow(assignedDevice, { confirmArmed: true });
    expect(screen.getByText('ESP32-A4CF12')).toBeInTheDocument();
  });

  it('Cancelar disarms without committing', () => {
    const { onDisarmDelete, onCommitDelete } = renderRow(assignedDevice, { confirmArmed: true });
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar eliminación clicker ESP32-A4CF12' }));
    expect(onDisarmDelete).toHaveBeenCalledTimes(1);
    expect(onCommitDelete).not.toHaveBeenCalled();
  });

  it('commits only after the full 2000ms hold', async () => {
    setupHoldTimers();
    const { onCommitDelete } = renderRow(assignedDevice, { confirmArmed: true });
    const holdButton = screen.getByRole('button', { name: 'Mantén para eliminar clicker ESP32-A4CF12' });
    fireEvent.pointerDown(holdButton, { pointerId: 1 });
    advanceHold(1999);
    expect(onCommitDelete).not.toHaveBeenCalled();
    advanceHold(1);
    await act(async () => {});
    expect(onCommitDelete).toHaveBeenCalledWith('ESP32-A4CF12');
    expect(screen.getByText('Eliminado')).toBeInTheDocument();
  });

  it('Escape disarms the armed delete', () => {
    const { onDisarmDelete } = renderRow(assignedDevice, { confirmArmed: true });
    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    });
    expect(onDisarmDelete).toHaveBeenCalled();
  });

  it('ignores Escape while nothing is armed', () => {
    const { onDisarmDelete } = renderRow(assignedDevice);
    act(() => {
      window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    });
    expect(onDisarmDelete).not.toHaveBeenCalled();
  });
});
