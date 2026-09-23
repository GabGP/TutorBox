import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { SpeechStatusBadge } from '../SpeechStatusBadge';

describe('SpeechStatusBadge Component', () => {
  it('returns null when message is empty', () => {
    const { container } = render(<SpeechStatusBadge state="idle" message="" />);
    expect(container.firstChild).toBeNull();
  });

  it('renders loading state with spinner and message', () => {
    render(<SpeechStatusBadge state="loading" message="Preparando la voz..." />);
    expect(screen.getByText('Preparando la voz...')).toBeInTheDocument();
    const badge = document.getElementById('speechState');
    expect(badge).toBeInTheDocument();
    expect(badge?.className).toContain('loading');
  });

  it('renders playing state with on class and animated waves', () => {
    render(<SpeechStatusBadge state="playing" message="Leyendo..." id="voice-test" />);
    const badge = document.getElementById('voice-test');
    expect(badge).toBeInTheDocument();
    expect(badge?.className).toContain('on');
    expect(badge?.className).toContain('playing');
  });

  it('renders error state with bad class and message', () => {
    render(<SpeechStatusBadge state="error" message="Fallo de audio" />);
    const badge = document.getElementById('speechState');
    expect(badge?.className).toContain('bad');
    expect(badge?.className).toContain('error');
    expect(screen.getByText('Fallo de audio')).toBeInTheDocument();
  });
});
