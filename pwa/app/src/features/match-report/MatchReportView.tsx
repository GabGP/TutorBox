import React, { useMemo } from 'react';
import { SessionReport } from '../session-engine/session.types';
import { generateCsvDataUri } from './csvExport';
import {
  getHardestQuestions,
  getToneColor,
  getTopRepeatedErrors,
} from './reportCalculator';
import styles from './report.module.css';
import { StoredRoundHistory } from './report.types';

export interface MatchReportViewProps {
  report: SessionReport | null;
  history: StoredRoundHistory[];
}

/**
 * Match Report View component.
 * Displays aggregated classroom session statistics, including group accuracy,
 * hardest questions with accuracy bars, repeated misconceptions, and CSV download.
 *
 * @param {MatchReportViewProps} props - Component props containing session report metrics and round history.
 * @returns {JSX.Element} The rendered match report dashboard.
 */
export const MatchReportView: React.FC<MatchReportViewProps> = ({
  report,
  history,
}) => {
  const hardest = useMemo(() => getHardestQuestions(history, 3), [history]);
  const repeatedErrors = useMemo(() => getTopRepeatedErrors(history, 3), [history]);
  const csvUri = useMemo(() => generateCsvDataUri(history), [history]);

  const avgText = report
    ? `${Math.round(report.average_accuracy_percentage)}%`
    : '…';
  const partText = report
    ? `${report.total_votes_cast} en ${report.total_rounds} preg.`
    : '…';

  return (
    <div className={styles.cols}>
      <div className={styles.col}>
        <div className={styles.two}>
          <div className={`${styles.stat} ${styles.tint}`}>
            <div>Promedio del grupo</div>
            <div className={styles.n} id="avg">
              {avgText}
            </div>
          </div>
          <div className={`${styles.stat} ${styles.ok}`}>
            <div>Respuestas</div>
            <div className={styles.n} id="part">
              {partText}
            </div>
          </div>
        </div>

        <div className={styles.cardWhite}>
          <h2 className={styles.sectionTitle}>
            Preguntas más difíciles
          </h2>
          <div className={styles.hard} id="hard">
            {hardest.length === 0 ? (
              <div className={styles.emptyMuted}>Sin preguntas respondidas.</div>
            ) : (
              hardest.map((h) => {
                const p = Math.round(h.tally.correct_percentage);
                const tone = getToneColor(p);
                return (
                  <div key={h.round_id} className={styles.hardItem}>
                    <div className={styles.hardHeader}>
                      <span>{h.text}</span>
                      <b className={styles.toneText} style={{ '--tone': tone } as React.CSSProperties}>{p}% acierto</b>
                    </div>
                    <div className={styles.track}>
                      <div
                        className={styles.trackFill}
                        style={{ '--progress': `${p}%`, '--tone': tone } as React.CSSProperties}
                      />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      <div className={styles.col}>
        <div className={styles.alertLg}>
          <b>Errores que se repiten</b>
          <div className={styles.errs} id="errors">
            {repeatedErrors.length === 0 ? (
              <div>Ningún error se repitió en el grupo.</div>
            ) : (
              repeatedErrors.map(({ history: h, wrong: w }) => (
                <div key={h.round_id}>
                  En <b>{h.text}</b>, {w.count} alumnos eligieron{' '}
                  <b>{h.options[w.choice]}</b>: {h.explanations[w.choice] || ''}
                </div>
              ))
            )}
          </div>
        </div>

        <a
          id="export"
          className={styles.exportBtn}
          href={csvUri}
          download="reporte-tutorbox.csv"
        >
          Guardar reporte del grupo
        </a>
      </div>
    </div>
  );
};
