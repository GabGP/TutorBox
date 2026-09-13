import { useCallback, useEffect, useState } from 'react';
import { RosterStudent } from './roster.types';
import { rosterApi } from './rosterApi';

interface UseRosterManagerOptions {
  enabled?: boolean;
}

/**
 * Custom React hook for managing classroom student accounts.
 * Provides student roster synchronization, new student creation,
 * temporary PIN resets with security notices, and error state tracking.
 *
 * @param {UseRosterManagerOptions} [options={}] - Hook options (e.g. enable gating).
 * @returns {object} Roster students list, loading/error states, PIN reset notices, and mutation methods.
 */
export function useRosterManager({ enabled = true }: UseRosterManagerOptions = {}) {
  const [students, setStudents] = useState<RosterStudent[]>([]);
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

  useEffect(() => {
    if (enabled) {
      loadStudents();
    }
  }, [enabled, loadStudents]);

  const addStudent = async (username: string, pin: string) => {
    setError(null);
    try {
      await rosterApi.createStudent(username, pin);
      await loadStudents();
    } catch (err: unknown) {
      const e = err as { status?: number; message?: string };
      const msg =
        e.status === 409
          ? 'Ese usuario ya existe'
          : e.message || 'Error al agregar alumno';
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
      const e = err as { message?: string };
      setError(e.message || 'Error al reiniciar PIN');
    }
  };

  return {
    students,
    loading,
    error,
    pinNotice,
    loadStudents,
    addStudent,
    resetStudentPin,
    clearError: () => setError(null),
    clearPinNotice: () => setPinNotice(null),
  };
}
