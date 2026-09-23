import { describe, expect, it } from 'vitest';
import { validatePinPair } from '../pinValidation';

describe('validatePinPair', () => {
  it('rejects empty entries', () => {
    expect(validatePinPair('', '1234', '0000')).toBe('empty');
    expect(validatePinPair('1234', '', '0000')).toBe('empty');
    expect(validatePinPair('', '', '0000')).toBe('empty');
  });

  it('rejects mismatched pairs', () => {
    expect(validatePinPair('1234', '4321', '0000')).toBe('mismatch');
  });

  it('rejects reuse of the current PIN', () => {
    expect(validatePinPair('0000', '0000', '0000')).toBe('same');
  });

  it('accepts a fresh matching pair', () => {
    expect(validatePinPair('1234', '1234', '0000')).toBeNull();
    expect(validatePinPair('1234', '1234')).toBeNull();
    expect(validatePinPair('1234', '1234', null)).toBeNull();
  });
});
