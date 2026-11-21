import { formatSecondsEs } from '../../shared/lib/format';
import type { ToastPush } from '../../shared/ui/Toast/toast.types';
import type { ModelResidency, ResidencyDirection } from './residency.types';

/** Spanish copy for one model's toasts. */
export interface ResidencyCopy {
  loaded: (seconds: string) => string;
  /** Loaded, but only `percent` % fits on the GPU: the rest runs on the CPU, slowly. */
  partialGpu: (seconds: string, percent: number) => string;
  unloaded: string;
  loadFailed: string;
  unloadFailed: string;
}

/** Where a hook floats its toasts: the teacher view's toast queue. */
export interface NoticeSink {
  pushToast: (toast: ToastPush) => string;
  dismissToast: (id: string) => void;
}

/** Used when a caller passes no sink: the notices are dropped, the work still happens. */
export const NO_NOTICES: NoticeSink = {
  pushToast: () => '',
  dismissToast: () => undefined,
};

function warning(message: string): ToastPush {
  return { message, tone: 'warn' };
}

/**
 * The toast for one load or unload. A null result means the request itself failed, which reads
 * like a failed residency. A load that did not fit entirely on the GPU warns: the model works,
 * but slowly, because the Jetson had too little free memory. 'kept', 'unsupported' and 'disabled' say nothing: the teacher does
 * not need to know that the model was left alone or that the server does not manage it.
 *
 * @param {ModelResidency | null} result - The backend answer, or null when the request failed.
 * @param {ResidencyDirection} direction - Whether this was a load or an unload.
 * @param {ResidencyCopy} copy - Spanish wording for this model.
 * @returns {ToastPush | null} The toast to show, or null for no toast.
 */
export function residencyNotice(
  result: ModelResidency | null,
  direction: ResidencyDirection,
  copy: ResidencyCopy
): ToastPush | null {
  const failure = direction === 'load' ? copy.loadFailed : copy.unloadFailed;
  if (result === null) return warning(failure);
  switch (result.action) {
    case 'loaded': {
      const seconds = formatSecondsEs(result.duration_ms ?? 0);
      const gpuPercent = result.gpu_percent;
      if (typeof gpuPercent === 'number' && gpuPercent < 100) {
        return warning(copy.partialGpu(seconds, gpuPercent));
      }
      return { message: copy.loaded(seconds), tone: 'success' };
    }
    case 'unloaded':
      return { message: copy.unloaded, tone: 'success' };
    case 'failed':
      return warning(failure);
    default:
      return null;
  }
}
