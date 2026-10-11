import { act, fireEvent, render, renderHook, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { ApiError } from '../../../shared/api/httpClient';
import { tutorApi, type TutorStudent } from '../tutorApi';
import { TutorChat } from '../TutorChat';
import { TutorRoster } from '../TutorRoster';
import { TutorWall } from '../TutorWall';
import { useTutorChat } from '../useTutorChat';

const reply = { reply: '¿Por dónde empiezas?', kind: 'hint', hint_level: 0, used_model: true, topic: null };

beforeEach(() => {
  sessionStorage.clear();
  vi.spyOn(tutorApi, 'ping').mockResolvedValue({ status: 'ok' });
});

afterEach(() => vi.restoreAllMocks());

describe('tutorApi', () => {
  it('talks to the tutor endpoints', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({ students: [] });
    vi.mocked(tutorApi.ping).mockRestore();

    await tutorApi.send('23 + 45');
    expect(spy).toHaveBeenLastCalledWith('POST', '/tutor/message', { message: '23 + 45' });
    await tutorApi.reset();
    expect(spy).toHaveBeenLastCalledWith('POST', '/tutor/reset', {});
    await tutorApi.ping();
    expect(spy).toHaveBeenLastCalledWith('POST', '/tutor/ping', {});
    expect(await tutorApi.students()).toEqual([]);
    expect(spy).toHaveBeenLastCalledWith('GET', '/tutor/students');
    await tutorApi.summary();
    expect(spy).toHaveBeenLastCalledWith('GET', '/tutor/summary', undefined, false);
  });
});

describe('useTutorChat', () => {
  it('adds the question and the reply, and keeps them for the tab', async () => {
    vi.spyOn(tutorApi, 'send').mockResolvedValue(reply);
    const { result } = renderHook(() => useTutorChat('ana'));

    expect(await act(() => result.current.send('  23 + 45  '))).toBe(true);

    expect(result.current.messages).toEqual([
      { id: 1, role: 'student', text: '23 + 45' },
      { id: 2, role: 'tutor', text: '¿Por dónde empiezas?', kind: 'hint', hintLevel: 0 },
    ]);
    expect(JSON.parse(sessionStorage.getItem('tb_tutor_chat:ana') ?? '[]')).toHaveLength(2);
    expect(renderHook(() => useTutorChat('ana')).result.current.messages).toHaveLength(2);
  });

  it('ignores empty messages and shows why a message failed', async () => {
    const send = vi
      .spyOn(tutorApi, 'send')
      .mockRejectedValueOnce(new ApiError('Conflicto', 409, 'El tutor no está activo.'))
      .mockRejectedValueOnce(new Error('offline'));
    const { result } = renderHook(() => useTutorChat('ana'));

    expect(await act(() => result.current.send('   '))).toBe(false);
    expect(send).not.toHaveBeenCalled();

    await act(() => result.current.send('hola'));
    expect(result.current.error).toBe('El tutor no está activo.');
    await act(() => result.current.send('hola'));
    expect(result.current.error).toBe('No se pudo enviar el mensaje.');
  });

  it('starts over and pings while open', async () => {
    vi.spyOn(tutorApi, 'send').mockResolvedValue(reply);
    const reset = vi.spyOn(tutorApi, 'reset').mockRejectedValue(new Error('offline'));
    const { result, unmount } = renderHook(() => useTutorChat('ana', { pingIntervalMs: 20 }));
    await act(() => result.current.send('23 + 45'));

    await act(() => result.current.reset());

    expect(reset).toHaveBeenCalled();
    expect(result.current.messages).toEqual([]);
    await waitFor(() => expect(vi.mocked(tutorApi.ping).mock.calls.length).toBeGreaterThan(1));
    unmount();
  });

  it('survives storage that cannot be read or written', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked');
    });

    expect(renderHook(() => useTutorChat('ana')).result.current.messages).toEqual([]);
  });
});

