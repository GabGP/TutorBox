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
  const options = [{ name: '' }, ...topics];

  return (
    <div className={styles.topics} id="topics">
      {options.map((t) => {
        const id = t.name;
        const meta = TOPIC_METADATA[id] || { label: id, glyph: '?' };
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
