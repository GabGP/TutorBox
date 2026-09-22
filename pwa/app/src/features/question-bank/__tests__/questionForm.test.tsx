import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { QuestionForm } from '../QuestionForm';
import { generatorApi } from '../../question-generator/generatorApi';
import { question } from './bankFixture';

describe('QuestionForm taxonomy selects', () => {
  const taxonomy = [
    {
      name: 'arithmetic',
      label: 'Aritmética',
      subconcepts: [
        {
          name: 'addition_subtraction',
          misconceptions: ['sign_error', 'borrowing_error'],
        },
        {
          name: 'multiplication_division',
          misconceptions: ['forgot_carry'],
        },
      ],
    },
  ];

  it('offers subconcepts and misconceptions from the chosen topic', async () => {
    vi.spyOn(generatorApi, 'getTopics').mockResolvedValue(taxonomy);
    render(<QuestionForm initial={null} onSaved={() => {}} />);
    await waitFor(() =>
      expect(
        screen.getByRole('option', { name: 'Aritmética' })
      ).toBeInTheDocument()
    );
    fireEvent.change(screen.getByLabelText('Tema'), {
      target: { value: 'arithmetic' },
    });
    const sub = screen.getByLabelText('Subconcepto');
    expect(sub.tagName).toBe('SELECT');
    const subTexts = Array.from((sub as HTMLSelectElement).options).map(
      (o) => o.text
    );
    expect(subTexts).toContain('Suma y resta');
    expect(subTexts).toContain('Multiplicación y división');

    fireEvent.change(sub, { target: { value: 'addition_subtraction' } });
    for (const k of ['B', 'C', 'D']) {
      const misc = screen.getByLabelText(`Error ${k}`);
      expect(misc.tagName).toBe('SELECT');
      const values = Array.from((misc as HTMLSelectElement).options).map(
        (o) => o.value
      );
      expect(values).toContain('sign_error');
      expect(values).toContain('borrowing_error');
    }
    vi.restoreAllMocks();
  });

  it('resets the subconcept when the topic changes away', async () => {
    vi.spyOn(generatorApi, 'getTopics').mockResolvedValue(taxonomy);
    render(<QuestionForm initial={null} onSaved={() => {}} />);
    await waitFor(() =>
      expect(
        screen.getByRole('option', { name: 'Aritmética' })
      ).toBeInTheDocument()
    );
    fireEvent.change(screen.getByLabelText('Tema'), {
      target: { value: 'arithmetic' },
    });
    fireEvent.change(screen.getByLabelText('Subconcepto'), {
      target: { value: 'addition_subtraction' },
    });
    expect(screen.getByLabelText('Subconcepto')).toHaveValue(
      'addition_subtraction'
    );
    fireEvent.change(screen.getByLabelText('Tema'), {
      target: { value: '' },
    });
    expect(screen.getByLabelText('Subconcepto')).toHaveValue('');
    vi.restoreAllMocks();
  });

  it('preserves edit values missing from the taxonomy with text fallback', async () => {
    vi.spyOn(generatorApi, 'getTopics').mockResolvedValue([]);
    render(<QuestionForm initial={question} onSaved={() => {}} />);
    // Stale topic/subconcept stay selectable so edits never lose data.
    expect(screen.getByLabelText('Tema')).toHaveValue('sumas');
    expect(screen.getByLabelText('Subconcepto')).toHaveValue('llevar');
    // No taxonomy for (sumas, llevar): misconceptions stay free text.
    const miscA = screen.getByLabelText('Error A');
    expect(miscA.tagName).toBe('INPUT');
    expect(miscA).toHaveValue('no-lleva');
    vi.restoreAllMocks();
  });
});
