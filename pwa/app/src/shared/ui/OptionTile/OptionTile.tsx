import React from 'react';
import { Check } from 'lucide-react';
import type { OptionLetter } from '../../constants/options';
import styles from './OptionTile.module.css';

export interface OptionTileProps {
  letter: OptionLetter;
  text: string;
  isPicked?: boolean;
  isLocked?: boolean;
  onSelect?: (letter: OptionLetter) => void;
  disabled?: boolean;
  className?: string;
}

/**
 * Quiz Response Option Button Tile.
 * Accessible, color-coded touch target (A=Crimson, B=Blue, C=Amber, D=Green)
 * supporting selection states, lock status, and keyboard interaction.
 *
 * @param {OptionTileProps} props - Component props containing option letter, text, picked/locked status, and click callback.
 * @returns {JSX.Element} The rendered option tile button.
 */
export const OptionTile: React.FC<OptionTileProps> = ({
  letter,
  text,
  isPicked = false,
  isLocked = false,
  onSelect,
  disabled = false,
  className = '',
}) => {
  const colorClass = styles[`k_${letter}`] || '';
  const stateClass = isPicked
    ? styles.picked
    : isLocked
    ? styles.locked
    : '';

  const handleClick = () => {
    if (!disabled && !isLocked && onSelect) {
      onSelect(letter);
    }
  };

  return (
    <button
      type="button"
      className={`${styles.tile} ${colorClass} ${stateClass} ${className}`}
      onClick={handleClick}
      disabled={disabled || isLocked}
      aria-label={`Opción ${letter}: ${text}`}
      aria-pressed={isPicked}
    >
      <i className={styles.letterBadge}>{letter}</i>
      <span className={styles.optionText}>{text}</span>
      {isPicked && <span className={styles.checkBadge}><Check size={19} aria-hidden /></span>}
    </button>
  );
};
