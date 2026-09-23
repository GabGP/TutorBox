import { describe, expect, it } from 'vitest';
import { toQuery } from '../query';

describe('toQuery', () => {
  it('returns an empty string for empty params', () => {
    expect(toQuery({})).toBe('');
    expect(toQuery()).toBe('');
  });

  it('serializes provided params', () => {
    expect(toQuery({ topic: 'fractions', limit: 5, offset: 0 })).toBe(
      '?topic=fractions&limit=5&offset=0'
    );
  });

  it('skips undefined, null and empty-string values', () => {
    expect(
      toQuery({ topic: undefined, user_id: null, success: '', limit: 20 })
    ).toBe('?limit=20');
  });

  it('keeps falsy-but-meaningful values', () => {
    expect(toQuery({ success: false, offset: 0 })).toBe(
      '?success=false&offset=0'
    );
  });

  it('encodes special characters', () => {
    expect(toQuery({ topic: 'a b&c' })).toBe('?topic=a+b%26c');
  });
});
