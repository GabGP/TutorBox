/**
 * Shared fixtures for the clicker suites: students, a starting fleet, and an
 * in-memory stand-in for the `/staff/devices` and `/staff/users` routes.
 * The fake applies the documented side effects (assigning moves a student off
 * the clicker that held them; unassigning, deleting and 404s behave as in
 * docs/api/devices.md), so reload-after-mutation assertions see real state.
 */
import { act, screen } from '@testing-library/react';
import { vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { ApiError } from '../../../shared/api/httpClient';
import type { RosterStudent } from '../../roster/roster.types';
import type { ClickerDevice } from '../clickers.types';

/**
 * A student as `GET /staff/users` really sends it: `id` is a number. The roster
 * type declares `id` as a string (a pre-existing mismatch in features/roster,
 * deliberately not changed here), so this is the single place that casts.
 */
export function serverStudent(numericId: number, username: string): RosterStudent {
  return { id: numericId as unknown as string, username, role: 'student' };
}

/** A student with the string id the roster type declares. */
export function stringIdStudent(id: string, username: string): RosterStudent {
  return { id, username, role: 'student' };
}

export const STUDENTS: RosterStudent[] = [
  serverStudent(1, 'ana'),
  serverStudent(2, 'beto'),
  serverStudent(3, 'carla'),
];

/** Sorted by device id, as the server returns them. */
export const FLEET_SEED: ClickerDevice[] = [
  {
    device_id: 'ESP32-A4CF12',
    assigned_user_id: 1,
    assigned_username: 'ana',
    created_at: '2026-08-29 14:00:00',
    secret_issued_at: '2026-08-30 09:15:00',
  },
  {
    device_id: 'ESP32-B7',
    assigned_user_id: null,
    assigned_username: null,
    created_at: '2026-08-29 14:05:00',
    secret_issued_at: null,
  },
];

export interface RecordedRequest {
  method: string;
  path: string;
  body?: unknown;
}

export interface FakeFleet {
  requests: RecordedRequest[];
  /** Live clicker list held by the fake server. */
  devices: ClickerDevice[];
  /** The next request with this method and path fails with `error`. */
  failNext: (method: string, path: string, error: Error) => void;
}

interface FleetSeed {
  devices?: ClickerDevice[];
  students?: RosterStudent[];
}

const ROUTE_PATTERN = /^\/staff\/devices\/([^/]+)(\/assign|\/unassign)?$/;

/**
 * Spies `requestApi` and answers the clicker routes from in-memory state.
 * Call inside a test; `vi.restoreAllMocks()` in afterEach removes the spy.
 */
export function installFakeFleet(seed: FleetSeed = {}): FakeFleet {
  const devices: ClickerDevice[] = (seed.devices ?? FLEET_SEED).map((device) => ({ ...device }));
  const students = seed.students ?? STUDENTS;
  const requests: RecordedRequest[] = [];
  const pendingFailures = new Map<string, Error>();

  const findDevice = (deviceId: string): ClickerDevice => {
    const device = devices.find((candidate) => candidate.device_id === deviceId);
    if (!device) throw new ApiError('No se encontró', 404);
    return device;
  };

  /** Takes a student off whichever clicker holds them (one clicker per student). */
  const releaseStudent = (userId: number) => {
    for (const device of devices) {
      if (device.assigned_user_id === userId) {
        device.assigned_user_id = null;
        device.assigned_username = null;
      }
    }
  };

  const answer = (method: string, path: string, body?: unknown): unknown => {
    if (method === 'GET' && path === '/staff/devices') {
      return { devices: devices.map((device) => ({ ...device })) };
    }
    if (method === 'GET' && path === '/staff/users') return { users: students };
    if (method === 'POST' && path === '/staff/devices') {
      const deviceId = (body as { device_id: string }).device_id;
      if (devices.some((device) => device.device_id === deviceId)) {
        throw new ApiError('Ya existe', 409);
      }
      const created: ClickerDevice = {
        device_id: deviceId,
        assigned_user_id: null,
        assigned_username: null,
        created_at: '2026-10-10 12:00:00',
        secret_issued_at: null,
      };
      devices.push(created);
      return created;
    }
    const match = ROUTE_PATTERN.exec(path);
    if (!match) return {};
    const device = findDevice(decodeURIComponent(match[1]));
    const action = match[2];
    if (method === 'DELETE' && !action) {
      devices.splice(devices.indexOf(device), 1);
      return { detail: 'Device removed from fleet.' };
    }
    if (method === 'POST' && action === '/unassign') {
      device.assigned_user_id = null;
      device.assigned_username = null;
      return { detail: 'Device unassigned successfully.' };
    }
    if (method === 'POST' && action === '/assign') {
      const userId = Number((body as { user_id: number }).user_id);
      const student = students.find((candidate) => Number(candidate.id) === userId);
      if (!student) throw new ApiError('No se encontró', 404);
      releaseStudent(userId);
      device.assigned_user_id = userId;
      device.assigned_username = student.username;
      return {
        device_id: device.device_id,
        assigned_user_id: userId,
        assigned_username: student.username,
      };
    }
    return {};
  };

  vi.spyOn(httpClient, 'requestApi').mockImplementation(
    async (method: string, path: string, body?: unknown) => {
      requests.push({ method, path, body });
      const key = `${method} ${path}`;
      const failure = pendingFailures.get(key);
      if (failure) {
        pendingFailures.delete(key);
        throw failure;
      }
      return answer(method, path, body);
    }
  );

  return {
    requests,
    devices,
    failNext: (method, path, error) => {
      pendingFailures.set(`${method} ${path}`, error);
    },
  };
}

/**
 * Lets queued promise callbacks run (the list reload after a mutation) while
 * fake timers are installed, where waitFor would stall.
 */
export async function flushRequests(): Promise<void> {
  await act(async () => {
    for (let turn = 0; turn < 20; turn += 1) await Promise.resolve();
  });
}

/** The list item holding one clicker's face (found via its aria-label). */
export function clickerRow(deviceId: string): HTMLElement {
  const row = screen.getByLabelText(`Clicker ${deviceId}`).closest('[role="listitem"]');
  if (!(row instanceof HTMLElement)) throw new Error(`No hay fila para ${deviceId}`);
  return row;
}
