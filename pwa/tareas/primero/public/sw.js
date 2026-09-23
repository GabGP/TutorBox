// Service Worker - Aprende Matemáticas con Q'uq'
// Cache-first for assets, network-first for API

const CACHE_VERSION = 'v4';
const CACHE_NAME = `kuk-math-${CACHE_VERSION}`;

const STATIC_ASSETS = [
  './',
  './index.html',
  './css/styles.css',
  './js/app.js',
  './js/kuk.js',
  './js/engine/scene.js',
  './js/engine/canvas.js',
  './js/engine/audio.js',
  './js/engine/touch.js',
  './js/engine/animation.js',
  './js/screens/map.js',
  './js/screens/lesson.js',
  './js/screens/profile.js',
  './js/screens/parent.js',
  './js/data/modules.js',
  './js/data/progress.js',
  './js/lessons/m1-ubicacion/arriba-abajo.js',
  './js/lessons/m1-ubicacion/adentro-afuera.js',
  './js/lessons/m1-ubicacion/cerca-lejos.js',
  './js/lessons/m2-patrones/patrones-guipil.js',
  './js/lessons/m3-conjuntos/agrupar-frutas.js',
  './js/lessons/m4-aritmetica/contar-1-9.js',
  './js/lessons/m5-problemas/problema-gallinas.js',
  './js/lessons/m6-geometria/identificar-formas.js',
  './js/lessons/m7-medicion/reloj-interactivo.js',
  './js/lessons/shared/choice-lesson.js',
  './js/lessons/shared/draw.js',
  './js/lessons/m2-patrones/patrones-numeros.js',
  './js/lessons/m2-patrones/patrones-formas.js',
  './js/lessons/m3-conjuntos/contar-conjunto.js',
  './js/lessons/m3-conjuntos/mas-menos.js',
  './js/lessons/m4-aritmetica/sumar-jocotes.js',
  './js/lessons/m4-aritmetica/restar-elotes.js',
  './js/lessons/m5-problemas/problema-quetzales.js',
  './js/lessons/m5-problemas/problema-tortillas.js',
  './js/lessons/m6-geometria/formas-naturaleza.js',
  './js/lessons/m6-geometria/construir-formas.js',
  './js/lessons/m7-medicion/dias-semana.js',
  './js/lessons/m7-medicion/mas-alto-bajo.js',
  './manifest.json',
  './fonts/nunito-latin.woff2',
  './icons/icon-192.svg',
  './icons/icon-512.svg'
];

// Install: cache all static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('[SW] Caching static assets');
      return cache.addAll(STATIC_ASSETS).catch(err => {
        console.warn('[SW] Some assets failed to cache:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activate: clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => {
            console.log('[SW] Deleting old cache:', key);
            return caches.delete(key);
          })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch: cache-first for all assets
self.addEventListener('fetch', event => {
  event.respondWith(cacheFirst(event.request));
});

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    // Return offline fallback if available
    const fallback = await caches.match('./index.html');
    return fallback || new Response('Offline', { status: 503 });
  }
}

