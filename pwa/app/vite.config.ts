import { existsSync, mkdirSync, copyFileSync } from 'fs';
import { resolve } from 'path';
import { defineConfig, Plugin } from 'vite';
import react from '@vitejs/plugin-react';

function tutorboxRouterPlugin(): Plugin {
  return {
    name: 'tutorbox-router-plugin',
    closeBundle() {
      const outDir = resolve(import.meta.dirname, '../../.cache/pwa/dist');
      const indexHtml = resolve(outDir, 'index.html');
      if (existsSync(indexHtml)) {
        for (const page of ['alumno', 'maestro', 'pantalla']) {
          const destDir = resolve(outDir, page);
          mkdirSync(destDir, { recursive: true });
          copyFileSync(indexHtml, resolve(destDir, 'index.html'));
        }
      }
      const legacyCss = resolve(import.meta.dirname, '../pilas/static/tb.css');
      const destStatic = resolve(outDir, 'static');
      if (existsSync(legacyCss) && existsSync(destStatic)) {
        copyFileSync(legacyCss, resolve(destStatic, 'tb.css'));
      }
    },
  };
}

export default defineConfig({
  plugins: [react(), tutorboxRouterPlugin()],
  base: '/',
  cacheDir: resolve(import.meta.dirname, '../../.cache/pwa/vite'),
  build: {
    outDir: resolve(import.meta.dirname, '../../.cache/pwa/dist'),
    assetsDir: 'static',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
