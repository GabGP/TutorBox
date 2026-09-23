import React from 'react';
import { Check, CircleHelp, Divide, LayoutGrid, Percent, Plus, Variable, type LucideIcon } from 'lucide-react';
import styles from './generator.module.css';
import { TopicModel } from './generator.types';
import { getTopicLabel } from '../../shared/taxonomy/labels';
import utils from '../../shared/styles/utils.module.css';

export { getMisconceptionLabel, getSubconceptLabel, getTopicLabel } from '../../shared/taxonomy/labels';

export interface TopicSelectorProps {
  topics: TopicModel[];
  selectedTopic: string;
  onSelectTopic: (topicName: string) => void;
}

const TOPIC_ICONS: Record<string, LucideIcon> = {
  '': LayoutGrid,
  arithmetic: Plus,
  decimals_percentages: Percent,
  fractions: Divide,
  pre_algebra: Variable,
};

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
        const GlyphIcon = TOPIC_ICONS[id] || CircleHelp;
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
            <span className={styles.glyph}><GlyphIcon size={24} aria-hidden /></span>
            <span className={utils.grow}>
              <div className={styles.l}>{label}</div>
              <div className={styles.m}>{description}</div>
            </span>
            <span className={styles.tick}>{isSelected ? <Check size={22} aria-hidden /> : null}</span>
          </button>
        );
      })}
    </div>
  );
};
