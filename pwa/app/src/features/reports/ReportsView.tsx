import React, { useEffect, useState } from 'react';
import { Calendar, CalendarDays, CalendarRange, Gamepad2, ListChecks, MessageCircle } from 'lucide-react';
import { toErrorMessage } from '../../shared/lib/errors';
import { formatFullDate } from '../../shared/lib/format';
import { getMisconceptionLabel, getTopicLabel } from '../../shared/taxonomy/labels';
import { SegmentedSwitch, type SwitchOption } from '../../shared/ui/SegmentedSwitch/SegmentedSwitch';
import { QuizReport, ReportPeriod, TutorReport, reportsApi } from './reportsApi';
import styles from './reports.module.css';

type ReportKind = 'quiz' | 'tutor' | 'games';

const KIND_OPTIONS: SwitchOption<ReportKind>[] = [
  { value: 'quiz', icon: ListChecks, label: 'Quiz' },
  { value: 'tutor', icon: MessageCircle, label: 'Tutor' },
  { value: 'games', icon: Gamepad2, label: 'Juegos' },
];
const PERIOD_OPTIONS: SwitchOption<ReportPeriod>[] = [
  { value: 'day', icon: CalendarDays, label: 'Día' },
  { value: 'week', icon: CalendarRange, label: 'Semana' },
  { value: 'month', icon: Calendar, label: 'Mes' },
];

const label = (topic: string | null) => (topic ? getTopicLabel(topic) : '—');
// SQLite stamps are UTC without a zone: mark them so the browser shows local time.
const localTime = (stamp: string) => formatFullDate(stamp.replace(' ', 'T') + 'Z');

const Stat: React.FC<{ name: string; value: React.ReactNode }> = ({ name, value }) => (
  <div className={styles.stat}><span>{name}</span><b>{value}</b></div>
);

const Bar: React.FC<{ pct: number }> = ({ pct }) => (
  <div className={styles.track}><div style={{ width: `${Math.min(100, pct)}%` }} /></div>
);

const QuizSection: React.FC<{ r: QuizReport }> = ({ r }) => (
  <>
    <div className={styles.stats}>
      <Stat name="Aciertos" value={`${Math.round(r.accuracy)}%`} />
      <Stat name="Respuestas" value={r.answers} />
      <Stat name="Alumnos" value={r.students} />
    </div>
    <div className={styles.stats}>
      <Stat name="Mejor tema" value={label(r.best_topic)} />
      <Stat name="Más difícil" value={label(r.weakest_topic)} />
      <Stat name="Más mejoró" value={label(r.most_improved_topic)} />
    </div>
    <h3 className={styles.h}>Aciertos por tema</h3>
    {r.topics.map((t) => (
      <div key={t.topic} className={styles.row}>
        <div className={styles.rowHead}>
          <span>{getTopicLabel(t.topic)}</span>
          <b>
            {Math.round(t.accuracy)}%
            {t.change != null && (
              <span className={t.change >= 0 ? styles.up : styles.down}>
                {t.change >= 0 ? ' ▲' : ' ▼'} {Math.abs(Math.round(t.change))} pts
              </span>
            )}
          </b>
        </div>
        <Bar pct={t.accuracy} />
      </div>
    ))}
    {r.misconceptions.length > 0 && <h3 className={styles.h}>Errores que más se repiten</h3>}
    {r.misconceptions.map((m) => (
      <div key={m.misconception + m.topic} className={styles.line}>
        <span>{getMisconceptionLabel(m.misconception)} · {getTopicLabel(m.topic)}</span>
        <b>{m.wrong_answers}</b>
      </div>
    ))}
  </>
);

const TutorSection: React.FC<{ r: TutorReport }> = ({ r }) => {
  const most = Math.max(1, ...r.topics.map((t) => t.turns));
  return (
    <>
      <div className={styles.stats}>
        <Stat name="Alumnos" value={r.students} />
        <Stat name="Sesiones" value={r.sessions} />
        <Stat name="Mensajes" value={r.turns} />
      </div>
      <div className={styles.stats}>
        <Stat name="Más preguntado" value={label(r.most_asked_topic)} />
        <Stat name="Donde más se atoran" value={label(r.most_stuck_topic)} />
      </div>
      <h3 className={styles.h}>Temas en el tutor</h3>
      {r.topics.map((t) => (
        <div key={t.topic} className={styles.row}>
          <div className={styles.rowHead}>
            <span>{getTopicLabel(t.topic)}</span>
            <b>{t.turns} mensajes · {t.solved} resueltos · {t.stuck} atorados</b>
          </div>
          <Bar pct={(100 * t.turns) / most} />
        </div>
      ))}
      <h3 className={styles.h}>Sesiones</h3>
      {r.session_summaries.map((s) => (
        <div key={s.student + s.started_at} className={styles.line}>
          <span>
            <b>{s.student}</b> · {localTime(s.started_at)}
            <br />
            <span className={styles.mute}>{s.topics.map(getTopicLabel).join(', ') || 'Sin tema'}</span>
          </span>
          <span className={styles.mute}>{s.solved} resueltos · {s.stuck} atorados</span>
        </div>
      ))}
    </>
  );
};

/**
 * Teacher analytics: quiz, tutor and (later) games reports for a day, week or
 * month. The tutor report lists topics per session, never the conversation.
 */
export const ReportsView: React.FC = () => {
  const [kind, setKind] = useState<ReportKind>('quiz');
  const [period, setPeriod] = useState<ReportPeriod>('week');
  const [report, setReport] = useState<{ kind: ReportKind; data: QuizReport | TutorReport } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (kind === 'games') return;
    let live = true;
    setReport(null);
    setError(null);
    (kind === 'quiz' ? reportsApi.quiz(period) : reportsApi.tutor(period))
      .then((data) => live && setReport({ kind, data }))
      .catch((err: unknown) => live && setError(toErrorMessage(err, 'No se pudo cargar el reporte')));
    return () => { live = false; };
  }, [kind, period]);

  const empty = report && ('answers' in report.data ? report.data.answers : report.data.turns) === 0;
  return (
    <div className={styles.view} id="reports">
      <SegmentedSwitch value={kind} onChange={setKind} options={KIND_OPTIONS} ariaLabel="Tipo de reporte" />
      {kind === 'games' ? (
        <p className={styles.note}>Próximamente: aquí verás los temas de las apps de práctica.</p>
      ) : (
        <>
          <SegmentedSwitch value={period} onChange={setPeriod} options={PERIOD_OPTIONS} ariaLabel="Periodo" />
          {error && <p className={styles.error} role="alert">{error}</p>}
          {!report && !error && <p className={styles.mute}>Cargando…</p>}
          {empty && <p className={styles.note}>Sin actividad en este periodo.</p>}
          {report && !empty && report.kind === 'quiz' && <QuizSection r={report.data as QuizReport} />}
          {report && !empty && report.kind === 'tutor' && <TutorSection r={report.data as TutorReport} />}
        </>
      )}
    </div>
  );
};
