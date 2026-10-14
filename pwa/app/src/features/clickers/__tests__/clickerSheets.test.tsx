import { fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../../../shared/api/httpClient';
import type { RosterStudent } from '../../roster/roster.types';
import { ClickerFleetView } from '../ClickerFleetView';
import { formatClickerDate } from '../clickerFormat';
import type { ClickerDevice } from '../clickers.types';
import {
  clickerRow,
  FLEET_SEED,
  installFakeFleet,
  serverStudent,
  stringIdStudent,
} from './clickerFixture';

const HINT = 'El clicker vota como el alumno elegido. Cambiarlo no requiere volver a configurar el clicker.';

/** Opens a row's Info or Editar action from the strip, as a teacher would. */
async function openFromStrip(deviceId: string, action: 'Ver detalle' | 'Editar') {
  const button = await within(clickerRow(deviceId)).findByRole('button', {
    name: action === 'Editar' ? `Editar clicker ${deviceId}` : `Ver detalle clicker ${deviceId}`,
  });
  fireEvent.click(button);
}

function editSelect(): HTMLSelectElement {
  return screen.getByLabelText('Alumno del clicker') as HTMLSelectElement;
}

function chooseStudent(value: string) {
  fireEvent.change(editSelect(), { target: { value } });
}

/** The text next to a dt label inside a dialog (the Info sheet's facts). */
function factOf(dialog: HTMLElement, label: string): string | null {
  return within(dialog).getByText(label).nextElementSibling?.textContent ?? null;
}

describe('ClickerFleetView Info sheet', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows the student, the added date and the first contact date', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-A4CF12' });
    await openFromStrip('ESP32-A4CF12', 'Ver detalle');
    const dialog = screen.getByRole('dialog', { name: 'Detalle clicker ESP32-A4CF12' });
    expect(within(dialog).getByText('ESP32-A4CF12')).toBeInTheDocument();
    expect(factOf(dialog, 'Alumno')).toBe('ana');
    expect(factOf(dialog, 'Agregado')).toBe(formatClickerDate('2026-08-29 14:00:00'));
    expect(factOf(dialog, 'Primer contacto')).toBe(formatClickerDate('2026-08-30 09:15:00'));
  });

  it('an older backend without secret_issued_at says Todavía no and does not throw', async () => {
    const olderBackendDevice: ClickerDevice = {
      device_id: 'ESP32-LEGACY',
      assigned_user_id: null,
      assigned_username: null,
      created_at: '2026-08-29 14:05:00',
    };
    installFakeFleet({ devices: [olderBackendDevice] });
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-LEGACY' });
    expect(within(clickerRow('ESP32-LEGACY')).getByText('Sin conectar')).toBeInTheDocument();
    await openFromStrip('ESP32-LEGACY', 'Ver detalle');
    const dialog = screen.getByRole('dialog', { name: 'Detalle clicker ESP32-LEGACY' });
    expect(factOf(dialog, 'Primer contacto')).toBe('Todavía no');
  });

  it('says Sin alumno and Todavía no for an idle clicker that never connected', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-B7' });
    await openFromStrip('ESP32-B7', 'Ver detalle');
    const dialog = screen.getByRole('dialog', { name: 'Detalle clicker ESP32-B7' });
    expect(factOf(dialog, 'Alumno')).toBe('Sin alumno');
    expect(factOf(dialog, 'Primer contacto')).toBe('Todavía no');
  });
});

