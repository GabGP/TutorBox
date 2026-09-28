[TutorBox](../../../README.md) › [pwa](../../README.md) › tareas › tercero

# Matemáticas 3º con Q'uq'

Third-grade (Tercero) math for Guatemalan children, the sibling of [`../primero`](../primero/README.md)
and [`../segundo`](../segundo/README.md): same engine, same Q'uq', same design rules (look, listen,
tap; offline; Guatemalan context). Only the content changes: **7 levels, one per CNB Tercero math
competencia**, 30 lessons.

## Where it runs

| Where | URL |
| :--- | :--- |
| TutorBox classroom (Jetson) | `http://tutorbox/tareas/tercero/` (mounted in `backend/src/main.py`, `REPO_MOUNTS`) |
| Any static host | serve `public/` — every path is relative |

There is no APK for Tercero yet: [`../android`](../android/README.md) packs `primero/public` only.

## Running and checking

```bash
npx serve public                 # the app
node tests/check-lessons.mjs     # structure, one right answer per round, drawing smoke test, retry/stars
npx serve .                      # then open:
                                 #   /tests/rounds.html        every round of every lesson at phone size (?m=m4 for one level)
                                 #   /tests/preview.html?lesson=m4-aritmetica/miles&round=2
                                 #   /tests/map-preview.html   the map with a sample child and stars
```

## Levels

Each lesson's CNB number is the content it mainly teaches; the header comment of each file lists
every content number its rounds cover. Source: `../cnb/3ro primaria.docx`.

| # | World | Competencia (Tercero) | Lessons (contenido CNB) |
|---|-------|-----------------------|-------------------------|
| 1 | Tejido Maya | Patrones y relaciones | Secuencias con Reglas (1.3.1) · Patrones que Crecen (1.2.1) · Piensa en el Patrón (1.5.1) |
| 2 | Volcán Santiaguito | Desplazamientos y señales | La Cruz Maya (2.1.3) · Caminos Cardinales (2.2.1) · Dibujos con Pares (2.2.2) |
| 3 | Mercado del Pueblo | Conjuntos | Vacío y Unitario (3.1.1) · Iguales y Equivalentes (3.2.1) · Unión e Intersección (3.3.2) |
| 4 | Milpa de Maíz | Aritmética básica | Mayas Grandes (4.1.7) · Hasta 10,000 (4.1.6) · Recta y Comparar (4.1.4) · Sumas y Restas (4.2.1) · Multiplicar y Repartir (4.3.1) · Dividir con Residuo (4.3.3) · Comparar Fracciones (4.4.2) |
| 5 | Tikal | Solución de problemas | Problemas de Dos Pasos (5.2.1) · Pictogramas y Barras (5.1.2) · Seguro o Posible (5.3.1) |
| 6 | Antigua Guatemala | Figuras y sólidos | Tipos de Ángulos (6.1.2) · Paralelas y Polígonos (6.1.4) · Cubos y Prismas (6.1.7) · Perímetro (6.2.1) · Ejes de Simetría (6.3.1) |
| 7 | Lago Atitlán | Medidas, tiempo, calendarios, dinero | Reloj en Minutos (7.6.1) · Días y Siglos (7.6.3) · Calendario Maya (7.7.2) · Libras y Galones (7.2.1) · Quetzales y Centavos (7.5.2) · Geme, Paso y Brazada (7.1.1) |

Levels 4, 6 and 7 have more lessons because their competencias have many more contents; the map,
stars and unlock logic all read the lesson count from `data/modules.js`.

Not covered on purpose: 4.1.8 (the meaning of 1 and 13 in the Maya cosmovision), 4.4.4 (fraction
words in Mayan languages) and the four year bearers of 7.7 — cultural content that should come from
a teacher or community source, not be invented by the app.

## Adding a lesson

Same rules as Segundo: every lesson is a `ChoiceLesson` that only returns rounds; answers are
computed in code and each wrong choice is a real mistake (`noCarry(1568, 2275)` -> 3,733,
`smallFromBig(5000, 1234)` -> 4,234, `2:70` for 2:30 + 40 minutes). Numbers drawn with `drawText`
get the thousands comma (`num(3407)` -> `3,407`). Wide pictures use `stacked()`, only in rounds
without a scene (the checker fails otherwise). Register the lesson in `data/modules.js` and add the
file to `STATIC_ASSETS` in `public/sw.js`.

## Storage

Progress lives in `localStorage` under `kuk3_progress_v1` / `kuk3_current_user` — different from
Primero (`kuk_*`) and Segundo (`kuk2_*`), because on the Jetson all grades share one origin and use
level ids `m1`–`m7`.
