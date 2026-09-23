# Aprende Matemáticas con Kuk 🦜

A complete educational web app for 1st-grade Guatemalan children learning math. Features Kuk the Quetzal as a guide character, 7 CNB modules, and a fully offline-capable PWA.

## Where it runs

The same `public/` folder, unchanged, runs in three places — which is why every path in it is
**relative** (`css/styles.css`, never `/css/styles.css`):

| Where | URL | Offline at home? |
| :--- | :--- | :--- |
| TutorBox classroom (Jetson) | `http://tutorbox/tareas/primero/` | No — plain HTTP has no service worker |
| Android app (APK) | packed by [`../android`](../android/README.md), downloaded from `http://tutorbox/descargas/` | Yes |
| Public hosting (Netlify, see `CLOUD.md`) | `https://<your-site>.netlify.app/` | Yes, via `sw.js` |

## Running locally

No build step and no server code — any static file server works:

```bash
npx serve public     # then open http://localhost:3000
```

---

## App Architecture

```
primero/
└── public/
    ├── index.html         # Single-page app shell
    ├── manifest.json      # PWA manifest
    ├── sw.js              # Service worker (offline on HTTPS hosting; skipped in the APK)
    ├── fonts/             # Nunito, bundled so nothing loads from the internet
    ├── css/
    │   └── styles.css     # Mobile-first CSS (360-414px)
    └── js/
        ├── app.js         # SPA router, global state, init
        ├── kuk.js         # Kuk the Quetzal character (SVG)
        ├── engine/
        │   ├── scene.js   # Base Scene class for lessons
        │   ├── canvas.js  # Canvas helper functions
        │   ├── audio.js   # Web Audio API engine
        │   ├── touch.js   # Touch/mouse normalizer
        │   └── animation.js # Tweening engine
        ├── screens/
        │   ├── map.js     # Adventure map (7 world nodes)
        │   ├── lesson.js  # Lesson container + victory screen
        │   ├── profile.js # Child profile creation/view
        │   └── parent.js  # Parent dashboard (PIN protected)
        ├── data/
        │   ├── modules.js # Module/lesson definitions
        │   └── progress.js# localStorage + server sync
        └── lessons/
            ├── m1-ubicacion/
            │   ├── arriba-abajo.js
            │   ├── adentro-afuera.js
            │   └── cerca-lejos.js
            ├── m2-patrones/patrones-guipil.js
            ├── m3-conjuntos/agrupar-frutas.js
            ├── m4-aritmetica/contar-1-9.js
            ├── m5-problemas/problema-gallinas.js
            ├── m6-geometria/identificar-formas.js
            └── m7-medicion/reloj-interactivo.js
```

---

## CNB Modules

This app covers **Primero (1er grado) only** — one app per grade. Each module is one of the 7
Primero math competencies, and every lesson teaches a content number from that same competency
(source: `../cnb/1er-grado-CNB-1.pdf`, pages 93–98; enforced by `tests/check-lessons.mjs`).

| # | World | Competencia (Primero) | Lessons (contenido CNB) |
|---|-------|-----------------------|-------------------------|
| 1 | Volcán Santiaguito | Relaciones por posición y distancia | Arriba y Abajo · Adentro y Afuera · Cerca y Lejos (1.1.2) |
| 2 | Tejido Maya | Patrones en la cultura y la naturaleza | Patrones del Güipil (2.2.1) · Patrones de la Naturaleza (2.1.1) · Patrones de Formas (2.1.2) |
| 3 | Mercado del Pueblo | Conjuntos | Agrupar Frutas (3.1.2) · Todos, Algunos, Ninguno (3.2.1) · Más o Menos (3.3.1) |
| 4 | Milpa de Maíz | Aritmética básica | Contar del 1 al 9 (4.1.2) · Sumar Jocotes (4.8.1) · Restar Elotes (4.8.6) |
| 5 | Tikal | Solución de problemas | Las Gallinas de María (5.3.1) · La Granja en Gráfica (5.2.2) · Tortillas para la Familia (5.3.1) |
| 6 | Antigua Guatemala | Figuras geométricas | Formas en la Ciudad (6.1.2) · Medir el Contorno (6.2.1) · Construir Figuras (6.1.2) |
| 7 | Lago Atitlán | Medidas, tiempo, calendario | El Reloj del Pueblo (7.2.1) · Los Meses del Año (7.3.1) · Tecomates y Puños (7.1.1) |

