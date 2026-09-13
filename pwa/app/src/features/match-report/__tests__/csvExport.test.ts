import { describe, expect, it } from 'vitest';
import { generateCsvDataUri } from '../csvExport';
import { StoredRoundHistory } from '../report.types';

describe('CSV Report Generator', () => {
  it('generates a well-formed CSV data URI with quoted strings', () => {
    const history: StoredRoundHistory[] = [
      {
        round_id: 'r1',
        text: '¿Cuánto es "x" en 2x = 8?',
        options: { A: '4', B: '2', C: '8', D: '16' },
        tally: {
          counts: { A: 10 },
          total_votes: 10,
          correct_option: 'A',
          correct_count: 10,
          correct_percentage: 100,
        },
        explanations: {},
      },
    ];

    const dataUri = generateCsvDataUri(history);
    expect(dataUri).toMatch(/^data:text\/csv;charset=utf-8,/);

    const decoded = decodeURIComponent(dataUri.replace('data:text/csv;charset=utf-8,', ''));
    expect(decoded).toContain('pregunta,correcta,respondieron,aciertos');
    expect(decoded).toContain('¿Cuánto es ""x"" en 2x = 8?');
    expect(decoded).toContain('"A · 4",10,10');
  });
});
