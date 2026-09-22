import { readFileSync, existsSync } from 'fs';
import { resolve } from 'path';
import { describe, expect, it } from 'vitest';

const APP_ROOT = resolve(__dirname, '../../..');

function readAppFile(...segments: string[]): string {
  return readFileSync(resolve(APP_ROOT, ...segments), 'utf-8');
}

describe('PWA document meta (P0-1)', () => {
  it('allows pinch-zoom and covers the viewport', () => {
    const html = readAppFile('index.html');
    expect(html).not.toMatch(/maximum-scale/);
    expect(html).toMatch(/viewport-fit=cover/);
    expect(html).toMatch(/width=device-width/);
  });

  it('declares theme-color, description and manifest entry', () => {
    const html = readAppFile('index.html');
    expect(html).toMatch(/name="theme-color" content="#0B6E99"/);
    expect(html).toMatch(/name="description"/);
    expect(html).toMatch(/rel="manifest" href="\/manifest\.webmanifest"/);
    expect(html).toMatch(/rel="icon".*favicon\.svg/);
    expect(html).toMatch(/apple-touch-icon/);
  });

  it('ships a valid installable manifest starting at /alumno/', () => {
    const manifestPath = resolve(APP_ROOT, 'public/manifest.webmanifest');
    expect(existsSync(manifestPath)).toBe(true);
    const manifest = JSON.parse(readAppFile('public/manifest.webmanifest'));
    expect(manifest.name).toBe('TutorBox');
    expect(manifest.display).toBe('standalone');
    expect(manifest.start_url).toBe('/alumno/');
    expect(manifest.theme_color).toBe('#0B6E99');
    expect(Array.isArray(manifest.icons)).toBe(true);
    expect(manifest.icons.length).toBeGreaterThan(0);
    for (const icon of manifest.icons) {
      expect(existsSync(resolve(APP_ROOT, `public${icon.src}`))).toBe(true);
    }
  });
});
