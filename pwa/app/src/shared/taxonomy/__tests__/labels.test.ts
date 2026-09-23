import { describe, expect, it } from 'vitest';
import {
  getMisconceptionLabel,
  getSubconceptLabel,
  getTopicLabel,
} from '../labels';

describe('taxonomy labels', () => {
  it('labels known topics and falls back to the slug', () => {
    expect(getTopicLabel('fractions')).toBe('Fracciones');
    expect(getTopicLabel('')).toBe('Todos los temas');
    expect(getTopicLabel('unknown-slug')).toBe('unknown-slug');
  });

  it('labels subconcepts, empty for missing', () => {
    expect(getSubconceptLabel('percentages')).toBe('Porcentajes');
    expect(getSubconceptLabel()).toBe('');
    expect(getSubconceptLabel(null)).toBe('');
    expect(getSubconceptLabel('custom')).toBe('custom');
  });

  it('labels misconceptions, empty for missing', () => {
    expect(getMisconceptionLabel('forgot_carry')).toBe('Olvidó la llevada');
    expect(getMisconceptionLabel()).toBe('');
    expect(getMisconceptionLabel('custom')).toBe('custom');
  });
});
