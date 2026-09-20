import React from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import styles from './Pagination.module.css';

export interface PaginationProps {
  page: number;
  pages: number;
  pageSize: number;
  pageSizeOptions?: number[];
  onPrev: () => void;
  onNext: () => void;
  onFirst?: () => void;
  onLast?: () => void;
  onPageSizeChange?: (size: number) => void;
  disabled?: boolean;
  id?: string;
}

/**
 * Generic icons-only pagination (shadcn `pagination` icons-only variant,
 * hand-rolled, no table dep). Prev/next (+ optional first/last) icon
 * buttons with a `page/pages` label and a rows-per-page selector.
 */
export const Pagination: React.FC<PaginationProps> = ({
  page,
  pages,
  pageSize,
  pageSizeOptions = [5, 10, 20, 50],
  onPrev,
  onNext,
  onFirst,
  onLast,
  onPageSizeChange,
  disabled = false,
  id,
}) => {
  const prevDisabled = disabled || page <= 1;
  const nextDisabled = disabled || page >= pages;
  return (
    <div className={styles.bar} id={id} role="navigation" aria-label="Paginación">
      <label className={styles.sizeWrap}>
        <span className={styles.sizeLabel}>Filas</span>
        <select
          className={styles.sizeSelect}
          aria-label="Filas por página"
          value={pageSize}
          disabled={disabled || !onPageSizeChange}
          onChange={(e) => onPageSizeChange?.(Number(e.target.value))}
        >
          {pageSizeOptions.map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </label>
      <span className={styles.pageLabel} aria-live="polite">
        {page}/{pages}
      </span>
      <div className={styles.buttons}>
        {onFirst && (
          <button
            type="button"
            className={styles.iconBtn}
            aria-label="Primera página"
            disabled={prevDisabled}
            onClick={onFirst}
          >
            <ChevronsLeft size={18} aria-hidden />
          </button>
        )}
        <button
          type="button"
          className={styles.iconBtn}
          aria-label="Anterior"
          disabled={prevDisabled}
          onClick={onPrev}
        >
          <ChevronLeft size={18} aria-hidden />
        </button>
        <button
          type="button"
          className={styles.iconBtn}
          aria-label="Siguiente"
          disabled={nextDisabled}
          onClick={onNext}
        >
          <ChevronRight size={18} aria-hidden />
        </button>
        {onLast && (
          <button
            type="button"
            className={styles.iconBtn}
            aria-label="Última página"
            disabled={nextDisabled}
            onClick={onLast}
          >
            <ChevronsRight size={18} aria-hidden />
          </button>
        )}
      </div>
    </div>
  );
};
