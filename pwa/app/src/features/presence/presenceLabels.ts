import type { PresenceChannel, SignalStrength, StudentPresence } from './presence.types';

/** A clicker below this battery level shows the low-battery warning. */
export const LOW_BATTERY_PERCENT = 20;

const SIGNAL_LABELS: Record<SignalStrength, string> = {
  good: 'Señal buena',
  fair: 'Señal regular',
  weak: 'Señal débil',
};

/** "hace 12 s" under a minute, "hace 3 min" from there. */
export function formatSecondsAgo(seconds: number): string {
  if (seconds < 60) return `hace ${seconds} s`;
  return `hace ${Math.floor(seconds / 60)} min`;
}

/** " hace 12 s", or nothing when the age is unknown. */
function agoSuffix(seconds: number | null): string {
  return seconds === null ? '' : ` ${formatSecondsAgo(seconds)}`;
}

/** Header line: "18 de 24 conectados", with " · 2 se cayeron" when someone dropped. */
export function presenceSummaryLabel(online: number, total: number, dropped: number): string {
  const connected = `${online} de ${total} conectados`;
  if (dropped === 0) return connected;
  const droppedText = dropped === 1 ? '1 se cayó' : `${dropped} se cayeron`;
  return `${connected} · ${droppedText}`;
}

/** Seconds since the most recent drop among the student's phone and clicker, or null when unknown. */
export function mostRecentDropSeconds(student: StudentPresence): number | null {
  const channels: PresenceChannel[] = student.clicker ? [student.phone, student.clicker] : [student.phone];
  const dropAges = channels.flatMap((channel) =>
    channel.status === 'dropped' && channel.seconds_ago !== null ? [channel.seconds_ago] : []
  );
  return dropAges.length > 0 ? Math.min(...dropAges) : null;
}

/** The student's status in words: "Conectado", "Se cayó hace 12 s" or "No ha entrado". */
export function studentStatusLabel(student: StudentPresence): string {
  if (student.status === 'online') return 'Conectado';
  if (student.status === 'absent') return 'No ha entrado';
  return `Se cayó${agoSuffix(mostRecentDropSeconds(student))}`;
}

/** Text alternative of the signal bars. */
export function signalLabel(signal: SignalStrength): string {
  return SIGNAL_LABELS[signal];
}

/** The low-battery warning, or null when the level is unknown or at least the threshold. */
export function lowBatteryLabel(percent: number | null): string | null {
  if (percent === null || percent >= LOW_BATTERY_PERCENT) return null;
  return `Batería baja ${percent} %`;
}
