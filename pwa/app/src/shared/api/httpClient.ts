import { getErrorMessage } from './errorCatalog';
import { storage } from '../lib/storage';

export const API_BASE = '/api/v1';

/**
 * Custom error wrapper capturing HTTP status code and server error details.
 */
export class ApiError extends Error {
  status: number;
  detail?: string;

  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Builds auth headers for a JSON or blob request from the stored token.
 */
function buildHeaders(body: unknown, json: boolean): Record<string, string> {
  const headers: Record<string, string> = {};
  if (json || body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }
  const token = storage.getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

/** Throws a standardized ApiError for a non-OK fetch response. */
async function throwForBadResponse(response: Response): Promise<never> {
  const data = await response.json().catch(() => ({}));
  const detail = (data as { detail?: string }).detail;
  const message = getErrorMessage(response.status, detail);
  throw new ApiError(message, response.status, detail);
}

/**
 * Executes a typed JSON REST API request against the TutorBox backend.
 * Automatically injects the stored Bearer auth token and standardizes error responses.
 *
 * @template T
 * @param {string} method - HTTP method ('GET', 'POST', 'PATCH', 'DELETE').
 * @param {string} path - Relative endpoint path under `/api/v1`.
 * @param {unknown} [body] - Optional JSON payload.
 * @param {boolean} [auth=true] - Whether to include stored Bearer authorization token.
 * @returns {Promise<T>} Typed parsed JSON response.
 */
export async function requestApi<T = unknown>(
  method: string,
  path: string,
  body?: unknown,
  auth = true
): Promise<T> {
  const headers = auth ? buildHeaders(body, true) : { 'Content-Type': 'application/json' };

  let response: Response;
  try {
    response = await fetch(API_BASE + path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(getErrorMessage(0), 0);
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = (data as { detail?: string }).detail;
    const message = getErrorMessage(response.status, detail);
    throw new ApiError(message, response.status, detail);
  }

  return data as T;
}

/**
 * Fetches binary media (e.g. offline synthesized WAV audio) and creates a local Object URL.
 *
 * @param {string} path - Relative endpoint path under `/api/v1`.
 * @param {string} [method] - HTTP method (defaults to 'GET').
 * @param {unknown} [body] - Optional JSON payload (for POST previews).
 * @returns {Promise<string>} Local blob URL suitable for HTMLAudioElement playback.
 */
export async function requestBlobUrl(
  path: string,
  method = 'GET',
  body?: unknown
): Promise<string> {
  const headers = buildHeaders(body, false);

  let response: Response;
  try {
    response = await fetch(API_BASE + path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(getErrorMessage(0), 0);
  }

  if (!response.ok) {
    await throwForBadResponse(response);
  }

  const blob = await response.blob();
  return URL.createObjectURL(blob);
}
