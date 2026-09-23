import { describe, expect, it } from 'vitest';
import { mapRosterError, toErrorMessage } from '../errors';

describe('toErrorMessage', () => {
  it('prefers Error messages', () => {
    expect(toErrorMessage(new Error('boom'), 'fallback')).toBe('boom');
  });

  it('reads message-like objects', () => {
    expect(toErrorMessage({ message: 'srv' }, 'fallback')).toBe('srv');
  });

  it('passes plain strings through', () => {
    expect(toErrorMessage('oops', 'fallback')).toBe('oops');
  });

  it('falls back for empty and unknown values', () => {
    expect(toErrorMessage(new Error(''), 'fallback')).toBe('fallback');
    expect(toErrorMessage(null, 'fallback')).toBe('fallback');
    expect(toErrorMessage(undefined, 'fallback')).toBe('fallback');
    expect(toErrorMessage({ message: '' }, 'fallback')).toBe('fallback');
  });
});

describe('mapRosterError', () => {
  it('maps known roster statuses through the catalog', () => {
    expect(mapRosterError(409, 'fallback')).toBe('Ya existe');
    expect(mapRosterError(403, 'fallback')).toBe('No tienes permiso para esto');
  });

  it('returns the fallback otherwise', () => {
    expect(mapRosterError(undefined, 'fallback')).toBe('fallback');
    expect(mapRosterError(500, 'fallback')).toBe('fallback');
  });
});
