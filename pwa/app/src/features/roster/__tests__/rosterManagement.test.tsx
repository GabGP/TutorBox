import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { RosterTable } from '../RosterTable';
import { rosterApi } from '../rosterApi';
import type { RosterStudent } from '../roster.types';
import { UserEditSheet } from '../UserEditSheet';
import { advanceHold, setupHoldTimers, teardownHoldTimers } from '../../../test/holdTimers';

const students: RosterStudent[] = [
  { id: '1', username: 'ana', role: 'student' },
  { id: '2', username: 'profe', role: 'teacher' },
];

describe('rosterApi user management', () => {
  it('createStudent sends role', async () => {
    const spy = vi
      .spyOn(httpClient, 'requestApi')
      .mockResolvedValue({ username: 'x', role: 'teacher' });
    await rosterApi.createStudent('x', '1234', 'teacher');
    expect(spy).toHaveBeenCalledWith('POST', '/staff/users', {
      username: 'x',
      pin: '1234',
      role: 'teacher',
    });
    spy.mockRestore();
  });

  it('getDeleted queries include_deleted', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({ users: [] });
    await rosterApi.getDeleted();
    expect(spy).toHaveBeenCalledWith('GET', '/staff/users?include_deleted=true');
    spy.mockRestore();
  });

  it('deleteUser sends DELETE', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({});
    await rosterApi.deleteUser('1');
    expect(spy).toHaveBeenCalledWith('DELETE', '/staff/users/1');
    spy.mockRestore();
  });

  it('recoverUser posts new username', async () => {
    const spy = vi
      .spyOn(httpClient, 'requestApi')
      .mockResolvedValue({ username: 'ana2', temporary_pin: '9999' });
    const res = await rosterApi.recoverUser('1', 'ana2');
    expect(spy).toHaveBeenCalledWith('POST', '/staff/users/1/recover', {
      username: 'ana2',
    });
    expect(res.temporary_pin).toBe('9999');
    spy.mockRestore();
  });
});

