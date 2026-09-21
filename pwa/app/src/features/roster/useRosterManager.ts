import { useCallback, useEffect, useState } from 'react';
import { toErrorMessage } from '../../shared/lib/errors';
import { DeletedUser, RosterStudent } from './roster.types';
import { rosterApi } from './rosterApi';

interface UseRosterManagerOptions {
  enabled?: boolean;
}

/**
 * Custom React hook for managing classroom user accounts.
 * Provides roster synchronization (students for the lobby, all users for
 * Settings), user creation with roles, temporary PIN resets, soft-delete,
 * recovery of deleted accounts, and error state tracking.
 *
 * @param {UseRosterManagerOptions} [options={}] - Hook options (e.g. enable gating).
 * @returns {object} User lists, loading/error states, PIN notices, and mutation methods.
 */
export function useRosterManager({ enabled = true }: UseRosterManagerOptions = {}) {
  const [students, setStudents] = useState<RosterStudent[]>([]);
  const [users, setUsers] = useState<RosterStudent[]>([]);
  const [deleted, setDeleted] = useState<DeletedUser[]>([]);
  const [showDeleted, setShowDeleted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pinNotice, setPinNotice] = useState<string | null>(null);

  const loadStudents = useCallback(async () => {
    setLoading(true);
    try {
      const data = await rosterApi.getStudents();
      setStudents(data);
      setError(null);
    } catch {
      // Ignore network errors in quiet polling
    } finally {
      setLoading(false);
    }
  }, []);

  const loadUsers = useCallback(async () => {
    try {
      const data = await rosterApi.getAll(false);
      setUsers((data.users || []) as RosterStudent[]);
    } catch {
      // Ignore network errors in quiet polling
    }
  }, []);

  useEffect(() => {
    if (enabled) {
      loadStudents();
      loadUsers();
    }
  }, [enabled, loadStudents, loadUsers]);

  const loadDeleted = useCallback(async () => {
    try {
      const data = await rosterApi.getDeleted();
      setDeleted(data);
    } catch {
      // Ignore network errors in quiet polling
    }
  }, []);

  const addStudent = async (username: string, pin: string, role = 'student') => {
    setError(null);
    try {
      await rosterApi.createStudent(username, pin, role);
      await loadStudents();
      await loadUsers();
    } catch (err: unknown) {
      const e = err as { status?: number };
      const msg =
        e.status === 409
          ? 'Ese usuario ya existe'
          : e.status === 403
            ? 'No tienes permiso para crear ese rol'
            : toErrorMessage(err, 'Error al agregar alumno');
      setError(msg);
      throw new Error(msg);
    }
  };

  const resetStudentPin = async (studentId: string, studentName: string) => {
    setError(null);
    try {
      const res = await rosterApi.resetPin(studentId);
      setPinNotice(
        `PIN temporal de ${studentName}: ${res.temporary_pin}. Al entrar deberá elegir un PIN nuevo.`
      );
    } catch (err: unknown) {
      setError(toErrorMessage(err, 'Error al reiniciar PIN'));
    }
  };

  const deleteStudent = async (studentId: string, studentName: string) => {
    setError(null);
    try {
      await rosterApi.deleteUser(studentId);
      setPinNotice(`Cuenta de ${studentName} eliminada.`);
      await loadStudents();
      await loadUsers();
      if (showDeleted) await loadDeleted();
    } catch (err: unknown) {
      const e = err as { status?: number };
      const msg =
        e.status === 409
          ? 'No se puede eliminar la última cuenta de docente o admin'
          : e.status === 403
            ? 'No tienes permiso para eliminar esa cuenta'
            : toErrorMessage(err, 'Error al eliminar cuenta');
      setError(msg);
      throw new Error(msg);
    }
  };

  const changeUserRole = async (userId: string, role: string) => {
    setError(null);
    try {
      await rosterApi.changeRole(userId, role);
      setPinNotice(null);
      await loadStudents();
      await loadUsers();
    } catch (err: unknown) {
      const e = err as { status?: number };
      const msg =
        e.status === 409
          ? 'No se puede quitar al último docente o admin'
          : e.status === 403
            ? 'No tienes permiso para ese rol'
            : toErrorMessage(err, 'Error al cambiar rol');
      setError(msg);
      throw new Error(msg);
    }
  };

  const recoverStudent = async (userId: string, username: string) => {
    setError(null);
    try {
      const res = await rosterApi.recoverUser(userId, username);
      setPinNotice(
        `Cuenta ${res.username} recuperada. PIN temporal: ${res.temporary_pin}. Al entrar deberá elegir un PIN nuevo.`
      );
      await loadDeleted();
      await loadStudents();
      await loadUsers();
    } catch (err: unknown) {
      const e = err as { status?: number };
      const msg =
        e.status === 409
          ? 'Ese nombre ya está en uso, elige otro'
          : toErrorMessage(err, 'Error al recuperar cuenta');
      setError(msg);
      throw new Error(msg);
    }
  };

  const toggleDeleted = async () => {
    const next = !showDeleted;
    setShowDeleted(next);
    if (next) await loadDeleted();
  };

  return {
    students,
    users,
    deleted,
    showDeleted,
    loading,
    error,
    pinNotice,
    loadStudents,
    loadUsers,
    loadDeleted,
    addStudent,
    resetStudentPin,
    deleteStudent,
    changeUserRole,
    recoverStudent,
    toggleDeleted,
    clearError: () => setError(null),
    clearPinNotice: () => setPinNotice(null),
  };
}
