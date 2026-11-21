import { describe, expect, it } from 'vitest';
import { summarizeRelease } from '../releaseSummary';
import type { MemoryReleaseReport } from '../systemHealth.types';
import { RELEASE_REPORT } from './systemHealthFixture';

const NOTHING: MemoryReleaseReport = {
  available_before_mb: 3000,
  available_after_mb: 3000,
  freed_mb: 0,
  actions: [],
};

describe('summarizeRelease', () => {
  it('says how much came back, what was unloaded and reloaded, in Spanish', () => {
    const summary = summarizeRelease(RELEASE_REPORT);

    expect(summary.message).toBe(
      'Memoria liberada: 2,3 GB. Descargado: modelo de preguntas, voz Qwen3-TTS. Recargado: modelo del tutor.'
    );
    expect(summary.tone).toBe('success');
    expect(summary.description).toBeUndefined();
  });

  it('names what was kept, and warns about what failed', () => {
    const summary = summarizeRelease({
      ...NOTHING,
      freed_mb: 512,
      actions: [
        { target: 'qwen2.5:3b', kind: 'quiz_model', action: 'kept', detail: 'a question generation is running' },
        { target: 'voz piper', kind: 'voice', action: 'kept', detail: 'a quiz game is running' },
        { target: 'modelo', kind: 'tutor_model', action: 'failed', detail: 'Ollama is unreachable' },
        { target: 'voz espeak', kind: 'voice', action: 'failed', detail: 'busy' },
      ],
    });

    expect(summary.message).toBe(
      'Memoria liberada: 0,5 GB. Se mantiene: modelo de preguntas, voz Piper.'
    );
    expect(summary.tone).toBe('warn');
    expect(summary.description).toBe('No se pudo: modelo del tutor, voz eSpeak NG.');
  });

  it('says so when nothing new came back', () => {
    expect(summarizeRelease(NOTHING).message).toBe('No hubo memoria nueva que liberar.');
  });

  it('says the release finished when the memory could not be read', () => {
    const summary = summarizeRelease({ ...NOTHING, available_before_mb: null, freed_mb: null });

    expect(summary.message).toBe('Liberación terminada.');
  });

  it('shows an unknown voice engine as it is, and a voice list target without a prefix', () => {
    const summary = summarizeRelease({
      ...NOTHING,
      freed_mb: 1024,
      actions: [
        { target: 'voz nueva', kind: 'voice', action: 'unloaded', detail: null },
        { target: 'voces', kind: 'voice', action: 'failed', detail: 'registry broken' },
        { target: 'heap del proceso', kind: 'backend_heap', action: 'failed', detail: 'no libc' },
      ],
    });

    expect(summary.message).toBe('Memoria liberada: 1,0 GB. Descargado: voz nueva.');
    expect(summary.description).toBe('No se pudo: voces, memoria del servidor.');
  });
});
