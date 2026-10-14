import { fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../../../shared/api/httpClient';
import { ClickerFleetView } from '../ClickerFleetView';
import { CLICKER_ID_ERROR } from '../clickerId';
import { FLEET_SEED, clickerRow, installFakeFleet } from './clickerFixture';

const EMPTY_TEXT = 'Encienda un clicker: aparece aquí solo.';

function typeClickerId(text: string) {
  fireEvent.change(screen.getByLabelText('Código del clicker'), { target: { value: text } });
}

function pressAgregar() {
  fireEvent.click(screen.getByRole('button', { name: 'Agregar' }));
}

describe('ClickerFleetView list', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows the title and how many clickers hold a student', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    expect(screen.getByText('Clickers')).toBeInTheDocument();
    expect(await screen.findByText('1 de 2 con alumno')).toBeInTheDocument();
  });

  it('marks the list busy with skeleton rows until the first load ends', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    const list = screen.getByRole('list', { name: 'Clickers' });
    expect(list).toHaveAttribute('aria-busy', 'true');
    expect(await screen.findByRole('button', { name: 'ESP32-A4CF12' })).toBeInTheDocument();
    expect(list).not.toHaveAttribute('aria-busy');
  });

  it('shows the empty text when the fleet has no clickers', async () => {
    installFakeFleet({ devices: [] });
    render(<ClickerFleetView />);
    expect(await screen.findByText(EMPTY_TEXT)).toBeInTheDocument();
    expect(screen.getByText('0 de 0 con alumno')).toBeInTheDocument();
  });

  it('lists the unassigned clickers first, newest first, then the assigned ones', async () => {
    installFakeFleet({
      devices: [
        { ...FLEET_SEED[0] },
        { ...FLEET_SEED[1] },
        { ...FLEET_SEED[1], device_id: 'ESP32-C1', created_at: '2026-10-01 09:00:00' },
      ],
    });
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-A4CF12' });
    const faceLabels = screen
      .getAllByLabelText(/^Clicker /)
      .map((face) => face.getAttribute('aria-label'));
    expect(faceLabels).toEqual([
      'Clicker ESP32-C1',
      'Clicker ESP32-B7',
      'Clicker ESP32-A4CF12',
    ]);
  });

  it('tags an idle clicker Sin alumno and a clicker that never connected Sin conectar', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-A4CF12' });
    const idle = within(clickerRow('ESP32-B7'));
    expect(idle.getByText('Sin alumno')).toBeInTheDocument();
    expect(idle.getByText('Sin conectar')).toBeInTheDocument();
    const assigned = within(clickerRow('ESP32-A4CF12'));
    expect(assigned.getByText('ana')).toBeInTheDocument();
    expect(assigned.queryByText('Sin conectar')).not.toBeInTheDocument();
  });

  it('shows the hint about new clickers under the add form', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    expect(screen.getByText('Los clickers nuevos aparecen solos al encenderlos.')).toBeInTheDocument();
    await screen.findByRole('button', { name: 'ESP32-A4CF12' });
  });

  it('toasts a failed load with the Spanish fallback', async () => {
    const fleet = installFakeFleet();
    fleet.failNext('GET', '/staff/devices', new ApiError('', 500));
    render(<ClickerFleetView />);
    expect(await screen.findByText('Error al cargar clickers')).toBeInTheDocument();
    expect(screen.getByText(EMPTY_TEXT)).toBeInTheDocument();
  });
});

describe('ClickerFleetView add form', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('uses the Spanish label, placeholder and input attributes', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    const input = screen.getByLabelText('Código del clicker');
    expect(input).toHaveAttribute('placeholder', 'Código de la etiqueta (ej. ESP32-A4CF12)');
    expect(input).toHaveAttribute('maxlength', '32');
    expect(input).toHaveAttribute('autocapitalize', 'off');
    expect(input).toHaveAttribute('autocorrect', 'off');
    expect(input).toHaveAttribute('spellcheck', 'false');
    await screen.findByRole('button', { name: 'ESP32-A4CF12' });
  });

  it('disables Agregar while the id is empty', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-A4CF12' });
    const button = screen.getByRole('button', { name: 'Agregar' });
    expect(button).toBeDisabled();
    typeClickerId('ESP32-C3');
    expect(button).toBeEnabled();
    typeClickerId('   ');
    expect(button).toBeDisabled();
  });

  it('posts the trimmed id, reloads the list and clears the field', async () => {
    const fleet = installFakeFleet();
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-A4CF12' });
    typeClickerId('  ESP32-C3 ');
    pressAgregar();
    expect(await screen.findByText('Clicker ESP32-C3 agregado.')).toBeInTheDocument();
    expect(fleet.requests).toContainEqual({
      method: 'POST',
      path: '/staff/devices',
      body: { device_id: 'ESP32-C3' },
    });
    expect(await screen.findByRole('button', { name: 'ESP32-C3' })).toBeInTheDocument();
    expect(screen.getByText('1 de 3 con alumno')).toBeInTheDocument();
    expect(screen.getByLabelText('Código del clicker')).toHaveValue('');
  });

  it('rejects a malformed id inline and sends nothing', async () => {
    const fleet = installFakeFleet();
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-A4CF12' });
    typeClickerId('ESP 32');
    pressAgregar();
    expect(screen.getByText(CLICKER_ID_ERROR)).toBeInTheDocument();
    expect(screen.getByLabelText('Código del clicker')).toHaveAttribute('aria-invalid', 'true');
    expect(fleet.requests.some((request) => request.method === 'POST')).toBe(false);
  });

  it('clears the inline error as the teacher edits the id', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-A4CF12' });
    typeClickerId('ESP/32');
    pressAgregar();
    expect(screen.getByText(CLICKER_ID_ERROR)).toBeInTheDocument();
    typeClickerId('ESP32');
    expect(screen.queryByText(CLICKER_ID_ERROR)).not.toBeInTheDocument();
  });

  it('toasts a duplicate as 409 and keeps the typed id', async () => {
    installFakeFleet();
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-A4CF12' });
    typeClickerId('ESP32-B7');
    pressAgregar();
    expect(await screen.findByText('Ese clicker ya está registrado.')).toBeInTheDocument();
    expect(screen.getByLabelText('Código del clicker')).toHaveValue('ESP32-B7');
  });

  it('toasts a 422 from the server with the id rule text', async () => {
    const fleet = installFakeFleet();
    fleet.failNext('POST', '/staff/devices', new ApiError('', 422));
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-A4CF12' });
    typeClickerId('ESP32-C3');
    pressAgregar();
    expect(await screen.findByText(CLICKER_ID_ERROR)).toBeInTheDocument();
  });

  it('shows the server message for other failures', async () => {
    const fleet = installFakeFleet();
    fleet.failNext('POST', '/staff/devices', new ApiError("Sin conexión con Utz'tutor", 0));
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-A4CF12' });
    typeClickerId('ESP32-C3');
    pressAgregar();
    expect(await screen.findByText("Sin conexión con Utz'tutor")).toBeInTheDocument();
  });

  it('falls back to the add error text when the failure has no message', async () => {
    const fleet = installFakeFleet();
    fleet.failNext('POST', '/staff/devices', new ApiError('', 500));
    render(<ClickerFleetView />);
    await screen.findByRole('button', { name: 'ESP32-A4CF12' });
    typeClickerId('ESP32-C3');
    pressAgregar();
    expect(await screen.findByText('Error al agregar clicker')).toBeInTheDocument();
  });
});
