import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { RemediationAlert } from '../RemediationAlert';

describe('RemediationAlert Component', () => {
  const defaultProps = {
    shouldShow: true,
    dominantCount: 8,
    totalVotes: 10,
    dominantPercentage: 80,
    dominantOptionText: '84 (Error de acarreo)',
    explanation: 'Al sumar 38 + 46, recuerden llevar 1 a las decenas.',
    speechState: 'idle' as const,
    voiceLang: 'es' as const,
    onPlay: vi.fn(),
    onSkip: vi.fn(),
  };

  it('renders nothing when shouldShow is false', () => {
    const { container } = render(<RemediationAlert {...defaultProps} shouldShow={false} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders distractor statistics, explanation, and action buttons', () => {
    render(<RemediationAlert {...defaultProps} />);

    expect(screen.getByText(/Error conceptual mayoritario/)).toBeInTheDocument();
    expect(screen.getByText('8 de 10 (80%) eligieron 84 (Error de acarreo)')).toBeInTheDocument();
    expect(screen.getByText('Al sumar 38 + 46, recuerden llevar 1 a las decenas.')).toBeInTheDocument();
    expect(screen.getByText('Escuchar en español')).toBeInTheDocument();
    expect(screen.getByText('Saltar')).toBeInTheDocument();
  });

  it('handles play and skip button clicks', () => {
    const onPlay = vi.fn();
    const onSkip = vi.fn();
    render(<RemediationAlert {...defaultProps} onPlay={onPlay} onSkip={onSkip} />);

    fireEvent.click(screen.getByText('Escuchar en español'));
    expect(onPlay).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByText('Saltar'));
    expect(onSkip).toHaveBeenCalledTimes(1);
  });

  it('renders inline spinner when loading and clicking primary button cancels', () => {
    const onSkip = vi.fn();
    render(<RemediationAlert {...defaultProps} speechState="loading" onSkip={onSkip} />);

    const playBtn = screen.getByText('Preparando la voz…').closest('button');
    expect(playBtn).toBeInTheDocument();
    expect(screen.getByText('Detener')).toBeInTheDocument();

    fireEvent.click(playBtn!);
    expect(onSkip).toHaveBeenCalledTimes(1);
  });

  it('renders inline audio wave when playing and clicking primary button stops playback', () => {
    const onSkip = vi.fn();
    render(<RemediationAlert {...defaultProps} speechState="playing" onSkip={onSkip} />);

    const playBtn = screen.getByText('Leyendo…').closest('button');
    expect(playBtn).toBeInTheDocument();
    expect(screen.getByText('Detener')).toBeInTheDocument();

    fireEvent.click(playBtn!);
    expect(onSkip).toHaveBeenCalledTimes(1);
  });
});
