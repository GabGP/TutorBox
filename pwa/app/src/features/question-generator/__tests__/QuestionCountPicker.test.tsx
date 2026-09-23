import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { QuestionCountPicker } from '../QuestionCountPicker';

describe('QuestionCountPicker error toast', () => {
  it('floats generation errors as error toasts without shifting layout', () => {
    render(
      <QuestionCountPicker
        count={5}
        topicLabel="Aritmética"
        onChangeCount={vi.fn()}
        errorNote="El modelo no respondió"
      />
    );
    expect(screen.getByRole('alert')).toHaveTextContent(
      'El modelo no respondió'
    );
    expect(document.getElementById('countNote')).toBeNull();
  });

  it('renders no toast without an error note', () => {
    render(
      <QuestionCountPicker
        count={5}
        topicLabel="Aritmética"
        onChangeCount={vi.fn()}
        errorNote={null}
      />
    );
    expect(screen.queryByTestId('toast-viewport')).not.toBeInTheDocument();
  });
});
