import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { AuditView } from '../AuditView';
import { VoicePicker } from '../../speech/VoicePicker';

describe('AuditView', () => {
  it('lists audit entries', async () => {
    vi.spyOn(httpClient, 'requestApi').mockResolvedValue({
      logs: [
        {
          id: 3,
          actor_user_id: 1,
          action: 'user_created',
          target_user_id: 5,
          created_at: '2026-01-01',
        },
      ],
    });
    render(<AuditView />);
    await waitFor(() =>
      expect(screen.getByText(/user_created/)).toBeInTheDocument()
    );
    vi.restoreAllMocks();
  });

  it('floats load failures as error toasts', async () => {
    vi.spyOn(httpClient, 'requestApi').mockRejectedValue({ status: 500 });
    render(<AuditView />);
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(
        'Error al cargar auditoría'
      )
    );
    vi.restoreAllMocks();
  });
});

describe('VoicePicker', () => {
  it('loads voices for the language', async () => {    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
        if (path.startsWith('/tts/voices'))
          return [{ id: 'voz-es', lang: 'es', engine: 'piper' }];
        if (path.startsWith('/tts/status'))
          return { engine: 'piper', loaded: false, model_id: 'm' };
        return {};
      }
    );
    render(<VoicePicker />);
    await waitFor(() =>
      expect(screen.getByText(/piper · voz-es/)).toBeInTheDocument()
    );
    expect(
      httpClient.requestApi as unknown as ReturnType<typeof vi.fn>
    ).toHaveBeenCalledWith('GET', expect.stringContaining('/tts/voices'));
    vi.restoreAllMocks();
  });

  it('hides load/unload and any admin notice for non-admins', async () => {
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
        if (path.startsWith('/tts/voices'))
          return [{ id: 'voz-es', lang: 'es', engine: 'piper' }];
        if (path.startsWith('/tts/status'))
          return { engine: 'piper', loaded: false, model_id: 'm' };
        return {};
      }
    );
    render(<VoicePicker />);
    await waitFor(() =>
      expect(screen.getByText(/piper · voz-es/)).toBeInTheDocument()
    );
    expect(
      screen.queryByRole('button', { name: 'Cargar voz' })
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/Solo admins/)).not.toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it('previews the selected voice via POST /tts/preview', async () => {
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
        if (path.startsWith('/tts/voices'))
          return [{ id: 'voz-es', lang: 'es', engine: 'piper' }];
        if (path.startsWith('/tts/status'))
          return { engine: 'piper', loaded: false, model_id: 'm' };
        return {};
      }
    );
    const blobSpy = vi
      .spyOn(httpClient, 'requestBlobUrl')
      .mockResolvedValue('blob:preview');
    const playSpy = vi
      .spyOn(window.HTMLMediaElement.prototype, 'play')
      .mockResolvedValue(undefined);
    render(<VoicePicker />);
    await waitFor(() =>
      expect(screen.getByText(/piper · voz-es/)).toBeInTheDocument()
    );
    fireEvent.click(screen.getByRole('button', { name: /Escuchar/ }));
    await waitFor(() =>
      expect(blobSpy).toHaveBeenCalledWith('/tts/preview', 'POST', {
        lang: 'es',
        engine: 'piper',
        voice: 'voz-es',
      })
    );
    expect(playSpy).toHaveBeenCalled();
    vi.restoreAllMocks();
  });

  it('persists the voice only via explicit save', async () => {
    localStorage.removeItem('tb_voice');
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
        if (path.startsWith('/tts/voices'))
          return [{ id: 'voz-es', lang: 'es', engine: 'piper' }];
        if (path.startsWith('/tts/status'))
          return { engine: 'piper', loaded: false, model_id: 'm' };
        return {};
      }
    );
    render(<VoicePicker />);
    await waitFor(() =>
      expect(screen.getByText(/piper · voz-es/)).toBeInTheDocument()
    );
    // Selecting alone persists nothing.
    expect(localStorage.getItem('tb_voice')).toBeNull();
    fireEvent.click(
      screen.getByRole('button', { name: 'Guardar como predeterminada' })
    );
    await waitFor(() =>
      expect(JSON.parse(localStorage.getItem('tb_voice') || '{}')).toEqual({
        lang: 'es',
        engine: 'piper',
        voice: 'voz-es',
      })
    );
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: /Predeterminada/ })
      ).toBeInTheDocument()
    );
    expect(
      httpClient.requestApi as unknown as ReturnType<typeof vi.fn>
    ).toHaveBeenCalledWith('POST', '/tts/unload', {});
    vi.restoreAllMocks();
  });

  it('loads without a frontend unload: eviction is server-owned', async () => {
    const calls: Array<[string, string, unknown?]> = [];
    let resolveLoad!: (v: unknown) => void;
    const loadGate = new Promise<unknown>((resolve) => {
      resolveLoad = resolve;
    });
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (m: string, path: string, body?: unknown) => {
        calls.push([m, path, body]);
        if (path.startsWith('/tts/voices'))
          return [
            { id: 'voz-es', lang: 'es', engine: 'espeak' },
            { id: 'voz-pi', lang: 'es', engine: 'piper' },
          ];
        if (path.startsWith('/tts/status'))
          return { engine: 'espeak', loaded: true, model_id: 'm' };
        if (path.startsWith('/tts/load')) return loadGate;
        return {};
      }
    );
    render(<VoicePicker isAdmin />);
    await waitFor(() =>
      expect(screen.getByText(/piper · voz-pi/)).toBeInTheDocument()
    );
    fireEvent.change(screen.getByLabelText('Voz'), {
      target: { value: 'piper::voz-pi' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Cargar voz' }));
    // Busy state is visible while the server works…
    await waitFor(() =>
      expect(screen.getByRole('button', { name: /Cargando/ })).toBeInTheDocument()
    );
    expect(screen.queryByText(/Motor:/)).not.toBeInTheDocument();
    resolveLoad({ engine: 'piper', loaded: true, model_id: 'm2', load_ms: 5 });
    await waitFor(() =>
      expect(screen.getByText(/Voz cargada \(piper/)).toBeInTheDocument()
    );
    // …and the client never unloads first: the server evicts on load.
    expect(
      calls.some(([m, p]) => m === 'POST' && p === '/tts/unload')
    ).toBe(false);
    expect(calls).toContainEqual([
      'POST',
      '/tts/load',
      { lang: 'es', engine: 'piper', voice: 'voz-pi' },
    ]);
    vi.restoreAllMocks();
  });

  it('shows load/unload for admins', async () => {
    vi.spyOn(httpClient, 'requestApi').mockImplementation(
      async (_m: string, path: string) => {
        if (path.startsWith('/tts/voices'))
          return [{ id: 'voz-es', lang: 'es', engine: 'piper' }];
        if (path.startsWith('/tts/status'))
          return { engine: 'piper', loaded: false, model_id: 'm' };
        return {};
      }
    );
    render(<VoicePicker isAdmin />);
    await waitFor(() =>
      expect(
        screen.getByRole('button', { name: 'Cargar voz' })
      ).toBeInTheDocument()
    );
    expect(
      screen.getByRole('button', { name: 'Descargar' })
    ).toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it('floats voice load failures as error toasts', async () => {
    vi.spyOn(httpClient, 'requestApi').mockRejectedValue({ status: 500 });
    render(<VoicePicker />);
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(
        'Error al cargar voces'
      )
    );
    vi.restoreAllMocks();
  });
});
