import { ApiError } from '../../shared/api/httpClient';
import { toErrorMessage } from '../../shared/lib/errors';
import { CLICKER_ID_ERROR } from './clickerId';

export const CLICKER_LOAD_ERROR = 'Error al cargar clickers';

/** HTTP status of a failed request, or null for anything else. */
function statusOf(err: unknown): number | null {
  return err instanceof ApiError ? err.status : null;
}

/** Toast text for a failed `POST /staff/devices`. */
export function registerErrorMessage(err: unknown): string {
  const status = statusOf(err);
  if (status === 409) return 'Ese clicker ya está registrado.';
  if (status === 422) return CLICKER_ID_ERROR;
  return toErrorMessage(err, 'Error al agregar clicker');
}

/** Toast text for a failed `POST /staff/devices/{id}/assign`. */
export function assignErrorMessage(err: unknown): string {
  const status = statusOf(err);
  if (status === 404) return 'Ese clicker o ese alumno ya no existe.';
  if (status === 422) return 'Solo se puede asignar a cuentas de alumno.';
  return toErrorMessage(err, 'Error al asignar clicker');
}

/** Toast text for a failed `POST /staff/devices/{id}/unassign`. */
export function unassignErrorMessage(err: unknown): string {
  return statusOf(err) === 404 ? 'Ese clicker ya no existe.' : 'Error al quitar alumno';
}

/** Toast text for a failed `DELETE /staff/devices/{id}`. */
export function deleteErrorMessage(err: unknown): string {
  return statusOf(err) === 404 ? 'Ese clicker ya no existe.' : 'Error al eliminar clicker';
}
