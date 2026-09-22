import { readFileSync } from 'fs';
import { resolve } from 'path';
import { describe, expect, it } from 'vitest';

const APP_ROOT = resolve(__dirname, '../../..');

function readAppFile(...segments: string[]): string {
  return readFileSync(resolve(APP_ROOT, ...segments), 'utf-8');
}

describe('Student mood wash scoping (P0-2)', () => {
  it('keeps body[data-mood] as hook without !important white-wash', () => {
    const tokens = readAppFile('src/app/styles/tokens.css');
    expect(tokens).toMatch(/body\[data-mood='good'\]/);
    const start = tokens.indexOf('Dynamic shell mood');
    const end = tokens.indexOf('@media (prefers-reduced-motion', start);
    const moodBlock = tokens.slice(start, end === -1 ? undefined : end);
    expect(moodBlock).not.toMatch(/!important/);
    expect(moodBlock).not.toMatch(/body\[data-mood\] header/);
    expect(moodBlock).not.toMatch(/body\[data-mood\] p/);
  });

  it('disables motion for reduced-motion users', () => {
    const tokens = readAppFile('src/app/styles/tokens.css');
    const animations = readAppFile('src/app/styles/animations.css');
    for (const css of [tokens, animations]) {
      expect(css).toMatch(/prefers-reduced-motion: reduce/);
    }
  });

  it('renders the pedagogical explanation as a solid readable card', () => {
    const css = readAppFile('src/pages/student/StudentResultScreen.module.css');
    expect(css).toMatch(/\.explain/);
    expect(css).toMatch(/background: #fff/);
    expect(css).toMatch(/color: var\(--ink\)/);
  });
});
