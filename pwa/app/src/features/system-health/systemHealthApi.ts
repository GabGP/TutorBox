import { requestApi } from '../../shared/api/httpClient';
import type { MemoryReleaseReport, SystemHealthSnapshot } from './systemHealth.types';

/** API client for the teacher's Jetson health panel (staff only). */
export const systemHealthApi = {
  /** One sample of CPU, GPU, memory, temperatures, power, disk and the models in memory. */
  getSnapshot: () => requestApi<SystemHealthSnapshot>('GET', '/system/health'),

  /** Unloads what the current mode does not need and reports what each step did. */
  freeMemory: () => requestApi<MemoryReleaseReport>('POST', '/system/free-memory'),
};
