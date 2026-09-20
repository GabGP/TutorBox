import React from 'react';
import styles from './generator.module.css';
import { TopicModel } from './generator.types';

export interface TopicSelectorProps {
  topics: TopicModel[];
  selectedTopic: string;
  onSelectTopic: (topicName: string) => void;
}

const TOPIC_METADATA: Record<string, { label: string; glyph: string }> = {
  '': { label: 'Todos los temas', glyph: '∗' },
  arithmetic: { label: 'Aritmética', glyph: '+' },
  decimals_percentages: { label: 'Decimales y porcentajes', glyph: '%' },
  fractions: { label: 'Fracciones', glyph: '½' },
  pre_algebra: { label: 'Pre-álgebra', glyph: 'x' },
};

/**
 * Resolves human-readable Spanish display labels for math curriculum topics.
 *
 * @param {string} topicName - Internal taxonomy topic slug (e.g. "arithmetic", "fractions").
 * @returns {string} Friendly Spanish topic label.
 */
export function getTopicLabel(topicName: string): string {
  return TOPIC_METADATA[topicName]?.label || topicName || 'Todos los temas';
}

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

/**
 * Resolves human-readable Spanish display labels for curriculum subconcepts.
 *
 * @param {string | null | undefined} subconceptName - Internal taxonomy subconcept slug.
 * @returns {string} Friendly Spanish subconcept label.
 */
export function getSubconceptLabel(subconceptName?: string | null): string {
  if (!subconceptName) return '';
  return SUBCONCEPT_LABELS[subconceptName] || subconceptName;
}

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

/**
 * Resolves human-readable Spanish display labels for diagnosed
 * misconception slugs (e.g. "forgot_carry" → "Olvidó la llevada").
 * Falls back to the raw slug so edits never lose data.
 *
 * @param {string | null | undefined} slug - Internal misconception identifier.
 * @returns {string} Friendly Spanish misconception label.
 */
export function getMisconceptionLabel(slug?: string | null): string {
  if (!slug) return '';
  return MISCONCEPTION_LABELS[slug] || slug;
}

/**
 * Topic Selector grid component.
 * Allows teachers to select a pedagogical topic (or mixed topics) for quiz generation.
 *
 * @param {TopicSelectorProps} props - Component props containing available topics, selection state, and change callback.
 * @returns {JSX.Element} The rendered topic selection list.
 */
export const TopicSelector: React.FC<TopicSelectorProps> = ({
  topics,
  selectedTopic,
  onSelectTopic,
}) => {
  const options: TopicModel[] = [
    { name: '', subconcepts: [] },
    ...topics,
  ];

  return (
    <div className={styles.topics} id="topics">
      {options.map((t) => {
        const id = t.name;
        const label = t.label || getTopicLabel(id) || id || 'Todos los temas';
        const meta = TOPIC_METADATA[id] || { label, glyph: '?' };
        const isSelected = selectedTopic === id;
        const description = id
          ? 'Preguntas creadas por el modelo'
          : 'Mezcla de todos los temas';

        return (
          <button
            key={id}
            type="button"
            className={`${styles.topic} ${isSelected ? styles.on : ''}`}
            onClick={() => onSelectTopic(id)}
            data-id={id}
          >
            <span className={styles.glyph}>{meta.glyph}</span>
            <span style={{ flex: 1, minWidth: 0 }}>
              <div className={styles.l}>{meta.label}</div>
              <div className={styles.m}>{description}</div>
            </span>
            <span className={styles.tick}>{isSelected ? '✓' : ''}</span>
          </button>
        );
      })}
    </div>
  );
};
