import { StoredRoundHistory } from './report.types';

/**
 * Encodes a classroom match history into a standard RFC 4180 CSV data URI.
 *
 * @param {StoredRoundHistory[]} history - List of executed round histories including questions, options, and tallies.
 * @returns {string} Fully formatted `data:text/csv;charset=utf-8,...` URI suitable for browser download triggers.
 */
export function generateCsvDataUri(history: StoredRoundHistory[]): string {
  const header = 'pregunta,correcta,respondieron,aciertos';
  const rows = history.map((h) => {
    const escapedText = `"${h.text.replace(/"/g, '""')}"`;
    const correctOpt = h.tally.correct_option;
    const correctVal = h.options[correctOpt] || '';
    const answer = `"${correctOpt} · ${correctVal.replace(/"/g, '""')}"`;
    return `${escapedText},${answer},${h.tally.total_votes},${h.tally.correct_count}`;
  });

  const csvContent = [header, ...rows].join('\n') + '\n';
  return `data:text/csv;charset=utf-8,${encodeURIComponent(csvContent)}`;
}
