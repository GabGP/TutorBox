import React, { useEffect } from 'react';
import { Pagination } from '../Pagination/Pagination';

export interface PagerProps {
  id?: string;
  offset: number;
  pageSize: number;
  total: number;
  pageSizeOptions?: number[];
  disabled?: boolean;
  onOffsetChange: (offset: number) => void;
  onPageSizeChange: (size: number) => void;
}

/**
 * Offset pager shared by the Bank and Telemetry list shells: page/pages
 * derivation, clamped prev/next/first/last wiring, page-size reset, and the
 * clamp-on-shrink guard so filtering never strands on an empty page.
 */
export const Pager: React.FC<PagerProps> = ({
  id,
  offset,
  pageSize,
  total,
  pageSizeOptions,
  disabled = false,
  onOffsetChange,
  onPageSizeChange,
}) => {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const page = Math.floor(offset / pageSize) + 1;
  const last = (pages - 1) * pageSize;

  useEffect(() => {
    if (total > 0 && offset >= total) {
      onOffsetChange(Math.max(0, (Math.ceil(total / pageSize) - 1) * pageSize));
    }
  }, [total, offset, pageSize, onOffsetChange]);

  return (
    <Pagination
      id={id}
      page={page}
      pages={pages}
      pageSize={pageSize}
      pageSizeOptions={pageSizeOptions}
      onPrev={() => onOffsetChange(Math.max(0, offset - pageSize))}
      onNext={() => onOffsetChange(Math.min(last, offset + pageSize))}
      onFirst={() => onOffsetChange(0)}
      onLast={() => onOffsetChange(last)}
      onPageSizeChange={(size) => {
        onPageSizeChange(size);
        onOffsetChange(0);
      }}
      disabled={disabled}
    />
  );
};
