import React from 'react';
import { BatteryLow, Gamepad2, Smartphone } from 'lucide-react';
import styles from './presence.module.css';
import type { ClickerPresence, PresenceChannel, PresenceStatus, StudentPresence } from './presence.types';
import { SignalBars } from './SignalBars';
import { DISCONNECTED_LABEL, lowBatteryLabel, studentStatusLabel } from './presenceLabels';

const DOT_CLASS_BY_STATUS: Record<PresenceStatus, string> = {
  online: styles.dotOnline,
  dropped: styles.dotDropped,
  absent: styles.dotAbsent,
};

/**
 * A dropped channel is dimmed. Every mark that is not connected says Desconectado, so the
 * status never relies on colour alone; a clicker that never joined says it without the dimming.
 * How long ago is said once, in the row's status, so one number ticks per row.
 */
function markClass(channel: PresenceChannel): string {
  return channel.status === 'dropped' ? `${styles.mark} ${styles.markDimmed}` : styles.mark;
}

const PhoneMark: React.FC<{ phone: PresenceChannel }> = ({ phone }) => (
  <span className={markClass(phone)}>
    <Smartphone size={16} aria-hidden />
    <span>Teléfono</span>
    {phone.status === 'dropped' && <span className={styles.droppedNote}>{DISCONNECTED_LABEL}</span>}
  </span>
);

const ClickerMark: React.FC<{ clicker: ClickerPresence }> = ({ clicker }) => {
  const batteryWarning = lowBatteryLabel(clicker.battery_pct);
  return (
    <span className={markClass(clicker)}>
      <Gamepad2 size={16} aria-hidden />
      <span className={styles.clickerId}>{clicker.device_id}</span>
      {clicker.status === 'absent' && <span className={styles.absentNote}>{DISCONNECTED_LABEL}</span>}
      {clicker.status === 'online' && clicker.signal !== null && <SignalBars signal={clicker.signal} />}
      {clicker.status === 'dropped' && <span className={styles.droppedNote}>{DISCONNECTED_LABEL}</span>}
      {batteryWarning !== null && (
        <span className={styles.batteryWarning}>
          <BatteryLow size={14} aria-hidden />
          {batteryWarning}
        </span>
      )}
    </span>
  );
};

export interface PresenceRowProps {
  student: StudentPresence;
}

/**
 * One student of the class list: a status dot, the username and the status in
 * words, then a mark for the phone (when it is or was connected) and one for
 * the clicker (when one is assigned). The status text is hidden from assistive
 * tech because the dot's label already carries it.
 */
export const PresenceRow: React.FC<PresenceRowProps> = ({ student }) => {
  const { phone, clicker } = student;
  const statusLabel = studentStatusLabel(student);
  const showPhone = phone.status !== 'absent';

  return (
    <li className={styles.row}>
      <div className={styles.head}>
        <span
          className={`${styles.dot} ${DOT_CLASS_BY_STATUS[student.status]}`}
          role="img"
          aria-label={statusLabel}
        />
        <span className={styles.username}>{student.username}</span>
        <span className={styles.statusText} aria-hidden="true">
          {statusLabel}
        </span>
      </div>
      {(showPhone || clicker !== null) && (
        <div className={styles.marks}>
          {showPhone && <PhoneMark phone={phone} />}
          {clicker !== null && <ClickerMark clicker={clicker} />}
        </div>
      )}
    </li>
  );
};
