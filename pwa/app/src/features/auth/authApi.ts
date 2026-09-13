import { requestApi } from '../../shared/api/httpClient';
import { storage } from '../../shared/lib/storage';
import { LoginResponse, SignupResponse, User } from './auth.types';

/**
 * API client contract for user authentication, signup, and credentials management.
 */
export const authApi = {
  /**
   * Authenticates user credentials against `/auth/login` and persists the session token.
   *
   * @param {string} username - Target account username.
   * @param {string} pin - Account PIN.
   * @returns {Promise<LoginResponse>} Server login response containing token and must_change_pin flag.
   */
  async login(username: string, pin: string): Promise<LoginResponse> {
    const response = await requestApi<LoginResponse>(
      'POST',
      '/auth/login',
      { username, pin },
      false
    );
    storage.setToken(response.session_id);
    return response;
  },

  /**
   * Registers a new student account against `/users/signup`.
   *
   * @param {string} username - Targeted account username.
   * @param {string} pin - Desired account PIN.
   * @returns {Promise<SignupResponse>} Server signup confirmation response.
   */
  async signup(username: string, pin: string): Promise<SignupResponse> {
    return requestApi<SignupResponse>(
      'POST',
      '/users/signup',
      { username, pin },
      false
    );
  },

  /**
   * Terminates active session against `/auth/logout` and purges stored token.
   *
   * @returns {Promise<void>}
   */
  async logout(): Promise<void> {
    try {
      await requestApi('POST', '/auth/logout');
    } catch {
      // Ignore network failures on logout
    }
    storage.clearToken();
  },

  /**
   * Retrieves profile details for currently authenticated user via `/users/me`.
   *
   * @returns {Promise<User | null>} User profile record, or null if unauthenticated or session expired.
   */
  async getCurrentUser(): Promise<User | null> {
    if (!storage.getToken()) {
      return null;
    }
    try {
      return await requestApi<User>('GET', '/users/me');
    } catch (e) {
      if ((e as { status?: number }).status === 401) {
        storage.clearToken();
      }
      return null;
    }
  },

  /**
   * Submits forced PIN update via `/users/me/pin` and re-authenticates the user.
   *
   * @param {string} username - Account username.
   * @param {string} currentPin - Existing or temporary PIN.
   * @param {string} newPin - New permanent PIN.
   * @returns {Promise<LoginResponse>} New login credentials response.
   */
  async changePin(username: string, currentPin: string, newPin: string): Promise<LoginResponse> {
    await requestApi('PATCH', '/users/me/pin', {
      current_pin: currentPin,
      new_pin: newPin,
    });
    // The backend revokes the current session upon PIN change, so re-authenticate
    return authApi.login(username, newPin);
  },
};
