import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { Pagination } from '../Pagination/Pagination';

describe('Pagination', () => {
  it('disables prev on first page and next on last', () => {
    const { rerender } = render(
      <Pagination page={1} pages={3} pageSize={10} onPrev={() => {}} onNext={() => {}} />
    );
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Siguiente' })).not.toBeDisabled();
    rerender(
      <Pagination page={3} pages={3} pageSize={10} onPrev={() => {}} onNext={() => {}} />
    );
    expect(screen.getByRole('button', { name: 'Siguiente' })).toBeDisabled();
  });

  it('offers a 5-row minimum page size', () => {
    render(
      <Pagination page={1} pages={2} pageSize={10} onPrev={() => {}} onNext={() => {}} />
    );
    const options = Array.from(
      screen.getByLabelText('Filas por página').querySelectorAll('option')
    ).map((o) => o.value);
    expect(options).toEqual(['5', '10', '20', '50']);
  });

  it('fires prev/next and page-size change', () => {
    const onPrev = vi.fn();
    const onNext = vi.fn();
    const onPageSizeChange = vi.fn();
    render(
      <Pagination
        page={2}
        pages={5}
        pageSize={10}
        onPrev={onPrev}
        onNext={onNext}
        onPageSizeChange={onPageSizeChange}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: 'Anterior' }));
    fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
    expect(onPrev).toHaveBeenCalledTimes(1);
    expect(onNext).toHaveBeenCalledTimes(1);
    fireEvent.change(screen.getByLabelText('Filas por página'), {
      target: { value: '20' },
    });
    expect(onPageSizeChange).toHaveBeenCalledWith(20);
  });

  it('shows page label and first/last when wired', () => {
    const onFirst = vi.fn();
    const onLast = vi.fn();
    render(
      <Pagination
        page={2}
        pages={4}
        pageSize={10}
        onPrev={() => {}}
        onNext={() => {}}
        onFirst={onFirst}
        onLast={onLast}
      />
    );
    expect(screen.getByText('2/4')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Primera página' }));
    fireEvent.click(screen.getByRole('button', { name: 'Última página' }));
    expect(onFirst).toHaveBeenCalledTimes(1);
    expect(onLast).toHaveBeenCalledTimes(1);
  });
});
