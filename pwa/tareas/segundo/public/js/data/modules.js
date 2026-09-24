// Module Definitions: one level per CNB Segundo math competency (m1 = competencia 1 ... m7 = 7).
// Each lesson's `cnb` is a Segundo content number from that same competency (checked by
// tests/check-lessons.mjs). Source: ../cnb/2do-grado-CNB-1.pdf, área de Matemáticas.

const lesson = (id, name, emoji, cnb, load) => ({ id, name, emoji, cnb, module: load });

export const MODULES = [
  {
    id: 'm1',
    name: 'Patrones',
    emoji: '🪡',
    color: '#6A1B9A',
    bgColor: '#F3E5F5',
    world: 'Tejido Maya',
    description: 'Crea patrones, encuentra errores y mide la distancia entre sus partes',
    cnb: 'Competencia 1: Construye patrones clasificando los elementos y determinando relaciones y distancias entre cada uno de ellos.',
    lessons: [
      lesson('patrones-tejido', 'Patrones del Tejido', '🌈', '1.2.2', () => import('../lessons/m1-patrones/patrones-tejido.js')),
      lesson('patron-diferente', '¿Cuál es Diferente?', '🔍', '1.1.1', () => import('../lessons/m1-patrones/patron-diferente.js')),
      lesson('patron-regla', 'Flores en la Regla', '📏', '1.2.4', () => import('../lessons/m1-patrones/patron-regla.js')),
    ],
  },
  {
    id: 'm2',
    name: 'Ubicación',
    emoji: '🌋',
    color: '#2E7D32',
    bgColor: '#E8F5E9',
    world: 'Volcán Santiaguito',
    description: 'Ubica puntos en el plano, sigue caminos y ordena lo que pasa en el tiempo',
    cnb: 'Competencia 2: Relaciona ideas y pensamientos referidos a diferentes signos y gráficas, algoritmos y términos matemáticos de su entorno familiar, escolar y cultural.',
    lessons: [
      lesson('plano-puntos', 'Puntos en el Plano', '📍', '2.2.2', () => import('../lessons/m2-ubicacion/plano-puntos.js')),
      lesson('plano-caminos', 'Caminos en el Plano', '🧭', '2.2.1', () => import('../lessons/m2-ubicacion/plano-caminos.js')),
      lesson('antes-despues', 'Antes y Después', '⏳', '2.1.2', () => import('../lessons/m2-ubicacion/antes-despues.js')),
    ],
  },
  {
    id: 'm3',
    name: 'Conjuntos',
    emoji: '🛒',
    color: '#E65100',
    bgColor: '#FFF3E0',
    world: 'Mercado del Pueblo',
    description: 'Decide qué pertenece, forma subconjuntos y clasifica por varias características',
    cnb: 'Competencia 3: Relaciona ideas y pensamientos con libertad y coherencia utilizando diferentes signos, símbolos gráficos, algoritmos y términos matemáticos.',
    lessons: [
      lesson('pertenece', '¿Pertenece?', '🧺', '3.1.1', () => import('../lessons/m3-conjuntos/pertenece.js')),
      lesson('subconjuntos', 'Subconjuntos', '🥭', '3.2.1', () => import('../lessons/m3-conjuntos/subconjuntos.js')),
      lesson('clasificar', 'Clasificar Figuras', '🔷', '3.3.1', () => import('../lessons/m3-conjuntos/clasificar.js')),
    ],
  },
  {
    id: 'm4',
    name: 'Aritmética',
    emoji: '🌽',
    color: '#F9A825',
    bgColor: '#FFFDE7',
    world: 'Milpa de Maíz',
    description: 'Números mayas, centenas, series, sumas, restas, multiplicación y fracciones',
    cnb: 'Competencia 4: Utiliza conocimientos y experiencias de aritmética básica en la interacción con su entorno familiar, escolar y comunitario.',
    lessons: [
      lesson('numeros-mayas', 'Números Mayas', '🐚', '4.1.3', () => import('../lessons/m4-aritmetica/numeros-mayas.js')),
      lesson('centenas', 'Centenas', '💯', '4.4.1', () => import('../lessons/m4-aritmetica/centenas.js')),
      lesson('series-recta', 'Series y Recta', '🔢', '4.5.1', () => import('../lessons/m4-aritmetica/series-recta.js')),
      lesson('sumar-restar', 'Sumar y Restar', '➕', '4.8.1', () => import('../lessons/m4-aritmetica/sumar-restar.js')),
      lesson('multiplicar', 'Multiplicar', '✖️', '4.9.2', () => import('../lessons/m4-aritmetica/multiplicar.js')),
      lesson('fracciones', 'Fracciones', '🍕', '4.10.3', () => import('../lessons/m4-aritmetica/fracciones.js')),
    ],
  },
  {
    id: 'm5',
    name: 'Problemas',
    emoji: '🏛️',
    color: '#4E342E',
    bgColor: '#EFEBE9',
    world: 'Tikal',
    description: 'Resuelve problemas, prueba y piensa, y lee gráficas de barras',
    cnb: 'Competencia 5: Emite juicios identificando causas y efectos para la solución de problemas en la vida cotidiana.',
    lessons: [
      lesson('problemas-mercado', 'Problemas del Mercado', '🛍️', '5.1.1', () => import('../lessons/m5-problemas/problemas-mercado.js')),
      lesson('piensa-resuelve', 'Prueba y Piensa', '🕵️', '5.2.1', () => import('../lessons/m5-problemas/piensa-resuelve.js')),
      lesson('grafica-barras', 'Gráfica de Barras', '📊', '5.4.3', () => import('../lessons/m5-problemas/grafica-barras.js')),
    ],
  },
  {
    id: 'm6',
    name: 'Geometría',
    emoji: '⛪',
    color: '#C62828',
    bgColor: '#FFEBEE',
    world: 'Antigua Guatemala',
    description: 'Ángulos rectos, sólidos, perímetro en centímetros y simetría',
    cnb: 'Competencia 6: Relaciona figuras geométricas con situaciones matemáticas y con su entorno familiar y escolar.',
    lessons: [
      lesson('figuras-angulos', 'Lados y Ángulos', '📐', '6.1.3', () => import('../lessons/m6-geometria/figuras-angulos.js')),
      lesson('solidos', 'Sólidos', '📦', '6.1.5', () => import('../lessons/m6-geometria/solidos.js')),
      lesson('perimetro-cm', 'Perímetro', '📏', '6.2.1', () => import('../lessons/m6-geometria/perimetro-cm.js')),
      lesson('simetria', 'Simetría', '🦋', '6.5.1', () => import('../lessons/m6-geometria/simetria.js')),
    ],
  },
  {
    id: 'm7',
    name: 'Medición',
    emoji: '🌊',
    color: '#01579B',
    bgColor: '#E1F5FE',
    world: 'Lago Atitlán',
    description: 'Reloj, metros, libras y litros, el Cholq\'ij y los quetzales',
    cnb: 'Competencia 7: Utiliza nuevos conocimientos a partir de nuevos modelos de la ciencia y la cultura.',
    lessons: [
      lesson('reloj', 'El Reloj', '🕐', '7.4.1', () => import('../lessons/m7-medicion/reloj.js')),
      lesson('medidas', 'Metros y Libras', '⚖️', '7.2.2', () => import('../lessons/m7-medicion/medidas.js')),
      lesson('cholqij', 'Calendario Cholq\'ij', '📅', '7.5.2', () => import('../lessons/m7-medicion/cholqij.js')),
      lesson('dinero', 'Quetzales', '💵', '7.6.2', () => import('../lessons/m7-medicion/dinero.js')),
    ],
  },
];

MODULES.forEach((m) => { m.totalLessons = m.lessons.length; });

export function getModule(id) {
  return MODULES.find(m => m.id === id);
}

export function getLesson(moduleId, lessonId) {
  const mod = getModule(moduleId);
  if (!mod) return null;
  return mod.lessons.find(l => l.id === lessonId);
}
