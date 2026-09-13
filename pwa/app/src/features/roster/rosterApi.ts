import { requestApi } from '../../shared/api/httpClient';
import { ResetPinResponse, RosterStudent } from './roster.types';

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
   * Registers a new student under staff administration via `POST /staff/users`.
   *
   * @param {string} username - Student username.
   * @param {string} pin - Initial student PIN.
   * @returns {Promise<RosterStudent>} Newly created student user record.
   */
  async createStudent(username: string, pin: string): Promise<RosterStudent> {
    return requestApi<RosterStudent>('POST', '/staff/users', {
      username,
      pin,
      role: 'student',
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
};
