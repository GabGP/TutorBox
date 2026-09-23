// Module Definitions: one module per CNB Primero math competency (m1 = competencia 1 ... m7 = 7).
// Each lesson's `cnb` is a Primero content number from that same competency (checked by
// tests/check-lessons.mjs). Source: ../cnb/1er-grado-CNB-1.pdf, pages 93-98.

export const MODULES = [
  {
    id: 'm1',
    name: 'Ubicación',
    emoji: '🌋',
    color: '#2E7D32',
    bgColor: '#E8F5E9',
    world: 'Volcán Santiaguito',
    description: 'Aprende dónde están las cosas: arriba, abajo, adentro, afuera',
    totalLessons: 3,
    cnb: 'Competencia 1: Establece relaciones entre personas, objetos y figuras geométricas por su posición en el espacio y por la distancia que hay entre ellos.',
    lessons: [
      {
        id: 'arriba-abajo',
        name: 'Arriba y Abajo',
        emoji: '⬆️',
        cnb: '1.1.2',
        module: () => import('../lessons/m1-ubicacion/arriba-abajo.js')
      },
      {
        id: 'adentro-afuera',
        name: 'Adentro y Afuera',
        emoji: '🏠',
        cnb: '1.1.2',
        module: () => import('../lessons/m1-ubicacion/adentro-afuera.js')
      },
      {
        id: 'cerca-lejos',
        name: 'Cerca y Lejos',
        emoji: '👀',
        cnb: '1.1.2',
        module: () => import('../lessons/m1-ubicacion/cerca-lejos.js')
      }
    ]
  },
  {
    id: 'm2',
    name: 'Patrones',
    emoji: '🪡',
    color: '#6A1B9A',
    bgColor: '#F3E5F5',
    world: 'Tejido Maya',
    description: 'Descubre patrones en la naturaleza y en los güipiles mayas',
    totalLessons: 3,
    cnb: 'Competencia 2: Expresa ideas referidas a patrones y relaciones matemáticas que se dan en las manifestaciones culturales en su entorno familiar.',
    lessons: [
      {
        id: 'patrones-guipil',
        name: 'Patrones del Güipil',
        emoji: '🌈',
        cnb: '2.2.1',
        module: () => import('../lessons/m2-patrones/patrones-guipil.js')
      },
      {
        id: 'patrones-naturaleza',
        name: 'Patrones de la Naturaleza',
        emoji: '🌿',
        cnb: '2.1.1',
        module: () => import('../lessons/m2-patrones/patrones-naturaleza.js')
      },
      {
        id: 'patrones-formas',
        name: 'Patrones de Formas',
        emoji: '🔷',
        cnb: '2.1.2',
        module: () => import('../lessons/m2-patrones/patrones-formas.js')
      }
    ]
  },
  {
    id: 'm3',
    name: 'Conjuntos',
    emoji: '🛒',
    color: '#E65100',
    bgColor: '#FFF3E0',
    world: 'Mercado del Pueblo',
    description: 'Agrupa, compara y clasifica frutas del mercado',
    totalLessons: 3,
    cnb: 'Competencia 3: Expresa ideas y pensamientos con libertad y coherencia utilizando diferentes signos, símbolos gráficos, algoritmos y términos matemáticos.',
    lessons: [
      {
        id: 'agrupar-frutas',
        name: 'Agrupar Frutas',
        emoji: '🥭',
        cnb: '3.1.2',
        module: () => import('../lessons/m3-conjuntos/agrupar-frutas.js')
      },
      {
        id: 'todos-algunos-ninguno',
        name: 'Todos, Algunos, Ninguno',
        emoji: '🧺',
        cnb: '3.2.1',
        module: () => import('../lessons/m3-conjuntos/todos-algunos-ninguno.js')
      },
      {
        id: 'mas-menos',
        name: 'Más o Menos',
        emoji: '⚖️',
        cnb: '3.3.1',
        module: () => import('../lessons/m3-conjuntos/mas-menos.js')
      }
    ]
  },
  {
    id: 'm4',
    name: 'Aritmética',
    emoji: '🌽',
    color: '#F9A825',
    bgColor: '#FFFDE7',
    world: 'Milpa de Maíz',
    description: 'Cuenta, suma y resta con jocotes y elotes',
    totalLessons: 3,
    cnb: 'Competencia 4: Utiliza conocimientos y experiencias de aritmética básica en la interacción con su entorno familiar.',
    lessons: [
      {
        id: 'contar-1-9',
        name: 'Contar del 1 al 9',
        emoji: '🔢',
        cnb: '4.1.2',
        module: () => import('../lessons/m4-aritmetica/contar-1-9.js')
      },
      {
        id: 'sumar-jocotes',
        name: 'Sumar Jocotes',
        emoji: '➕',
        cnb: '4.8.1',
        module: () => import('../lessons/m4-aritmetica/sumar-jocotes.js')
      },
      {
        id: 'restar-elotes',
        name: 'Restar Elotes',
        emoji: '➖',
        cnb: '4.8.6',
        module: () => import('../lessons/m4-aritmetica/restar-elotes.js')
      }
    ]
  },
  {
    id: 'm5',
    name: 'Problemas',
    emoji: '🏛️',
    color: '#4E342E',
    bgColor: '#EFEBE9',
    world: 'Tikal',
    description: 'Resuelve problemas y lee gráficas de la granja',
    totalLessons: 3,
    cnb: 'Competencia 5: Expresa opiniones sobre hechos y eventos de la vida cotidiana, relacionados con la solución de problemas.',
    lessons: [
      {
        id: 'problema-gallinas',
        name: 'Las Gallinas de María',
        emoji: '🐔',
        cnb: '5.3.1',
        module: () => import('../lessons/m5-problemas/problema-gallinas.js')
      },
      {
        id: 'granja-grafica',
        name: 'La Granja en Gráfica',
        emoji: '📊',
        cnb: '5.2.2',
        module: () => import('../lessons/m5-problemas/granja-grafica.js')
      },
      {
        id: 'problema-tortillas',
        name: 'Tortillas para la Familia',
        emoji: '🫓',
        cnb: '5.3.1',
        module: () => import('../lessons/m5-problemas/problema-tortillas.js')
      }
    ]
  },
  {
    id: 'm6',
    name: 'Geometría',
    emoji: '⛪',
    color: '#C62828',
    bgColor: '#FFEBEE',
    world: 'Antigua Guatemala',
    description: 'Identifica, compara y mide figuras de tu entorno',
    totalLessons: 3,
    cnb: 'Competencia 6: Identifica formas y relaciones de figuras geométricas vinculadas a situaciones matemáticas y a su entorno familiar.',
    lessons: [
      {
        id: 'identificar-formas',
        name: 'Formas en la Ciudad',
        emoji: '🔺',
        cnb: '6.1.2',
        module: () => import('../lessons/m6-geometria/identificar-formas.js')
      },
      {
        id: 'medir-contorno',
        name: 'Medir el Contorno',
        emoji: '📐',
        cnb: '6.2.1',
        module: () => import('../lessons/m6-geometria/medir-contorno.js')
      },
      {
        id: 'construir-formas',
        name: 'Construir Figuras',
        emoji: '🧱',
        cnb: '6.1.2',
        module: () => import('../lessons/m6-geometria/construir-formas.js')
      }
    ]
  },
  {
    id: 'm7',
    name: 'Medición',
    emoji: '🌊',
    color: '#01579B',
    bgColor: '#E1F5FE',
    world: 'Lago Atitlán',
    description: 'Mide con tecomates y puños, lee el reloj y conoce el calendario',
    totalLessons: 3,
    cnb: 'Competencia 7: Construye nuevos conocimientos a partir de nuevos modelos de la ciencia y la cultura.',
    lessons: [
      {
        id: 'reloj-interactivo',
        name: 'El Reloj del Pueblo',
        emoji: '🕐',
        cnb: '7.2.1',
        module: () => import('../lessons/m7-medicion/reloj-interactivo.js')
      },
      {
        id: 'meses-del-anio',
        name: 'Los Meses del Año',
        emoji: '📅',
        cnb: '7.3.1',
        module: () => import('../lessons/m7-medicion/meses-del-anio.js')
      },
      {
        id: 'tecomates-punos',
        name: 'Tecomates y Puños',
        emoji: '🥣',
        cnb: '7.1.1',
        module: () => import('../lessons/m7-medicion/tecomates-punos.js')
      }
    ]
  }
];

export function getModule(id) {
  return MODULES.find(m => m.id === id);
}

export function getLesson(moduleId, lessonId) {
  const mod = getModule(moduleId);
  if (!mod) return null;
  return mod.lessons.find(l => l.id === lessonId);
}