describe('ClickerFleetView edit sheet options', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('lists free students first, then holders labelled with their clicker', async () => {
    const unsortedStudents: RosterStudent[] = [
      serverStudent(4, 'diego'),
      serverStudent(2, 'beto'),
      serverStudent(1, 'ana'),
      serverStudent(3, 'carla'),
    ];
    installFakeFleet({
      students: unsortedStudents,
      devices: [
        { ...FLEET_SEED[0], device_id: 'ESP32-A4CF12', assigned_user_id: 4, assigned_username: 'diego' },
        { ...FLEET_SEED[0], device_id: 'ESP32-C2', assigned_user_id: 1, assigned_username: 'ana' },
        { ...FLEET_SEED[1], device_id: 'ESP32-B7' },
      ],
    });
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-B7' });
    fireEvent.click(screen.getByRole('button', { name: 'ESP32-B7' }));
    const labels = Array.from(editSelect().options).map((option) => option.textContent);
    expect(labels).toEqual([
      'Elija un alumno',
      'beto',
      'carla',
      'ana (tiene ESP32-C2)',
      'diego (tiene ESP32-A4CF12)',
    ]);
    expect(editSelect().options[0]).toBeDisabled();
    expect(editSelect()).toHaveValue('');
  });

  it('preselects the clicker student as plain text among the holders', async () => {
    installFakeFleet({
      students: [serverStudent(4, 'diego'), serverStudent(2, 'beto')],
      devices: [
        { ...FLEET_SEED[0], device_id: 'ESP32-A4CF12', assigned_user_id: 4, assigned_username: 'diego' },
      ],
    });
    render(<ClickerFleetView />);
    fireEvent.click(await screen.findByRole('button', { name: 'ESP32-A4CF12' }));
    const labels = Array.from(editSelect().options).map((option) => option.textContent);
    expect(labels).toEqual(['Elija un alumno', 'beto', 'diego']);
    expect(editSelect()).toHaveValue('4');
  });
});

