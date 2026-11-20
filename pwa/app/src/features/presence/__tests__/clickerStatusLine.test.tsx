import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ClickerStatusLine } from '../ClickerStatusLine';
import type { ClickerPresence } from '../presence.types';

const base: ClickerPresence = {
  device_id: 'ESP32-A4CF12',
  status: 'online',
  seconds_ago: 1,
  signal: 'weak',
  rssi: -85,
  battery_pct: 64,
};

describe('ClickerStatusLine', () => {
  it('says Conectado with the signal bars while online', () => {
    render(<ClickerStatusLine clicker={base} />);
    expect(screen.getByRole('img', { name: 'Conectado' })).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'Señal débil' })).toBeInTheDocument();
    expect(screen.queryByText(/Batería baja/)).toBeNull();
  });

  it('says how long ago a dropped clicker went silent, without bars, in a dimmed pill', () => {
    const { container } = render(<ClickerStatusLine clicker={{ ...base, status: 'dropped', seconds_ago: 75 }} />);
    expect(screen.getByRole('img', { name: 'Se cayó hace 1 min' })).toBeInTheDocument();
    expect(screen.queryByRole('img', { name: /Señal/ })).toBeNull();
    // Same pill as the lobby's clicker mark, dashed once it dropped.
    expect((container.firstChild as HTMLElement).className).toMatch(/mark/);
    expect((container.firstChild as HTMLElement).className).toMatch(/markDimmed/);
  });

  it('says Desconectado for a clicker that never joined, and warns on low battery', () => {
    render(<ClickerStatusLine clicker={{ ...base, status: 'absent', seconds_ago: null, battery_pct: 9 }} />);
    expect(screen.getByRole('img', { name: 'Desconectado' })).toBeInTheDocument();
    expect(screen.getByText('Batería baja 9 %')).toBeInTheDocument();
  });
});
