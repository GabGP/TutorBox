import { formatGigabytes } from './systemHealthFormat';
import type { MemoryReleaseReport, ReleaseAction } from './systemHealth.types';

export interface ReleaseSummary {
  message: string;
  description?: string;
  tone: 'success' | 'warn';
}

const ENGINE_LABELS: Record<string, string> = {
  'qwen3-tts': 'Qwen3-TTS',
  piper: 'Piper',
  espeak: 'eSpeak NG',
  sherpa: 'Sherpa',
  kokoro: 'Kokoro',
  mms: 'MMS',
};

const KIND_LABELS: Record<ReleaseAction['kind'], string> = {
  quiz_model: 'modelo de preguntas',
  tutor_model: 'modelo del tutor',
  voice: 'voz',
  backend_heap: 'memoria del servidor',
};

/** A voice target arrives as "voz <engine>"; any other target (e.g. "voces") is shown as it is. */
function labelOf(action: ReleaseAction): string {
  if (action.kind !== 'voice' || !action.target.startsWith('voz ')) {
    return action.kind === 'voice' ? action.target : KIND_LABELS[action.kind];
  }
  const engine = action.target.slice('voz '.length);
  return `voz ${ENGINE_LABELS[engine] ?? engine}`;
}

function listOf(actions: ReleaseAction[], result: ReleaseAction['action']): string[] {
  return actions.filter((action) => action.action === result).map(labelOf);
}

/**
 * The toast after a release, in Spanish: the RAM won back, what was unloaded, what was
 * loaded again, what was kept, and what failed (the only case that turns the toast warn).
 */
export function summarizeRelease(report: MemoryReleaseReport): ReleaseSummary {
  const { actions, freed_mb: freedMb } = report;
  const unloaded = listOf(
    actions.filter((action) => action.kind !== 'backend_heap'),
    'unloaded'
  );
  const reloaded = listOf(actions, 'loaded');
  const kept = listOf(actions, 'kept');
  const failed = listOf(actions, 'failed');

  const sentences: string[] = [];
  if (freedMb !== null && freedMb > 0) {
    sentences.push(`Memoria liberada: ${formatGigabytes(freedMb / 1024)}`);
  } else if (freedMb !== null) {
    sentences.push('No hubo memoria nueva que liberar');
  } else {
    sentences.push('Liberación terminada');
  }
  if (unloaded.length > 0) sentences.push(`Descargado: ${unloaded.join(', ')}`);
  if (reloaded.length > 0) sentences.push(`Recargado: ${reloaded.join(', ')}`);
  if (kept.length > 0) sentences.push(`Se mantiene: ${kept.join(', ')}`);

  const summary: ReleaseSummary = {
    message: `${sentences.join('. ')}.`,
    tone: failed.length > 0 ? 'warn' : 'success',
  };
  if (failed.length > 0) summary.description = `No se pudo: ${failed.join(', ')}.`;
  return summary;
}
