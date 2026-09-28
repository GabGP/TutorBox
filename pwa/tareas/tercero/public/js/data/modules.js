// Module Definitions: one level per CNB Tercero math competency (m1 = competencia 1 ... m7 = 7).
// Each lesson's `cnb` is a Tercero content number from that same competency (checked by
// tests/check-lessons.mjs). Source: ../cnb/3ro primaria.docx, área de Matemáticas.

const lesson = (id, name, emoji, cnb, load) => ({ id, name, emoji, cnb, module: load });

export const MODULES = [
  {
    id: 'm1',
    name: 'Patrones',
    emoji: '🪡',
    color: '#6A1B9A',
    bgColor: '#F3E5F5',
    world: 'Tejido Maya',
    description: 'Descubre reglas de suma, resta y multiplicación en patrones que crecen',
    cnb: 'Competencia 1: Construye patrones y establece relaciones que le facilitan la interpretación de signos y señales utilizados para el desplazamiento en su comunidad y otros contextos.',
    lessons: [
      lesson('secuencias', 'Secuencias con Reglas', '🔢', '1.3.1', () => import('../lessons/m1-patrones/secuencias.js')),
      lesson('patrones-tabla', 'Patrones que Crecen', '🌸', '1.2.1', () => import('../lessons/m1-patrones/patrones-tabla.js')),
      lesson('piensa-patron', 'Piensa en el Patrón', '🧩', '1.5.1', () => import('../lessons/m1-patrones/piensa-patron.js')),
    ],
  },
  {
    id: 'm2',
    name: 'Ubicación',
    emoji: '🌋',
    color: '#2E7D32',
    bgColor: '#E8F5E9',
    world: 'Volcán Santiaguito',
    description: 'La Cruz Maya, los puntos cardinales y dibujos con pares ordenados',
    cnb: 'Competencia 2: Utiliza diferentes estrategias para representar los algoritmos y términos matemáticos en su entorno cultural, familiar, escolar y comunitario.',
    lessons: [
      lesson('cruz-maya', 'La Cruz Maya', '🧭', '2.1.3', () => import('../lessons/m2-ubicacion/cruz-maya.js')),
      lesson('plano-cardinal', 'Caminos Cardinales', '🗺️', '2.2.1', () => import('../lessons/m2-ubicacion/plano-cardinal.js')),
      lesson('dibujo-pares', 'Dibujos con Pares', '📍', '2.2.2', () => import('../lessons/m2-ubicacion/dibujo-pares.js')),
    ],
  },
  {
    id: 'm3',
    name: 'Conjuntos',
    emoji: '🛒',
    color: '#E65100',
    bgColor: '#FFF3E0',
    world: 'Mercado del Pueblo',
    description: 'Conjuntos vacíos y unitarios, iguales y equivalentes, unión e intersección',
    cnb: 'Competencia 3: Propone diferentes ideas y pensamientos con libertad y coherencia utilizando diferentes signos, símbolos gráficos, algoritmos y términos matemáticos.',
    lessons: [
      lesson('vacio-unitario', 'Vacío y Unitario', '🫙', '3.1.1', () => import('../lessons/m3-conjuntos/vacio-unitario.js')),
      lesson('iguales-equivalentes', 'Iguales y Equivalentes', '⚖️', '3.2.1', () => import('../lessons/m3-conjuntos/iguales-equivalentes.js')),
      lesson('union-interseccion', 'Unión e Intersección', '⭕', '3.3.2', () => import('../lessons/m3-conjuntos/union-interseccion.js')),
    ],
  },
  {
    id: 'm4',
    name: 'Aritmética',
    emoji: '🌽',
    color: '#F9A825',
    bgColor: '#FFFDE7',
    world: 'Milpa de Maíz',
    description: 'Números hasta 10,000 y mayas grandes, operaciones, divisiones y fracciones',
    cnb: 'Competencia 4: Aplica conocimientos y experiencias de aritmética básica en la interacción con su entorno familiar, escolar y comunitario.',
    lessons: [
      lesson('mayas-grandes', 'Mayas Grandes', '🐚', '4.1.7', () => import('../lessons/m4-aritmetica/mayas-grandes.js')),
      lesson('miles', 'Hasta 10,000', '🔟', '4.1.6', () => import('../lessons/m4-aritmetica/miles.js')),
      lesson('recta-comparar', 'Recta y Comparar', '📏', '4.1.4', () => import('../lessons/m4-aritmetica/recta-comparar.js')),
      lesson('sumas-restas', 'Sumas y Restas', '➕', '4.2.1', () => import('../lessons/m4-aritmetica/sumas-restas.js')),
      lesson('multiplicar-repartir', 'Multiplicar y Repartir', '✖️', '4.3.1', () => import('../lessons/m4-aritmetica/multiplicar-repartir.js')),
      lesson('division-residuo', 'Dividir con Residuo', '➗', '4.3.3', () => import('../lessons/m4-aritmetica/division-residuo.js')),
      lesson('fracciones', 'Comparar Fracciones', '🍕', '4.4.2', () => import('../lessons/m4-aritmetica/fracciones.js')),
    ],
  },
  {
    id: 'm5',
    name: 'Problemas',
    emoji: '🏛️',
    color: '#4E342E',
    bgColor: '#EFEBE9',
    world: 'Tikal',
    description: 'Problemas de dos pasos, pictogramas y lo seguro, posible o imposible',
    cnb: 'Competencia 5: Aplica conocimientos matemáticos en la sistematización de soluciones diversas a problemas de la vida cotidiana.',
    lessons: [
      lesson('problemas-dos-pasos', 'Problemas de Dos Pasos', '🧮', '5.2.1', () => import('../lessons/m5-problemas/problemas-dos-pasos.js')),
      lesson('pictogramas', 'Pictogramas y Barras', '📊', '5.1.2', () => import('../lessons/m5-problemas/pictogramas.js')),
      lesson('seguro-posible', 'Seguro o Posible', '🎲', '5.3.1', () => import('../lessons/m5-problemas/seguro-posible.js')),
    ],
  },
  {
    id: 'm6',
    name: 'Geometría',
    emoji: '⛪',
    color: '#C62828',
    bgColor: '#FFEBEE',
    world: 'Antigua Guatemala',
    description: 'Ángulos, paralelas, cubos y prismas, perímetro y ejes de simetría',
    cnb: 'Competencia 6: Utiliza la información que obtiene de las relaciones de diferentes elementos expresándolas en forma gráfica.',
    lessons: [
      lesson('angulos', 'Tipos de Ángulos', '📐', '6.1.2', () => import('../lessons/m6-geometria/angulos.js')),
      lesson('paralelas-poligonos', 'Paralelas y Polígonos', '🛤️', '6.1.4', () => import('../lessons/m6-geometria/paralelas-poligonos.js')),
      lesson('cubos-prismas', 'Cubos y Prismas', '📦', '6.1.7', () => import('../lessons/m6-geometria/cubos-prismas.js')),
      lesson('perimetro', 'Perímetro', '📏', '6.2.1', () => import('../lessons/m6-geometria/perimetro.js')),
      lesson('eje-simetria', 'Ejes de Simetría', '🦋', '6.3.1', () => import('../lessons/m6-geometria/eje-simetria.js')),
    ],
  },
  {
    id: 'm7',
    name: 'Medición',
    emoji: '🌊',
    color: '#01579B',
    bgColor: '#E1F5FE',
    world: 'Lago Atitlán',
    description: 'Reloj en minutos, calendarios, pesos y galones, quetzales y medidas del cuerpo',
    cnb: 'Competencia 7: Aplica nuevos conocimientos a partir de nuevos modelos de la ciencia y la cultura.',
    lessons: [
      lesson('reloj-minutos', 'Reloj en Minutos', '🕐', '7.6.1', () => import('../lessons/m7-medicion/reloj-minutos.js')),
      lesson('dias-siglos', 'Días y Siglos', '📆', '7.6.3', () => import('../lessons/m7-medicion/dias-siglos.js')),
      lesson('calendarios', 'Calendario Maya', '📅', '7.7.2', () => import('../lessons/m7-medicion/calendarios.js')),
      lesson('pesos-capacidad', 'Libras y Galones', '⚖️', '7.2.1', () => import('../lessons/m7-medicion/pesos-capacidad.js')),
      lesson('quetzales', 'Quetzales y Centavos', '💵', '7.5.2', () => import('../lessons/m7-medicion/quetzales.js')),
      lesson('geme-paso', 'Geme, Paso y Brazada', '👣', '7.1.1', () => import('../lessons/m7-medicion/geme-paso.js')),
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
