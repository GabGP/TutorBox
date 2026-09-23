import { requestApi } from '../../shared/api/httpClient';
import {
  DeletedUser,
  RecoverUserResponse,
  ResetPinResponse,
  RosterStudent,
} from './roster.types';

/**
 * API client contract for classroom student roster administration.
 */
export const rosterApi = {
  /**
   * Fetches the classroom user list from `/staff/users` and filters for student accounts.
   *
   * @returns {Promise<RosterStudent[]>} Array of registered student user objects.
   */
  async getStudents(): Promise<RosterStudent[]> {
    const res = await requestApi<{ users: RosterStudent[] }>('GET', '/staff/users');
    return (res.users || []).filter((u) => u.role === 'student');
  },

  /**
   * Fetches all classroom users (any role) from `/staff/users`.
   * Pass `includeDeleted` to list soft-deleted accounts for recovery.
   */
  async getAll(includeDeleted = false): Promise<{
    users: (RosterStudent | DeletedUser)[];
  }> {
    const query = includeDeleted ? '?include_deleted=true' : '';
    return requestApi<{ users: (RosterStudent | DeletedUser)[] }>(
      'GET',
      `/staff/users${query}`
    );
  },

  /**
   * Fetches soft-deleted accounts via `GET /staff/users?include_deleted=true`.
   */
  async getDeleted(): Promise<DeletedUser[]> {
    const res = await rosterApi.getAll(true);
    return (res.users || []) as DeletedUser[];
  },

  /**
   * Registers a new user under staff administration via `POST /staff/users`.
   * Teachers may create students/teachers; only admins may create admins
   * (enforced server-side).
   */
  async createStudent(
    username: string,
    pin: string,
    role: string = 'student'
  ): Promise<RosterStudent> {
    return requestApi<RosterStudent>('POST', '/staff/users', {
      username,
      pin,
      role,
    });
  },

  /**
   * Resets a student account PIN to a temporary random PIN via `POST /staff/users/{id}/reset-pin`.
   *
   * @param {string} studentId - Target student user UUID.
   * @returns {Promise<ResetPinResponse>} Response containing the generated temporary PIN.
   */
  async resetPin(studentId: string): Promise<ResetPinResponse> {
    return requestApi<ResetPinResponse>('POST', `/staff/users/${studentId}/reset-pin`);
  },

  /**
   * Changes a user's role via `PATCH /staff/users/{id}/role`.
   * Teachers are limited to student/teacher; only admins touch admin
   * accounts (enforced server-side).
   */
  async changeRole(
    userId: string,
    role: string
  ): Promise<RosterStudent> {
    return requestApi<RosterStudent>('PATCH', `/staff/users/${userId}/role`, {
      role,
    });
  },

  /**
   * Soft-deletes a user account via `DELETE /staff/users/{id}`.
   * Sessions are revoked and clickers unlinked server-side.
   */
  async deleteUser(userId: string): Promise<void> {
    await requestApi('DELETE', `/staff/users/${userId}`);
  },

  /**
   * Recovers a soft-deleted account via `POST /staff/users/{id}/recover`
   * with a new username. Returns a temporary PIN the user must change.
   */
  async recoverUser(
    userId: string,
    username: string
  ): Promise<RecoverUserResponse> {
    return requestApi<RecoverUserResponse>(
      'POST',
      `/staff/users/${userId}/recover`,
      { username }
    );
  },
};