describe('ClickerFleetView edit sheet actions', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('keeps Asignar disabled until a different student is chosen', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    fireEvent.click(await screen.findByRole('button', { name: 'ESP32-B7' }));
    const assign = screen.getByRole('button', { name: 'Asignar' });
    expect(assign).toBeDisabled();
    chooseStudent('2');
    expect(assign).toBeEnabled();
  });

  it('disables Asignar while the choice is already the clicker student', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    fireEvent.click(await screen.findByRole('button', { name: 'ESP32-A4CF12' }));
    const assign = screen.getByRole('button', { name: 'Asignar' });
    expect(assign).toBeDisabled();
    chooseStudent('3');
    expect(assign).toBeEnabled();
    chooseStudent('1');
    expect(assign).toBeDisabled();
  });

  it('posts the numeric student id, closes on success and toasts', async () => {
    const fleet = installFakeFleet();
    render(<ClickerFleetView />);
    fireEvent.click(await screen.findByRole('button', { name: 'ESP32-B7' }));
    chooseStudent('2');
    fireEvent.click(screen.getByRole('button', { name: 'Asignar' }));
    expect(await screen.findByText('ESP32-B7 asignado a beto.')).toBeInTheDocument();
    expect(fleet.requests).toContainEqual({
      method: 'POST',
      path: '/staff/devices/ESP32-B7/assign',
      body: { user_id: 2 },
    });
    expect(screen.queryByRole('dialog', { name: 'Editar clicker ESP32-B7' })).not.toBeInTheDocument();
  });

  it('moving a student leaves their old clicker Sin alumno after the reload', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    fireEvent.click(await screen.findByRole('button', { name: 'ESP32-B7' }));
    chooseStudent('1');
    fireEvent.click(screen.getByRole('button', { name: 'Asignar' }));
    expect(await screen.findByText('ESP32-B7 asignado a ana.')).toBeInTheDocument();
    expect(within(clickerRow('ESP32-A4CF12')).getByText('Sin alumno')).toBeInTheDocument();
    expect(within(clickerRow('ESP32-B7')).getByText('ana')).toBeInTheDocument();
  });

  it('shows Quitar alumno only for an assigned clicker, then unassigns and closes', async () => {
    const fleet = installFakeFleet();
    render(<ClickerFleetView />);
    fireEvent.click(await screen.findByRole('button', { name: 'ESP32-B7' }));
    expect(screen.queryByRole('button', { name: 'Quitar alumno' })).not.toBeInTheDocument();
    fireEvent.keyDown(document.body, { key: 'Escape' });
    fireEvent.click(screen.getByRole('button', { name: 'ESP32-A4CF12' }));
    fireEvent.click(screen.getByRole('button', { name: 'Quitar alumno' }));
    expect(await screen.findByText('ESP32-A4CF12 quedó sin alumno.')).toBeInTheDocument();
    expect(fleet.requests).toContainEqual({
      method: 'POST',
      path: '/staff/devices/ESP32-A4CF12/unassign',
      body: undefined,
    });
    expect(screen.queryByRole('dialog', { name: 'Editar clicker ESP32-A4CF12' })).not.toBeInTheDocument();
  });

  it('shows the hint under the actions', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    fireEvent.click(await screen.findByRole('button', { name: 'ESP32-B7' }));
    expect(screen.getByText(HINT)).toBeInTheDocument();
  });

  it.each([
    [new ApiError('', 404), 'Ese clicker o ese alumno ya no existe.'],
    [new ApiError('', 422), 'Solo se puede asignar a cuentas de alumno.'],
    [new ApiError('', 500), 'Error al asignar clicker'],
  ])('maps a failed assign to its message and keeps the sheet open', async (error, message) => {
    const fleet = installFakeFleet();
    fleet.failNext('POST', '/staff/devices/ESP32-B7/assign', error);
    render(<ClickerFleetView />);
    fireEvent.click(await screen.findByRole('button', { name: 'ESP32-B7' }));
    chooseStudent('2');
    fireEvent.click(screen.getByRole('button', { name: 'Asignar' }));
    expect(await screen.findByText(message)).toBeInTheDocument();
    expect(screen.getByRole('dialog', { name: 'Editar clicker ESP32-B7' })).toBeInTheDocument();
  });

  it.each([
    [new ApiError('', 404), 'Ese clicker ya no existe.'],
    [new ApiError('', 500), 'Error al quitar alumno'],
  ])('maps a failed unassign to its message and keeps the sheet open', async (error, message) => {
    const fleet = installFakeFleet();
    fleet.failNext('POST', '/staff/devices/ESP32-A4CF12/unassign', error);
    render(<ClickerFleetView />);
    fireEvent.click(await screen.findByRole('button', { name: 'ESP32-A4CF12' }));
    fireEvent.click(screen.getByRole('button', { name: 'Quitar alumno' }));
    expect(await screen.findByText(message)).toBeInTheDocument();
    expect(screen.getByRole('dialog', { name: 'Editar clicker ESP32-A4CF12' })).toBeInTheDocument();
  });

  it.each([
    ['the numeric ids the server sends', [serverStudent(2, 'beto')]],
    ['the string ids the roster type declares', [stringIdStudent('2', 'beto')]],
  ])('an enabled Asignar with %s always sends the assign request', async (_shape, students) => {
    const fleet = installFakeFleet({ students });
    render(<ClickerFleetView />);
    fireEvent.click(await screen.findByRole('button', { name: 'ESP32-B7' }));
    chooseStudent('2');
    const assign = screen.getByRole('button', { name: 'Asignar' });
    expect(assign).toBeEnabled();
    fireEvent.click(assign);
    expect(await screen.findByText('ESP32-B7 asignado a beto.')).toBeInTheDocument();
    expect(fleet.requests).toContainEqual(
      expect.objectContaining({
        method: 'POST',
        path: '/staff/devices/ESP32-B7/assign',
        body: { user_id: 2 },
      })
    );
  });

  it('explains that no student can be picked when the account list is empty', async () => {
    installFakeFleet({ students: [] });
    render(<ClickerFleetView />);
    fireEvent.click(await screen.findByRole('button', { name: 'ESP32-B7' }));
    expect(editSelect()).toBeDisabled();
    expect(screen.getByText('No hay alumnos registrados.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Asignar' })).toBeDisabled();
  });
});
