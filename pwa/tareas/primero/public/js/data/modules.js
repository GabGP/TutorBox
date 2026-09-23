// Module Definitions - All 7 CNB Modules
// Each module maps to a real Guatemalan location and CNB competency

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
    cnb: 'Geometría y Medición - Posición y ubicación',
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
    description: 'Descubre los patrones en los güipiles mayas',
    totalLessons: 3,
    cnb: 'Álgebra - Patrones y secuencias',
    lessons: [
      {
        id: 'patrones-guipil',
        name: 'Patrones del Güipil',
        emoji: '🌈',
        cnb: '2.2.1',
        module: () => import('../lessons/m2-patrones/patrones-guipil.js')
      },
      {
        id: 'patrones-numeros',
        name: 'Patrones de Números',
        emoji: '🔢',
        cnb: '4.1.5',
        module: () => import('../lessons/m2-patrones/patrones-numeros.js')
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
    description: 'Agrupa y clasifica frutas del mercado guatemalteco',
    totalLessons: 3,
    cnb: 'Números - Conjuntos y clasificación',
    lessons: [
      {
        id: 'agrupar-frutas',
        name: 'Agrupar Frutas',
        emoji: '🥭',
        cnb: '3.1.2',
        module: () => import('../lessons/m3-conjuntos/agrupar-frutas.js')
      },
      {
        id: 'contar-conjunto',
        name: 'Contar el Conjunto',
        emoji: '🧺',
        cnb: '4.1.2',
        module: () => import('../lessons/m3-conjuntos/contar-conjunto.js')
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
    description: 'Cuenta del 1 al 9 con jocotes y maíz guatemalteco',
    totalLessons: 3,
    cnb: 'Números - Operaciones básicas de suma y resta',
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
    description: 'Resuelve problemas de la vida diaria guatemalteca',
    totalLessons: 3,
    cnb: 'Números - Resolución de problemas',
    lessons: [
      {
        id: 'problema-gallinas',
        name: 'Las Gallinas de María',
        emoji: '🐔',
        cnb: '5.3.1',
        module: () => import('../lessons/m5-problemas/problema-gallinas.js')
      },
      {
        id: 'problema-quetzales',
        name: 'Quetzales del Mercado',
        emoji: '💰',
        cnb: '7.4.1',
        module: () => import('../lessons/m5-problemas/problema-quetzales.js')
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
    description: 'Identifica figuras en la arquitectura de la Antigua',
    totalLessons: 3,
    cnb: 'Geometría - Identificación de figuras planas',
    lessons: [
      {
        id: 'identificar-formas',
        name: 'Formas en la Ciudad',
        emoji: '🔺',
        cnb: '1.4.1',
        module: () => import('../lessons/m6-geometria/identificar-formas.js')
      },
      {
        id: 'formas-naturaleza',
        name: 'Formas en la Naturaleza',
        emoji: '🌿',
        cnb: '1.4.1',
        module: () => import('../lessons/m6-geometria/formas-naturaleza.js')
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
    description: 'Aprende a medir el tiempo con el reloj',
    totalLessons: 3,
    cnb: 'Geometría y Medición - Tiempo y longitud',
    lessons: [
      {
        id: 'reloj-interactivo',
        name: 'El Reloj del Pueblo',
        emoji: '🕐',
        cnb: '7.2.1',
        module: () => import('../lessons/m7-medicion/reloj-interactivo.js')
      },
      {
        id: 'dias-semana',
        name: 'Días de la Semana',
        emoji: '📅',
        cnb: '7.3.1',
        module: () => import('../lessons/m7-medicion/dias-semana.js')
      },
      {
        id: 'mas-alto-bajo',
        name: 'Más Alto o Más Bajo',
        emoji: '📏',
        cnb: '1.1.3',
        module: () => import('../lessons/m7-medicion/mas-alto-bajo.js')
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
