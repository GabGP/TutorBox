/**
 * Shared class-list fixtures for the presence suites. They follow the shape in
 * presence.types.ts: each status is decided by the server, and the students
 * are already in username order.
 */
import type { ClassPresence } from '../presence.types';

export const EMPTY_CLASS: ClassPresence = {
  online: 0,
  total: 0,
  students: [],
  unassigned_clickers: [],
};

/** Three students: one connected by phone and clicker, one dropped, one who never came in. */
export const MIXED_CLASS: ClassPresence = {
  online: 1,
  total: 3,
  students: [
    {
      user_id: 7,
      username: 'ana',
      status: 'online',
      phone: { status: 'online', seconds_ago: 3 },
      clicker: {
        device_id: 'ESP32-A4CF12',
        status: 'online',
        seconds_ago: 3,
        signal: 'good',
        rssi: -58,
        battery_pct: 88,
      },
    },
    {
      user_id: 8,
      username: 'beto',
      status: 'dropped',
      phone: { status: 'dropped', seconds_ago: 12 },
      clicker: null,
    },
    {
      user_id: 9,
      username: 'carla',
      status: 'absent',
      phone: { status: 'absent', seconds_ago: null },
      clicker: {
        device_id: 'ESP32-B7C001',
        status: 'absent',
        seconds_ago: null,
        signal: null,
        rssi: null,
        battery_pct: null,
      },
    },
  ],
  unassigned_clickers: ['ESP32-C3D002'],
};
