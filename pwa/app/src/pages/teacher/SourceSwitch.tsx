import styles from './TeacherView.module.css';

export type QuestionSource = 'generate' | 'bank';

export interface SwitchOption<T extends string> {
  value: T;
  glyph: string;
  label: string;
}

export interface SourceSwitchProps<T extends string> {
  value: T;
  onChange: (v: T) => void;
  options: SwitchOption<T>[];
  ariaLabel?: string;
}

/**
 * Squishy segmented switch (2+ options). The thumb slides with a spring;
 * options squash while pressed.
 */
export function SourceSwitch<T extends string>({
  value,
  onChange,
  options,
  ariaLabel = 'Selector',
}: SourceSwitchProps<T>) {
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
          {o.glyph} {o.label}
        </button>
      ))}
    </div>
  );
}

export const QUESTION_SOURCE_OPTIONS: SwitchOption<QuestionSource>[] = [
  { value: 'generate', glyph: '⚡', label: 'Generar' },
  { value: 'bank', glyph: '📚', label: 'Banco' },
];
