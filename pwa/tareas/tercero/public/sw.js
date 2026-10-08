// Service Worker - Aprende Matemáticas con Q'uq'
// Cache-first for assets, network-first for API

const CACHE_VERSION = 'v1';
const CACHE_NAME = `kuk3-math-${CACHE_VERSION}`;

const STATIC_ASSETS = [
  './',
  './css/styles.css',
  './fonts/nunito-latin.woff2',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon.svg',
  './icons/quq.svg',
  './icons/worlds/m1.svg',
  './icons/worlds/m2.svg',
  './icons/worlds/m3.svg',
  './icons/worlds/m4.svg',
  './icons/worlds/m5.svg',
  './icons/worlds/m6.svg',
  './icons/worlds/m7.svg',
  './index.html',
  './js/app.js',
  './js/data/modules.js',
  './js/data/progress.js',
  './js/engine/animation.js',
  './js/engine/audio.js',
  './js/engine/canvas.js',
  './js/engine/scene.js',
  './js/engine/touch.js',
  './js/kuk.js',
  './js/lessons/m1-patrones/patrones-tabla.js',
  './js/lessons/m1-patrones/piensa-patron.js',
  './js/lessons/m1-patrones/secuencias.js',
  './js/lessons/m2-ubicacion/cruz-maya.js',
  './js/lessons/m2-ubicacion/dibujo-pares.js',
  './js/lessons/m2-ubicacion/plano-cardinal.js',
  './js/lessons/m3-conjuntos/iguales-equivalentes.js',
  './js/lessons/m3-conjuntos/union-interseccion.js',
  './js/lessons/m3-conjuntos/vacio-unitario.js',
  './js/lessons/m4-aritmetica/division-residuo.js',
  './js/lessons/m4-aritmetica/fracciones.js',
  './js/lessons/m4-aritmetica/mayas-grandes.js',
  './js/lessons/m4-aritmetica/miles.js',
  './js/lessons/m4-aritmetica/multiplicar-repartir.js',
  './js/lessons/m4-aritmetica/recta-comparar.js',
  './js/lessons/m4-aritmetica/sumas-restas.js',
  './js/lessons/m5-problemas/pictogramas.js',
  './js/lessons/m5-problemas/problemas-dos-pasos.js',
  './js/lessons/m5-problemas/seguro-posible.js',
  './js/lessons/m6-geometria/angulos.js',
  './js/lessons/m6-geometria/cubos-prismas.js',
  './js/lessons/m6-geometria/eje-simetria.js',
  './js/lessons/m6-geometria/paralelas-poligonos.js',
  './js/lessons/m6-geometria/perimetro.js',
  './js/lessons/m7-medicion/calendarios.js',
  './js/lessons/m7-medicion/dias-siglos.js',
  './js/lessons/m7-medicion/geme-paso.js',
  './js/lessons/m7-medicion/pesos-capacidad.js',
  './js/lessons/m7-medicion/quetzales.js',
  './js/lessons/m7-medicion/reloj-minutos.js',
  './js/lessons/shared/art.js',
  './js/lessons/shared/choice-lesson.js',
  './js/lessons/shared/draw.js',
  './js/screens/lesson.js',
  './js/screens/map.js',
  './js/screens/parent.js',
  './js/screens/profile.js',
  './manifest.json',
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
