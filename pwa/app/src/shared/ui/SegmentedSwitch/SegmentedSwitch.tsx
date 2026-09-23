import type { LucideIcon } from 'lucide-react';
import styles from './SegmentedSwitch.module.css';

export interface SwitchOption<T extends string> {
  value: T;
  icon: LucideIcon;
  label: string;
}

export interface SegmentedSwitchProps<T extends string> {
  value: T;
  onChange: (v: T) => void;
  options: SwitchOption<T>[];
  ariaLabel?: string;
}

/**
 * Squishy segmented switch (2+ options). The thumb slides with a spring;
 * options squash while pressed.
 */
export function SegmentedSwitch<T extends string>({
  value,
  onChange,
  options,
  ariaLabel = 'Selector',
}: SegmentedSwitchProps<T>) {
  const index = Math.max(
    0,
    options.findIndex((o) => o.value === value)
  );
  return (
    <div className={styles.switchTrack} role="tablist" aria-label={ariaLabel}>
      <span
        className={styles.switchThumb}
        aria-hidden
        style={{
          width: `calc((100% - 8px) / ${options.length})`,
          transform: `translateX(${index * 100}%)`,
        }}
      />
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="tab"
          aria-selected={value === o.value}
          className={`${styles.switchOpt} ${value === o.value ? styles.switchOptOn : ''}`}
          onClick={() => onChange(o.value)}
        >
          <span className={styles.optLabel}><o.icon size={18} aria-hidden /> {o.label}</span>
        </button>
      ))}
    </div>
  );
}
