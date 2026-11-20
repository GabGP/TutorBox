import React from 'react';
import { BatteryLow } from 'lucide-react';
import styles from './presence.module.css';
import type { ClickerPresence, PresenceStatus } from './presence.types';
import { SignalBars } from './SignalBars';
import { clickerStatusLabel, lowBatteryLabel } from './presenceLabels';

const DOT_CLASS_BY_STATUS: Record<PresenceStatus, string> = {
  online: styles.dotOnline,
  dropped: styles.dotDropped,
  absent: styles.dotAbsent,
};

/** The words take the lobby's look: plain, bold red once dropped, italic when never joined. */
const TEXT_CLASS_BY_STATUS: Record<PresenceStatus, string> = {
  online: styles.statusText,
  dropped: styles.droppedNote,
  absent: styles.absentNote,
};

export interface ClickerStatusLineProps {
  clicker: ClickerPresence;
}

/**
 * A clicker's live status in the lobby's pill (dashed and dimmed once it
 * dropped): the status dot, the status in words, the signal bars while
 * connected and the low-battery warning.
 * The words are hidden from assistive tech because the dot's label carries them.
 */
export const ClickerStatusLine: React.FC<ClickerStatusLineProps> = ({ clicker }) => {
  const statusLabel = clickerStatusLabel(clicker);
  const batteryWarning = lowBatteryLabel(clicker.battery_pct);
  return (
    <span className={clicker.status === 'dropped' ? `${styles.mark} ${styles.markDimmed}` : styles.mark}>
      <span
        className={`${styles.dot} ${DOT_CLASS_BY_STATUS[clicker.status]}`}
        role="img"
        aria-label={statusLabel}
      />
      <span className={TEXT_CLASS_BY_STATUS[clicker.status]} aria-hidden="true">
        {statusLabel}
      </span>
      {clicker.status === 'online' && clicker.signal !== null && <SignalBars signal={clicker.signal} />}
      {batteryWarning !== null && (
        <span className={styles.batteryWarning}>
          <BatteryLow size={14} aria-hidden />
          {batteryWarning}
        </span>
      )}
    </span>
  );
};
