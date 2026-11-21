import React from 'react';
import { Spinner } from '../../shared/ui/Spinner/Spinner';
import styles from './ModelLoadingLine.module.css';

export interface ModelLoadingLineProps {
  /** Shown beside the spinner and announced by it, e.g. "Cargando el modelo de preguntas…". */
  text: string;
}

/**
 * A spinner with its label and an indeterminate bar, in place of the progress bar while the
 * quiz model loads (the total is not known until the first question starts).
 */
export const ModelLoadingLine: React.FC<ModelLoadingLineProps> = ({ text }) => (
  <div className={styles.line}>
    <div className={styles.track} aria-hidden="true">
      <span className={styles.beam} />
    </div>
    <p className={styles.text}>
      <Spinner label={text} size={14} />
      <span aria-hidden="true">{text}</span>
    </p>
  </div>
);
