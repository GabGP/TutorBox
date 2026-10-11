import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { PresenceRow } from '../PresenceRow';
import type { ClickerPresence, StudentPresence } from '../presence.types';

const onlineClicker: ClickerPresence = {
  device_id: 'ESP32-A4CF12',
  status: 'online',
  seconds_ago: 3,
  signal: 'good',
  rssi: -58,
  battery_pct: 88,
};

/** Renders one row inside the list it belongs to, so the markup is valid. */
function renderStudent(overrides: Partial<StudentPresence>) {
  const student: StudentPresence = {
    user_id: 7,
    username: 'ana',
    status: 'online',
    phone: { status: 'online', seconds_ago: 3 },
    clicker: null,
    ...overrides,
  };
  render(
    <ul>
      <PresenceRow student={student} />
    </ul>
  );
}

/** The element that holds one mark: the parent of its label or id text. */
function markOf(text: string): HTMLElement {
  const parent = screen.getByText(text).parentElement;
  if (!parent) throw new Error(`No hay marca para ${text}`);
  return parent;
}

describe('PresenceRow', () => {
  it('shows a connected phone and clicker with the status in words', () => {
    renderStudent({ clicker: onlineClicker });

    expect(screen.getByRole('img', { name: 'Conectado' })).toBeInTheDocument();
    expect(screen.getByText('Conectado')).toHaveAttribute('aria-hidden', 'true');
    expect(screen.getByText('ana')).toBeInTheDocument();
    expect(screen.getByText('Teléfono')).toBeInTheDocument();
    expect(screen.getByText('ESP32-A4CF12')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'Señal buena' })).toBeInTheDocument();
    expect(screen.queryByText(/Batería baja/)).not.toBeInTheDocument();
  });

  it('says how long ago a dropped student went silent, once, and dims the dropped phone', () => {
    renderStudent({
      status: 'dropped',
      phone: { status: 'dropped', seconds_ago: 12 },
    });

    expect(screen.getByRole('img', { name: 'Se cayó hace 12 s' })).toBeInTheDocument();
    expect(screen.getAllByText(/hace 12 s/)).toHaveLength(1);
    expect(markOf('Teléfono')).toHaveTextContent('Desconectado');
    expect(markOf('Teléfono')).not.toHaveTextContent(/hace/);
    expect(markOf('Teléfono').className).toContain('markDimmed');
  });

  it('uses the more recent drop when the phone and the clicker both dropped', () => {
    renderStudent({
      status: 'dropped',
      phone: { status: 'dropped', seconds_ago: 300 },
      clicker: { ...onlineClicker, status: 'dropped', seconds_ago: 40 },
    });

    expect(screen.getByRole('img', { name: 'Se cayó hace 40 s' })).toBeInTheDocument();
  });

  it('shows No ha entrado with no marks when the student never came in', () => {
    renderStudent({
      status: 'absent',
      phone: { status: 'absent', seconds_ago: null },
      clicker: null,
    });

    expect(screen.getByRole('img', { name: 'No ha entrado' })).toBeInTheDocument();
    expect(screen.queryByText('Teléfono')).not.toBeInTheDocument();
    expect(screen.queryByText('Sin conectar')).not.toBeInTheDocument();
  });

  it('marks an assigned clicker that was never seen as Sin conectar', () => {
    renderStudent({
      clicker: {
        device_id: 'ESP32-B7C001',
        status: 'absent',
        seconds_ago: null,
        signal: null,
        rssi: null,
        battery_pct: null,
      },
    });

    expect(screen.getByText('ESP32-B7C001')).toBeInTheDocument();
    expect(screen.getByText('Sin conectar')).toBeInTheDocument();
    expect(screen.queryByRole('img', { name: /Señal/ })).not.toBeInTheDocument();
  });

  it('dims a dropped clicker and marks it Desconectado while the phone keeps the student connected', () => {
    renderStudent({
      phone: { status: 'online', seconds_ago: 3 },
      clicker: { ...onlineClicker, status: 'dropped', seconds_ago: 9 },
    });

    expect(screen.getByRole('img', { name: 'Conectado' })).toBeInTheDocument();
    expect(markOf('ESP32-A4CF12')).toHaveTextContent('Desconectado');
    expect(screen.queryByText(/hace/)).not.toBeInTheDocument();
    expect(markOf('ESP32-A4CF12').className).toContain('markDimmed');
    expect(screen.queryByRole('img', { name: /Señal/ })).not.toBeInTheDocument();
  });

  it('warns when the clicker battery is under 20 percent', () => {
    renderStudent({ clicker: { ...onlineClicker, battery_pct: 15 } });
    expect(screen.getByText('Batería baja 15 %')).toBeInTheDocument();
  });

  it('does not warn at exactly 20 percent', () => {
    renderStudent({ clicker: { ...onlineClicker, battery_pct: 20 } });
    expect(screen.queryByText(/Batería baja/)).not.toBeInTheDocument();
  });

  it('hides the signal bars when the clicker reports no signal', () => {
    renderStudent({ clicker: { ...onlineClicker, signal: null } });
    expect(screen.queryByRole('img', { name: /Señal/ })).not.toBeInTheDocument();
    expect(screen.getByText('ESP32-A4CF12')).toBeInTheDocument();
  });

  it.each([
    ['good', 'Señal buena'],
    ['fair', 'Señal regular'],
    ['weak', 'Señal débil'],
  ] as const)('labels a %s signal for screen readers as "%s"', (signal, label) => {
    renderStudent({ clicker: { ...onlineClicker, signal } });
    expect(screen.getByRole('img', { name: label })).toBeInTheDocument();
  });
});
