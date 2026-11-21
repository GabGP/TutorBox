import type { MemoryReleaseReport, SystemHealthSnapshot } from '../systemHealth.types';

/** A board that reads everything, with the values of the Jetson on 2026-11-21. */
export const FULL_SNAPSHOT: SystemHealthSnapshot = {
  sampled_at: new Date().toISOString(),
  cpu: {
    usage_percent: 36,
    status: 'ok',
    per_core: [
      { index: 0, usage_percent: 35, freq_mhz: 1190 },
      { index: 1, usage_percent: 20, freq_mhz: 1344 },
    ],
  },
  memory: {
    total_mb: 7485.4,
    available_mb: 3385.7,
    used_percent: 54.8,
    swap_total_mb: 0,
    swap_used_mb: 0,
    status: 'ok',
  },
  gpu: { load_percent: 99.8, freq_mhz: 306, max_freq_mhz: 918, status: 'ok' },
  temperatures: [
    { zone: 'cpu-thermal', celsius: 59.1, status: 'ok' },
    { zone: 'gpu-thermal', celsius: 82.4, status: 'warn' },
  ],
  power: [
    { rail: 'VDD_IN', milliwatts: 5981 },
    { rail: 'VDD_SOC', milliwatts: 1115 },
  ],
  disk: { total_gb: 914.3, free_gb: 821, free_percent: 89.8, status: 'ok' },
  uptime_seconds: 98992.6,
  load_average: [3.32, 4.45, 3.74],
  models: [{ name: 'qwen2.5:3b', gpu_percent: 100 }],
  voices: ['piper'],
};

/** A machine where almost nothing could be read: every metric is missing. */
export const EMPTY_SNAPSHOT: SystemHealthSnapshot = {
  sampled_at: new Date().toISOString(),
  cpu: { usage_percent: null, per_core: [], status: 'unknown' },
  memory: null,
  gpu: null,
  temperatures: [],
  power: [],
  disk: null,
  uptime_seconds: null,
  load_average: null,
  models: [],
  voices: [],
};

/** A release that freed 2.3 GB, unloaded the quiz model and a voice, and loaded the tutor back. */
export const RELEASE_REPORT: MemoryReleaseReport = {
  available_before_mb: 1000,
  available_after_mb: 3355.2,
  freed_mb: 2355.2,
  actions: [
    { target: 'qwen2.5:3b', kind: 'quiz_model', action: 'unloaded', detail: null },
    { target: 'voz qwen3-tts', kind: 'voice', action: 'unloaded', detail: null },
    { target: 'hf.co/tutor', kind: 'tutor_model', action: 'loaded', detail: null },
    { target: 'heap del proceso', kind: 'backend_heap', action: 'unloaded', detail: null },
  ],
};
