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

| # | World | Topic | CNB Area |
|---|-------|-------|----------|
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

Rules the check below enforces: every map entry loads **its own** file, has a CNB number, and
every round has exactly one right answer. A wrong tap never ends a round — the child hears the
hint and tries again; stars count first-try answers.

**Check and preview** (no dependencies):

```bash
node tests/check-lessons.mjs          # structure, one right answer per round, drawing smoke test, retry/stars logic
npx serve .                           # then open /tests/preview.html?lesson=m4-aritmetica/sumar-jocotes&round=2
```

Lessons with free-form interaction (dragging, tracing, the clock) still extend `Scene`
(`public/js/engine/scene.js`) directly — see `m7-medicion/reloj-interactivo.js`.

---

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
