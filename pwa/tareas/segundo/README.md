[TutorBox](../../../README.md) › [pwa](../../README.md) › tareas › segundo

# Matemáticas 2º con Q'uq'

Second-grade (Segundo) math for Guatemalan children, the sibling of [`../primero`](../primero/README.md):
same engine, same Q'uq', same design rules (look, listen, tap; no reading required; offline; Guatemalan
context). Only the content changes: **7 levels, one per CNB Segundo math competencia**.

## Where it runs

| Where | URL |
| :--- | :--- |
| TutorBox classroom (Jetson) | `http://tutorbox/tareas/segundo/` (mounted in `backend/src/main.py`, `REPO_MOUNTS`) |
| Any static host | serve `public/` — every path is relative |

There is no APK for Segundo yet: [`../android`](../android/README.md) packs `primero/public` only.

## Running and checking

```bash
npx serve public                 # the app
node tests/check-lessons.mjs     # structure, one right answer per round, drawing smoke test, retry/stars
npx serve .                      # then open:
                                 #   /tests/rounds.html        every round of every lesson at phone size (?m=m4 for one level)
                                 #   /tests/preview.html?lesson=m4-aritmetica/numeros-mayas&round=2
                                 #   /tests/map-preview.html   the map with a sample child and stars
```

## Levels

Each lesson's CNB number is the content it mainly teaches; the header comment of each file lists
every content number its rounds cover. Source: `../cnb/2do-grado-CNB-1.pdf`.

| # | World | Competencia (Segundo) | Lessons (contenido CNB) |
|---|-------|-----------------------|-------------------------|
| 1 | Tejido Maya | Construye patrones | Patrones del Tejido (1.2.2) · ¿Cuál es Diferente? (1.1.1) · Flores en la Regla (1.2.4) |
| 2 | Volcán Santiaguito | Signos, gráficas: posición y tiempo | Puntos en el Plano (2.2.2) · Caminos en el Plano (2.2.1) · Antes y Después (2.1.2) |
| 3 | Mercado del Pueblo | Conjuntos | ¿Pertenece? (3.1.1) · Subconjuntos (3.2.1) · Clasificar Figuras (3.3.1) |
| 4 | Milpa de Maíz | Aritmética básica | Números Mayas (4.1.3) · Centenas (4.4.1) · Series y Recta (4.5.1) · Sumar y Restar (4.8.1) · Multiplicar (4.9.2) · Fracciones (4.10.3) |
| 5 | Tikal | Solución de problemas | Problemas del Mercado (5.1.1) · Prueba y Piensa (5.2.1) · Gráfica de Barras (5.4.3) |
| 6 | Antigua Guatemala | Figuras geométricas | Lados y Ángulos (6.1.3) · Sólidos (6.1.5) · Perímetro (6.2.1) · Simetría (6.5.1) |
| 7 | Lago Atitlán | Medidas, tiempo, calendario, dinero | El Reloj (7.4.1) · Metros y Libras (7.2.2) · Calendario Cholq'ij (7.5.2) · Quetzales (7.6.2) |

Level 4 has six lessons because competencia 4 alone has ten indicators; the map, stars and unlock
logic all read the lesson count from `data/modules.js`.

## Adding a lesson

Every Segundo lesson is a `ChoiceLesson` (`public/js/lessons/shared/choice-lesson.js`) that only
returns its rounds; the checker fails anything else. Compute answers in code, and make each wrong
choice a real mistake a child makes (`pickChoices(32 - 7, [35, 24])`: 35 comes from subtracting the
small digit from the big one). Shared drawings: `drawText`, `drawBlocks` (base-ten blocks) and
`drawMaya` (Maya numerals) in `shared/draw.js`; `stacked()` for wide pictures such as clocks.
Register the lesson in `data/modules.js` and add the file to `STATIC_ASSETS` in `public/sw.js`.

## Storage

Progress lives in `localStorage` under `kuk2_progress_v1` / `kuk2_current_user` — different from
Primero's keys, because on the Jetson both apps share one origin and both use level ids `m1`–`m7`.
