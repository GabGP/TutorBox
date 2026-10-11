import { fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../../../shared/api/httpClient';
import { ClassPresenceList } from '../ClassPresenceList';
import { presenceApi } from '../presenceApi';
import type { ClassPresence } from '../presence.types';
import { EMPTY_CLASS, MIXED_CLASS } from './presenceFixture';

/** A poll interval long enough that the suite never polls again during a test. */
const NO_REPOLL_MS = 60_000;

function renderList(
  overrides: { onManageUsers?: () => void; onOpenClickers?: () => void; pollingIntervalMs?: number } = {}
) {
  const handlers = {
    onManageUsers: vi.fn(),
    onOpenClickers: vi.fn(),
  };
  render(
    <ClassPresenceList
      onManageUsers={overrides.onManageUsers ?? handlers.onManageUsers}
      onOpenClickers={overrides.onOpenClickers ?? handlers.onOpenClickers}
      pollingIntervalMs={overrides.pollingIntervalMs ?? NO_REPOLL_MS}
    />
  );
  return handlers;
}

function answerWith(payload: ClassPresence) {
  return vi.spyOn(presenceApi, 'getClassPresence').mockResolvedValue(payload);
}

describe('ClassPresenceList', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows a loading line until the first answer arrives', () => {
    vi.spyOn(presenceApi, 'getClassPresence').mockReturnValue(new Promise(() => undefined));
    renderList();

    expect(screen.getByText('Cargando la lista de alumnos…')).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    expect(screen.queryByText(/Todavía no hay alumnos/)).not.toBeInTheDocument();
  });

  it('shows the connected count and the dropped count in the header', async () => {
    answerWith(MIXED_CLASS);
    renderList();

    expect(await screen.findByText('ana')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Alumnos' })).toBeInTheDocument();
    expect(screen.getByText('1 de 3 conectados · 1 se cayó')).toBeInTheDocument();
  });

  it('uses the plural for several dropped students', async () => {
    answerWith({
      ...MIXED_CLASS,
      students: [
        MIXED_CLASS.students[0],
        { ...MIXED_CLASS.students[1], user_id: 10, username: 'dani' },
        { ...MIXED_CLASS.students[1], user_id: 11, username: 'eva' },
      ],
    });
    renderList();

    expect(await screen.findByText('dani')).toBeInTheDocument();
    expect(screen.getByText('1 de 3 conectados · 2 se cayeron')).toBeInTheDocument();
  });

  it('keeps the order the server sent, whatever the poll', async () => {
    answerWith(MIXED_CLASS);
    renderList();

    await screen.findByText('ana');
    const names = screen.getAllByText(/^(ana|beto|carla)$/).map((element) => element.textContent);
    expect(names).toEqual(['ana', 'beto', 'carla']);
  });

  it('says the class is empty and asks the teacher to add students', async () => {
    answerWith(EMPTY_CLASS);
    renderList();

    expect(await screen.findByText(/Todavía no hay alumnos\. Agregue uno/)).toBeInTheDocument();
    expect(screen.queryByText('Cargando la lista de alumnos…')).not.toBeInTheDocument();
  });

  it('lists the unassigned clickers with the note and the way to assign them', async () => {
    answerWith(MIXED_CLASS);
    const handlers = renderList();

    expect(await screen.findByRole('heading', { name: 'Clickers sin alumno' })).toBeInTheDocument();
    const section = screen.getByRole('region', { name: 'Clickers sin alumno' });
    expect(within(section).getByText('ESP32-C3D002')).toBeInTheDocument();
    expect(
      within(section).getByText('Un clicker necesita un alumno antes de poder conectarse.')
    ).toBeInTheDocument();
    fireEvent.click(within(section).getByRole('button', { name: 'Asignar clickers' }));
    expect(handlers.onOpenClickers).toHaveBeenCalledTimes(1);
    expect(handlers.onManageUsers).not.toHaveBeenCalled();
  });

  it('leaves the unassigned section out when every clicker has a student', async () => {
    answerWith({ ...MIXED_CLASS, unassigned_clickers: [] });
    renderList();

    await screen.findByText('ana');
    expect(screen.queryByText('Clickers sin alumno')).not.toBeInTheDocument();
  });

  it('hands Administrar usuarios to its handler', async () => {
    answerWith(EMPTY_CLASS);
    const handlers = renderList();

    fireEvent.click(screen.getByRole('button', { name: 'Administrar usuarios' }));
    expect(handlers.onManageUsers).toHaveBeenCalledTimes(1);
    await screen.findByText(/Todavía no hay alumnos/);
  });

  it('shows the error line, not an empty class, when the first poll fails', async () => {
    vi.spyOn(presenceApi, 'getClassPresence').mockRejectedValue(new Error('offline'));
    renderList();

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No se pudo cargar la lista de alumnos. Se vuelve a intentar.'
    );
    expect(screen.queryByText(/Todavía no hay alumnos/)).not.toBeInTheDocument();
    expect(screen.queryByText('Cargando la lista de alumnos…')).not.toBeInTheDocument();
  });

  it('keeps the last list on screen and shows the error when a later poll fails', async () => {
    vi.spyOn(presenceApi, 'getClassPresence')
      .mockResolvedValueOnce(MIXED_CLASS)
      .mockRejectedValue(new ApiError("Sin conexión con Utz'tutor", 0));
    renderList({ pollingIntervalMs: 20 });

    expect(await screen.findByRole('alert')).toHaveTextContent("Sin conexión con Utz'tutor");
    expect(screen.getByText('ana')).toBeInTheDocument();
    expect(screen.getByText('1 de 3 conectados · 1 se cayó')).toBeInTheDocument();
  });
});
