import type { LucideIcon } from 'lucide-react';

/**
 * Canonical curriculum taxonomy labels. Moved out of
 * `features/question-generator/TopicSelector.tsx` so question-bank,
 * telemetry and teacher layers can share without depending on a feature.
 */

export const TOPIC_METADATA: Record<string, { label: string; iconName: string }> = {
  '': { label: 'Todos los temas', iconName: 'LayoutGrid' },
  arithmetic: { label: 'Aritmética', iconName: 'Plus' },
  decimals_percentages: { label: 'Decimales y porcentajes', iconName: 'Percent' },
  fractions: { label: 'Fracciones', iconName: 'Divide' },
  pre_algebra: { label: 'Pre-álgebra', iconName: 'Variable' },
};

export const TOPIC_LABELS: Record<string, string> = Object.fromEntries(
  Object.entries(TOPIC_METADATA).map(([key, meta]) => [key, meta.label]),
);

const SUBCONCEPT_LABELS: Record<string, string> = {
  addition_subtraction: 'Suma y resta',
  multiplication_division: 'Multiplicación y división',
  order_of_operations: 'Jerarquía de operaciones',
  simplification: 'Simplificación',
  one_step_equations: 'Ecuaciones de 1 paso',
  two_step_equations: 'Ecuaciones de 2 pasos',
  decimal_operations: 'Operaciones con decimales',
  percentages: 'Porcentajes',
};

const MISCONCEPTION_LABELS: Record<string, string> = {
  sign_error: 'Error de signo',
  borrowing_error: 'Error al pedir prestado',
  alignment_error: 'Error de alineación',
  added_instead_of_subtracted: 'Sumó en vez de restar',
  table_lookup_error: 'Error en las tablas de multiplicar',
  remainder_ignored: 'Ignoró el resto',
  inverted_division: 'División invertida',
  forgot_carry: 'Olvidó la llevada',
  left_to_right_precedence: 'Operó de izquierda a derecha sin jerarquía',
  addition_before_multiplication: 'Sumó antes de multiplicar',
  ignored_parentheses: 'Ignoró los paréntesis',
  added_denominators: 'Sumó los denominadores',
  ignored_common_denominator: 'Ignoró el común denominador',
  subtracted_denominators: 'Restó los denominadores',
  cross_multiplied_for_product: 'Multiplicó en cruz para el producto',
  forgot_to_invert_divisor: 'Olvidó invertir el divisor',
  multiplied_only_numerators: 'Multiplicó solo los numeradores',
  divided_only_numerator: 'Dividió solo el numerador',
  subtracted_to_reduce: 'Restó para simplificar',
  partial_factor_division: 'Dividió solo parte de los factores',
  sign_flip_error: 'Error al cambiar el signo',
  wrong_inverse_operation: 'Operación inversa equivocada',
  applied_op_to_one_side_only: 'Operó en un solo lado',
  divided_before_subtracting: 'Dividió antes de restar',
  forgot_division: 'Olvidó dividir',
  subtracted_instead_of_divided: 'Restó en vez de dividir',
  sign_inversion_error: 'Error de inversión de signo',
  misplaced_decimal_point: 'Punto decimal mal colocado',
  ignored_decimal_places: 'Ignoró los decimales',
  added_without_aligning_decimal: 'Sumó sin alinear el punto decimal',
  multiplied_by_percentage_directly: 'Multiplicó por el porcentaje directamente',
  confused_fraction_with_percent: 'Confundió fracción con porcentaje',
  subtracted_percentage_as_raw_number: 'Restó el porcentaje como número',
};

/** Resolves a topic slug to its Spanish display label. */
export function getTopicLabel(topicName: string): string {
  return TOPIC_METADATA[topicName]?.label || topicName || 'Todos los temas';
}

/** Resolves a subconcept slug to its Spanish display label. */
export function getSubconceptLabel(subconceptName?: string | null): string {
  if (!subconceptName) return '';
  return SUBCONCEPT_LABELS[subconceptName] || subconceptName;
}

/** Resolves a misconception slug to its Spanish label, falling back to the raw slug. */
export function getMisconceptionLabel(slug?: string | null): string {
  if (!slug) return '';
  return MISCONCEPTION_LABELS[slug] || slug;
}

/** Maps iconName keys to lucide icons. Kept beside labels to avoid feature coupling. */
export async function resolveTopicIcon(iconName: string): Promise<LucideIcon | null> {
  const icons = await import('lucide-react');
  const table: Record<string, LucideIcon> = {
    LayoutGrid: icons.LayoutGrid,
    Plus: icons.Plus,
    Percent: icons.Percent,
    Divide: icons.Divide,
    Variable: icons.Variable,
    CircleHelp: icons.CircleHelp,
  };
  return table[iconName] ?? null;
}
