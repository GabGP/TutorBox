import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../../../shared/api/httpClient';
import { SystemHealthView } from '../SystemHealthView';
import { systemHealthApi } from '../systemHealthApi';
import { EMPTY_SNAPSHOT, FULL_SNAPSHOT, RELEASE_REPORT } from './systemHealthFixture';

function region(name: string): HTMLElement {
  return screen.getByRole('region', { name });
}

describe('SystemHealthView readings', () => {
  beforeEach(() => {
    vi.spyOn(systemHealthApi, 'getSnapshot').mockResolvedValue(FULL_SNAPSHOT);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows each reading with its value and its status word', async () => {
    render(<SystemHealthView />);
    await screen.findByRole('region', { name: 'Procesador' });

    expect(within(region('Procesador')).getByText('36 % de uso')).toBeInTheDocument();
    expect(within(region('Procesador')).getByText('Bien')).toBeInTheDocument();
    expect(within(region('GPU')).getByText('100 % de carga')).toBeInTheDocument();
    expect(within(region('GPU')).getByText('Reloj: 306 MHz de 918 MHz')).toBeInTheDocument();
    expect(within(region('Memoria')).getByText('3,3 GB libres')).toBeInTheDocument();
    expect(within(region('Memoria')).getByText('Sin intercambio (swap)')).toBeInTheDocument();
    expect(within(region('Disco')).getByText('821,0 GB libres')).toBeInTheDocument();
    expect(within(region('Energía')).getByText('5,98 W en total')).toBeInTheDocument();
  });

  it('colours each temperature by its own status, and the card by the worst one', async () => {
    render(<SystemHealthView />);
    await screen.findByRole('region', { name: 'Temperaturas' });

    const temperatures = region('Temperaturas');
    expect(temperatures).toHaveAttribute('data-status', 'warn');
    expect(within(temperatures).getByText('Atención')).toBeInTheDocument();
    expect(within(temperatures).getByText('59,1 °C')).toBeInTheDocument();
    expect(within(temperatures).getByText('82,4 °C la más caliente')).toBeInTheDocument();
  });

  it('lists the cores, the models in memory and the voices loaded', async () => {
    render(<SystemHealthView />);
    await screen.findByRole('region', { name: 'Procesador' });

    expect(screen.getByRole('progressbar', { name: 'Uso del núcleo 1' })).toBeInTheDocument();
    expect(within(region('Modelos en memoria')).getByText('qwen2.5:3b')).toBeInTheDocument();
    expect(within(region('Modelos en memoria')).getByText('GPU 100 %')).toBeInTheDocument();
    expect(within(region('Voz cargada')).getByText('piper')).toBeInTheDocument();
    expect(screen.getByText('Carga media (1, 5 y 15 min): 3,32 · 4,45 · 3,74')).toBeInTheDocument();
  });

  it('shows a dash and no status for readings that the board could not give', async () => {
    vi.mocked(systemHealthApi.getSnapshot).mockResolvedValue(EMPTY_SNAPSHOT);
    render(<SystemHealthView />);
    await screen.findByRole('region', { name: 'Memoria' });

    expect(within(region('Memoria')).getByText('—')).toBeInTheDocument();
    expect(within(region('Memoria')).getByText('Sin datos')).toBeInTheDocument();
    expect(within(region('GPU')).getByText('Sin datos')).toBeInTheDocument();
    expect(within(region('Modelos en memoria')).getByText('Ninguno')).toBeInTheDocument();
    expect(within(region('Voz cargada')).getByText('Ninguna')).toBeInTheDocument();
    expect(region('Energía')).toHaveAttribute('data-status', 'none');
  });

  it('says how long ago the sample was taken', async () => {
    render(<SystemHealthView />);

    expect(await screen.findByText(/Actualizado hace \d+ s/)).toBeInTheDocument();
  });
});

describe('SystemHealthView release', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('frees the memory with a spinner, then toasts the summary and samples again', async () => {
    const getSnapshot = vi.spyOn(systemHealthApi, 'getSnapshot').mockResolvedValue(FULL_SNAPSHOT);
    let finish: (report: typeof RELEASE_REPORT) => void = () => undefined;
    vi.spyOn(systemHealthApi, 'freeMemory').mockReturnValue(
      new Promise((resolve) => {
        finish = resolve;
      })
    );
    render(<SystemHealthView />);
    await screen.findByRole('region', { name: 'Procesador' });

    fireEvent.click(screen.getByRole('button', { name: 'Liberar memoria' }));

    expect(screen.getByRole('status', { name: 'Liberando memoria…' })).toBeInTheDocument();
    // While the spinner runs, its label joins the button's accessible name.
    expect(screen.getByRole('button', { name: /Liberar memoria/ })).toBeDisabled();

    await act(async () => finish(RELEASE_REPORT));

    expect(await screen.findByText(/Memoria liberada: 2,3 GB\./)).toBeInTheDocument();
    expect(screen.getByText(/Recargado: modelo del tutor\./)).toBeInTheDocument();
    expect(screen.queryByRole('status', { name: 'Liberando memoria…' })).not.toBeInTheDocument();
    await waitFor(() => expect(getSnapshot).toHaveBeenCalledTimes(2));
  });

  it('toasts a warning when a step failed', async () => {
    vi.spyOn(systemHealthApi, 'getSnapshot').mockResolvedValue(FULL_SNAPSHOT);
    vi.spyOn(systemHealthApi, 'freeMemory').mockResolvedValue({
      ...RELEASE_REPORT,
      actions: [{ target: 'qwen2.5:3b', kind: 'quiz_model', action: 'failed', detail: 'down' }],
    });
    render(<SystemHealthView />);
    await screen.findByRole('region', { name: 'Procesador' });

    fireEvent.click(screen.getByRole('button', { name: 'Liberar memoria' }));

    expect(await screen.findByText('No se pudo: modelo de preguntas.')).toBeInTheDocument();
  });

  it('toasts the error when the release cannot be sent', async () => {
    vi.spyOn(systemHealthApi, 'getSnapshot').mockResolvedValue(FULL_SNAPSHOT);
    vi.spyOn(systemHealthApi, 'freeMemory').mockRejectedValue(new ApiError('Sin conexión con Utz\'tutor', 0));
    render(<SystemHealthView />);
    await screen.findByRole('region', { name: 'Procesador' });

    fireEvent.click(screen.getByRole('button', { name: 'Liberar memoria' }));

    expect(await screen.findByText("Sin conexión con Utz'tutor")).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Liberar memoria' })).toBeEnabled();
  });

  it('toasts the error when the first sample fails', async () => {
    vi.spyOn(systemHealthApi, 'getSnapshot').mockRejectedValue(new ApiError('No tienes permiso para esto', 403));
    render(<SystemHealthView />);

    expect(await screen.findByText('No tienes permiso para esto')).toBeInTheDocument();
    expect(screen.getByText('Leyendo el estado…')).toBeInTheDocument();
  });
});
