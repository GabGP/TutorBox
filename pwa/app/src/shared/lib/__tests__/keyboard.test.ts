import { renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { mapKeyToOption, useOptionKeyboard } from '../keyboard';

describe('Keyboard Adapter', () => {
  it('maps letter keys A-D and number keys 1-4 to uppercase option letters', () => {
    expect(mapKeyToOption('a')).toBe('A');
    expect(mapKeyToOption('A')).toBe('A');
    expect(mapKeyToOption('b')).toBe('B');
    expect(mapKeyToOption('c')).toBe('C');
    expect(mapKeyToOption('d')).toBe('D');
    expect(mapKeyToOption('1')).toBe('A');
    expect(mapKeyToOption('2')).toBe('B');
    expect(mapKeyToOption('3')).toBe('C');
    expect(mapKeyToOption('4')).toBe('D');
    expect(mapKeyToOption('e')).toBeNull();
    expect(mapKeyToOption('5')).toBeNull();
  });

  it('triggers onSelect when key event fires on window', () => {
    const onSelect = vi.fn();
    renderHook(() => useOptionKeyboard(onSelect, true));

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'b' }));
    expect(onSelect).toHaveBeenCalledWith('B');

    window.dispatchEvent(new KeyboardEvent('keydown', { key: '4' }));
    expect(onSelect).toHaveBeenCalledWith('D');
  });

  it('does not trigger onSelect when disabled', () => {
    const onSelect = vi.fn();
    renderHook(() => useOptionKeyboard(onSelect, false));

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'a' }));
    expect(onSelect).not.toHaveBeenCalled();
  });

  it('ignores events originating from input elements', () => {
    const onSelect = vi.fn();
    renderHook(() => useOptionKeyboard(onSelect, true));

    const input = document.createElement('input');
    document.body.appendChild(input);

    const event = new KeyboardEvent('keydown', { key: 'a' });
    Object.defineProperty(event, 'target', { value: input, writable: false });
    window.dispatchEvent(event);

    expect(onSelect).not.toHaveBeenCalled();
    document.body.removeChild(input);
  });
});