describe('RosterTable management UI', () => {
  it('shows role picker only when multiple creatable roles', () => {
    const { rerender } = render(
      <RosterTable
        students={students}
        onAddStudent={vi.fn()}
        onResetPin={vi.fn()}
      />
    );
    expect(screen.queryByLabelText('Rol')).not.toBeInTheDocument();

    rerender(
      <RosterTable
        students={students}
        onAddStudent={vi.fn()}
        onResetPin={vi.fn()}
        creatableRoles={['student', 'teacher']}
      />
    );
    expect(screen.getByLabelText('Rol')).toBeInTheDocument();
  });

  it('holds the reset action in the sheet before calling onResetPin (800ms)', async () => {
    setupHoldTimers();
    try {
      const onResetPin = vi.fn().mockResolvedValue(undefined);
      render(
        <RosterTable
          students={students}
          onAddStudent={vi.fn()}
          onResetPin={onResetPin}
        />
      );
      // Compact rows expose a single Editar affordance (no inline actions).
      expect(screen.queryByText('Reiniciar PIN')).not.toBeInTheDocument();
      fireEvent.click(screen.getAllByRole('button', { name: 'Editar' })[0]);
      const resetBtn = screen.getByRole('button', { name: 'Reiniciar PIN' });
      // A plain click never resets: press-and-hold is the confirm.
      fireEvent.click(resetBtn);
      expect(onResetPin).not.toHaveBeenCalled();
      fireEvent.pointerDown(resetBtn, { pointerId: 1 });
      advanceHold(800);
      await act(async () => {});
      expect(onResetPin).toHaveBeenCalledWith('1', 'ana');
    } finally {
      teardownHoldTimers();
    }
  });

  it('holds delete in the sheet before calling onDeleteUser (2000ms)', async () => {
    setupHoldTimers();
    try {
      const onDeleteUser = vi.fn().mockResolvedValue(undefined);
      render(
        <RosterTable
          students={students}
          onAddStudent={vi.fn()}
          onResetPin={vi.fn()}
          onDeleteUser={onDeleteUser}
        />
      );
      fireEvent.click(screen.getAllByRole('button', { name: 'Editar' })[0]);
      const deleteBtn = screen.getByRole('button', { name: 'Eliminar cuenta' });
      fireEvent.click(deleteBtn);
      expect(onDeleteUser).not.toHaveBeenCalled();
      fireEvent.pointerDown(deleteBtn, { pointerId: 1 });
      advanceHold(2000);
      await act(async () => {});
      expect(onDeleteUser).toHaveBeenCalledWith('1', 'ana');
    } finally {
      teardownHoldTimers();
    }
  });

  it('hides delete in the sheet when onDeleteUser is absent (lobby)', () => {    render(
      <RosterTable
        students={students}
        onAddStudent={vi.fn()}
        onResetPin={vi.fn()}
      />
    );
    fireEvent.click(screen.getAllByRole('button', { name: 'Editar' })[0]);
    expect(
      screen.queryByRole('button', { name: 'Eliminar cuenta' })
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Reiniciar PIN' })
    ).toBeInTheDocument();
  });

  it('renders deleted view with recover action', () => {
    render(
      <RosterTable
        students={students}
        onAddStudent={vi.fn()}
        onResetPin={vi.fn()}
        deleted={[
          { id: '9', role: 'student', former_username: 'viejo', deleted_at: 'x' },
        ]}
        showDeleted
        onToggleDeleted={vi.fn()}
        onRecoverUser={vi.fn()}
      />
    );
    expect(screen.getByText('viejo')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Recuperar' })
    ).toBeInTheDocument();
  });

  it('collapses the sheet on a long downward drag of the grip', () => {
    const onClose = vi.fn();
    render(
      <UserEditSheet
        user={{ id: '1', username: 'ana', role: 'student' }}
        onClose={onClose}
        onResetPin={vi.fn()}
      />
    );
    const dialog = screen.getByRole('dialog');
    const grip = dialog.firstElementChild as HTMLElement;
    fireEvent.pointerDown(grip, { clientY: 100, pointerId: 1 });
    fireEvent.pointerMove(grip, { clientY: 260, pointerId: 1 });
    fireEvent.pointerUp(grip, { clientY: 260, pointerId: 1 });
    expect(onClose).toHaveBeenCalled();
  });

  it('snaps back on a short drag without closing', () => {    const onClose = vi.fn();
    render(
      <UserEditSheet
        user={{ id: '1', username: 'ana', role: 'student' }}
        onClose={onClose}
        onResetPin={vi.fn()}
      />
    );
    const dialog = screen.getByRole('dialog');
    const grip = dialog.firstElementChild as HTMLElement;
    fireEvent.pointerDown(grip, { clientY: 100, pointerId: 1 });
    fireEvent.pointerMove(grip, { clientY: 130, pointerId: 1 });
    fireEvent.pointerUp(grip, { clientY: 130, pointerId: 1 });
    expect(onClose).not.toHaveBeenCalled();
  });

  it('locks background scroll while open and restores on close', () => {
    const { unmount } = render(
      <UserEditSheet
        user={{ id: '1', username: 'ana', role: 'student' }}
        onClose={vi.fn()}
        onResetPin={vi.fn()}
      />
    );
    expect(document.body.style.overflow).toBe('hidden');
    unmount();
    expect(document.body.style.overflow).toBe('');
  });

  it('stages role and applies on save', async () => {
    const onRoleChange = vi.fn().mockResolvedValue(undefined);
    render(
      <RosterTable
        students={students}
        onAddStudent={vi.fn()}
        onResetPin={vi.fn()}
        editableRoles={['student', 'teacher']}
        onRoleChange={onRoleChange}
      />
    );
    fireEvent.click(screen.getAllByRole('button', { name: 'Editar' })[0]);
    // Nothing to save before touching the picker.
    expect(
      screen.queryByRole('button', { name: 'Guardar cambios' })
    ).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Rol del usuario'), {
      target: { value: 'teacher' },
    });
    expect(onRoleChange).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }));
    await waitFor(() => expect(onRoleChange).toHaveBeenCalledWith('1', 'teacher'));
  });

  it('hides role editing without editableRoles', () => {
    render(
      <RosterTable
        students={students}
        onAddStudent={vi.fn()}
        onResetPin={vi.fn()}
      />
    );
    fireEvent.click(screen.getAllByRole('button', { name: 'Editar' })[0]);
    expect(screen.queryByLabelText('Rol del usuario')).not.toBeInTheDocument();
  });

  it('sends PATCH role change via rosterApi', async () => {
    const spy = vi
      .spyOn(httpClient, 'requestApi')
      .mockResolvedValue({ id: '1', username: 'ana', role: 'teacher' });
    await rosterApi.changeRole('1', 'teacher');
    expect(spy).toHaveBeenCalledWith('PATCH', '/staff/users/1/role', {
      role: 'teacher',
    });
    spy.mockRestore();
  });
});
