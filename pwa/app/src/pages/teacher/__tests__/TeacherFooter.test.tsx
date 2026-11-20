import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { advanceHold, setupHoldTimers, teardownHoldTimers } from '../../../test/holdTimers';
import { TeacherFooter } from '../TeacherFooter';

const baseProps = {
  isPrimaryDisabled: false,
  isLobbySuccess: false,
  wizardIndex: 0,
  onPrimary: vi.fn(),
  onSecondary: vi.fn(),
};

describe('TeacherFooter primary guard', () => {
  it('keeps other labels single-tap', () => {
    const onPrimary = vi.fn();
    render(<TeacherFooter {...baseProps} primaryText="Siguiente pregunta" onPrimary={onPrimary} />);
    fireEvent.click(screen.getByRole('button', { name: 'Siguiente pregunta' }));
    expect(onPrimary).toHaveBeenCalledTimes(1);
  });

  it('guards Terminar la pregunta behind a 1200ms hold', () => {
    const onPrimary = vi.fn();
    setupHoldTimers();
    try {
      render(<TeacherFooter {...baseProps} primaryText="Terminar la pregunta" onPrimary={onPrimary} />);
      const holdBtn = screen.getByRole('button', { name: 'Terminar la pregunta' });
      fireEvent.click(holdBtn);
      expect(onPrimary).not.toHaveBeenCalled();
      fireEvent.pointerDown(holdBtn, { pointerId: 1 });
      advanceHold(1200);
      expect(onPrimary).toHaveBeenCalledTimes(1);
    } finally {
      teardownHoldTimers();
    }
  });
});

describe('TeacherFooter secondary guard', () => {
  it('keeps Cancelar in the lobby a single tap', () => {
    const onSecondary = vi.fn();
    render(
      <TeacherFooter {...baseProps} primaryText="Comenzar el juego" secondaryText="Cancelar" onSecondary={onSecondary} />
    );
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }));
    expect(onSecondary).toHaveBeenCalledTimes(1);
  });

  it('guards Cancelar during a started match behind a 2000ms hold', () => {
    const onSecondary = vi.fn();
    setupHoldTimers();
    try {
      render(
        <TeacherFooter
          {...baseProps}
          primaryText="Siguiente pregunta"
          secondaryText="Cancelar"
          isSecondaryHold
          onSecondary={onSecondary}
        />
      );
      const holdBtn = screen.getByRole('button', { name: 'Mantén para cancelar el juego' });
      fireEvent.click(holdBtn);
      expect(onSecondary).not.toHaveBeenCalled();
      fireEvent.pointerDown(holdBtn, { pointerId: 1 });
      advanceHold(1200);
      expect(onSecondary).not.toHaveBeenCalled();
      advanceHold(800);
      expect(onSecondary).toHaveBeenCalledTimes(1);
    } finally {
      teardownHoldTimers();
    }
  });
});