describe('TutorChat', () => {
  it('greets the student and shows the conversation', async () => {
    let answer: (value: typeof reply) => void = () => undefined;
    vi.spyOn(tutorApi, 'send').mockReturnValue(new Promise((resolve) => (answer = resolve)));
    render(<TutorChat username="ana" />);
    expect(screen.getByText(/¡Hola, ana!/)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Tu mensaje para el tutor'), { target: { value: '23 + 45' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enviar' }));

    expect(await screen.findByText('El tutor está pensando…')).toBeInTheDocument();
    await act(async () => answer(reply));
    expect(screen.getByText('¿Por dónde empiezas?')).toBeInTheDocument();
    expect(screen.getByLabelText('Tu mensaje para el tutor')).toHaveValue('');
  });

  it('tags hints above level 0 and shows praise as the accent bubble', () => {
    sessionStorage.setItem(
      'tb_tutor_chat:ana',
      JSON.stringify([
        { id: 1, role: 'tutor', text: 'Empieza por las unidades.', kind: 'hint', hintLevel: 2 },
        { id: 2, role: 'tutor', text: '¿Por dónde empiezas?', kind: 'hint', hintLevel: 0 },
        { id: 3, role: 'tutor', text: '¡Muy bien! 23 + 45 = 68.', kind: 'praise', hintLevel: 2 },
      ])
    );
    render(<TutorChat username="ana" />);

    expect(screen.getAllByText(/^Pista \d de 3$/)).toHaveLength(1);
    expect(screen.getByText('Pista 2 de 3')).toBeInTheDocument();
    const praise = screen.getByText('¡Muy bien! 23 + 45 = 68.');
    expect(praise.parentElement?.querySelector('svg')).not.toBeNull();
  });

  it('refuses pasted or dropped images', () => {
    render(<TutorChat username="ana" />);
    const input = screen.getByLabelText('Tu mensaje para el tutor');
    const files = { files: [new File(['x'], 'tarea.png', { type: 'image/png' })] };

    fireEvent.paste(input, { clipboardData: files });
    expect(screen.getByRole('alert')).toHaveTextContent('Solo puedo leer texto, no imágenes.');

    fireEvent.change(input, { target: { value: '5' } });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    fireEvent.drop(input, { dataTransfer: files });
    expect(screen.getByRole('alert')).toBeInTheDocument();
    fireEvent.paste(input, { clipboardData: { files: [] } });
  });

  it('clears the chat on "Empezar de nuevo"', async () => {
    const reset = vi.spyOn(tutorApi, 'reset').mockResolvedValue({ status: 'ok' });
    render(<TutorChat username="ana" />);

    fireEvent.click(screen.getByRole('button', { name: /Empezar de nuevo/ }));

    await waitFor(() => expect(reset).toHaveBeenCalled());
  });
});

describe('TutorRoster', () => {
  const students: TutorStudent[] = [
    { username: 'ana', online: true, seconds_ago: 5, turns: 4, solved: 1, problem: '23 + 45', hint_level: 2 },
    { username: 'beto', online: false, seconds_ago: 300, turns: 1, solved: 0, problem: null, hint_level: 0 },
  ];

  it('lists who is connected and what they are working on', async () => {
    vi.spyOn(tutorApi, 'students').mockResolvedValue(students);
    render(<TutorRoster host="tutorbox" />);

    expect(await screen.findByText('ana')).toBeInTheDocument();
    expect(screen.getByText('1 conectados')).toBeInTheDocument();
    expect(screen.getByText('Resolviendo 23 + 45 · pista 2 de 3')).toBeInTheDocument();
    expect(screen.getByText(/4 mensajes · 1 resueltos · ahora/)).toBeInTheDocument();
    expect(screen.getByText(/hace 5 min/)).toBeInTheDocument();
    expect(screen.getByText('Sin problema abierto')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'Conectado' })).toBeInTheDocument();
  });

  it('puts a connected student on the last hint first, marked as needing help', async () => {
    const stuck: TutorStudent = { ...students[1], username: 'carla', online: true, problem: '36 ÷ 4', hint_level: 3 };
    vi.spyOn(tutorApi, 'students').mockResolvedValue([...students, stuck]);
    render(<TutorRoster host="tutorbox" />);

    expect(await screen.findByText('Necesita ayuda')).toBeInTheDocument();
    const names = screen.getAllByRole('listitem').map((item) => item.querySelector('strong')?.textContent);
    expect(names).toEqual(['carla', 'ana', 'beto']);
    expect(screen.getByText('Resolviendo 36 ÷ 4 · pista 3 de 3')).toBeInTheDocument();
  });

  it('explains how students join, and reports errors', async () => {
    const list = vi
      .spyOn(tutorApi, 'students')
      .mockResolvedValueOnce([])
      .mockRejectedValueOnce(new ApiError('Sin permiso', 403))
      .mockRejectedValue(new Error('offline'));
    render(<TutorRoster host="tutorbox" pollingIntervalMs={20} />);

    expect(await screen.findByText('tutorbox/alumno')).toBeInTheDocument();
    expect(await screen.findByText('Sin permiso')).toBeInTheDocument();
    expect(await screen.findByText('No se pudo cargar la lista.')).toBeInTheDocument();
    expect(list.mock.calls.length).toBeGreaterThan(2);
  });
});

describe('TutorWall', () => {
  it('shows where to join and the class totals, without names', async () => {
    vi.spyOn(tutorApi, 'summary').mockResolvedValue({ online: 3, solved: 5, need_help: 1 });
    render(<TutorWall host="tutorbox" />);

    expect(screen.getByText('Practica con el tutor')).toBeInTheDocument();
    expect(screen.getByText('tutorbox/alumno')).toBeInTheDocument();
    expect(screen.getAllByText('–')).toHaveLength(3); // before the first answer
    expect(await screen.findByText('5')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('keeps polling quietly when the totals cannot be read', async () => {
    const summary = vi.spyOn(tutorApi, 'summary').mockRejectedValue(new Error('offline'));
    const { unmount } = render(<TutorWall host="" pollingIntervalMs={20} />);

    await waitFor(() => expect(summary.mock.calls.length).toBeGreaterThan(1));
    expect(screen.getAllByText('–')).toHaveLength(3);
    expect(screen.queryByText(/\/alumno/)).not.toBeInTheDocument();
    unmount();
  });
});