---|-------|-------|----------|
| 1 | Volcán Santiaguito | Ubicación (arriba/abajo, adentro/afuera) | Geometría y Medición |
| 2 | Tejido Maya | Patrones del Güipil | Álgebra |
| 3 | Mercado del Pueblo | Conjuntos y clasificación | Números |
| 4 | Milpa de Maíz | Contar 1-9 | Números |
| 5 | Tikal | Problemas de la vida cotidiana | Números |
| 6 | Antigua Guatemala | Figuras geométricas | Geometría |
| 7 | Lago Atitlán | Medición del tiempo | Medición |

---

## How to Add New Lessons

Most lessons are **"look, listen, tap the answer"** and extend `ChoiceLesson`
(`public/js/lessons/shared/choice-lesson.js`), which already does layout, taps, retries, praise,
the 🔊 replay button and stars. A lesson only lists its rounds:

```javascript
// public/js/lessons/m4-aritmetica/sumar-jocotes.js  (CNB Primero 4.8.1)
import { ChoiceLesson, numberChoices } from '../shared/choice-lesson.js';

export default class SumarJocotesLesson extends ChoiceLesson {
  get intro() { return '¡Vamos a juntar jocotes!'; }
  makeRounds() {
    return [[2, 1], [3, 3]].map(([a, b]) => ({
      say: `Aquí hay ${a} jocotes y allá hay ${b}. ¿Cuántos hay en total?`, // what Q'uq' says
      ask: `${a} + ${b} = ?`,                                             // text for the adult
      hint: 'Junta los jocotes y cuéntalos todos.',                        // after a wrong tap
      scene: (ctx, box) => { /* draw the picture inside box */ },
      choices: numberChoices(a + b),  // the answer is computed, never typed by hand
    }));
  }
}
```

Then register it in `public/js/data/modules.js` with its CNB content number, and add the file
to `STATIC_ASSETS` in `public/sw.js`:

```javascript
{ id: 'sumar-jocotes', name: 'Sumar Jocotes', emoji: '➕', cnb: '4.8.1',
  module: () => import('../lessons/m4-aritmetica/sumar-jocotes.js') }
```

Rules the check below enforces: every map entry loads **its own** file, has a CNB number from its
module's competency, and every round has exactly one right answer. In **every** lesson a wrong
answer never ends a round — the child hears "¡Casi!" and a hint, and tries again; stars count
first-try answers. Q'uq' says the intro and the first question as one sentence, because each new
sentence cuts off the previous one.

**Check and preview** (no dependencies):

```bash
node tests/check-lessons.mjs          # structure, one right answer per round, drawing smoke test, retry/stars logic
npx serve .                           # then open /tests/preview.html?lesson=m4-aritmetica/sumar-jocotes&round=2
```

Lessons with free-form interaction (dragging, tracing, the clock) still extend `Scene`
(`public/js/engine/scene.js`) directly — see `m7-medicion/reloj-interactivo.js`.

---

## Art

Everything is drawn in code or SVG; nothing is loaded from the internet.

| What | Where | Notes |
| :--- | :--- | :--- |
| Q'uq' the quetzal | `public/icons/quq.svg` | The **only** drawing of him: every screen shows this file, and canvas lessons use `drawQuq()` from `lessons/shared/draw.js`. |
| App & Android icons | `public/icons/icon.svg`, `icon-192.png`, `icon-512.png`, `../android/.../drawable-nodpi/ic_launcher_foreground.png` | Generated from `quq.svg` — after editing it run `python tools/render-icons.py` (needs Chrome + Pillow). |
| Map worlds | `public/icons/worlds/m1.svg` … `m7.svg` | Volcán Santiaguito, güipil, mercado, milpa, Tikal, Arco de Santa Catalina, Atitlán. |
| Fruit, maize, farm animals | `public/js/lessons/shared/art.js` | Canvas drawings used instead of emoji, so they look the same on every phone (the mango emoji does not exist before Android 9). Pass them anywhere an emoji is accepted. |

Check it all at once: serve this folder and open `tests/gallery.html`; `tests/map-preview.html`
opens the real map with a sample child and stars.

## Design Principles

- **No reading required**: All UI uses images, colors, emojis, audio narration
- **Mobile-first**: Designed for Android phones 360–414px wide
- **Guatemalan context**: All scenarios use local culture, food, places
- **Offline capable**: the APK carries every file; on HTTPS hosting the service worker caches them. Progress lives in `localStorage`
- **No build step**: Pure ES modules; keep every path relative

---

## Tech Stack

- **Frontend**: Vanilla JS (ES Modules) + Canvas API — no backend
- **Offline**: Android WebView wrapper (`../android`); Service Worker + Web App Manifest on HTTPS hosting
- **Audio**: Web Audio API + Web Speech API (the phone's text-to-speech inside the APK)
- **Storage**: `localStorage` only

---

*App made with love for Guatemalan children. ¡Aprende con Kuk! 🦜*
