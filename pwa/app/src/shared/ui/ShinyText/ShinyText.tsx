import React from 'react';
import styles from './ShinyText.module.css';

export interface ShinyTextProps {
  text: string;
  speed?: number;
  className?: string;
  as?: 'h1' | 'h2' | 'h3' | 'p' | 'span';
  id?: string;
}

/**
 * Text component with an animated shimmering gradient sweep.
 */
export const ShinyText: React.FC<ShinyTextProps> = ({
  text,
  speed = 5.5,
  className,
  as: Component = 'span',
  id,
}) => {
  return (
    <Component
      id={id}
      className={`${styles.shiny} ${className || ''}`.trim()}
      style={{ '--speed': `${speed}s` } as React.CSSProperties}
    >
      {text}
    </Component>
  );
};
