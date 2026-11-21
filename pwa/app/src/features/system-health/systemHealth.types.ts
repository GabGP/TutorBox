/** Status of one reading. It colours the card, and the word on the card says the same thing. */
export type HealthStatus = 'ok' | 'warn' | 'critical' | 'unknown';

export interface CoreReading {
  index: number;
  usage_percent: number | null;
  freq_mhz: number | null;
}

export interface CpuReading {
  usage_percent: number | null;
  per_core: CoreReading[];
  status: HealthStatus;
}

export interface MemoryReading {
  total_mb: number;
  available_mb: number;
  used_percent: number;
  swap_total_mb: number;
  swap_used_mb: number;
  status: HealthStatus;
}

export interface GpuReading {
  load_percent: number | null;
  freq_mhz: number | null;
  max_freq_mhz: number | null;
  status: HealthStatus;
}

export interface TemperatureReading {
  zone: string;
  celsius: number;
  status: HealthStatus;
}

export interface PowerReading {
  rail: string;
  milliwatts: number;
}

export interface DiskReading {
  total_gb: number;
  free_gb: number;
  free_percent: number;
  status: HealthStatus;
}

export interface ModelReading {
  name: string;
  gpu_percent: number | null;
}

/** One sample of the appliance (`GET /api/v1/system/health`). Unreadable metrics are null or empty. */
export interface SystemHealthSnapshot {
  sampled_at: string;
  cpu: CpuReading;
  memory: MemoryReading | null;
  gpu: GpuReading | null;
  temperatures: TemperatureReading[];
  power: PowerReading[];
  disk: DiskReading | null;
  uptime_seconds: number | null;
  load_average: number[] | null;
  models: ModelReading[];
  voices: string[];
}

export type ReleaseKind = 'quiz_model' | 'tutor_model' | 'voice' | 'backend_heap';

export type ReleaseResult = 'loaded' | 'unloaded' | 'kept' | 'failed' | 'disabled' | 'unsupported';

export interface ReleaseAction {
  target: string;
  kind: ReleaseKind;
  action: ReleaseResult;
  detail: string | null;
}

/** What `POST /api/v1/system/free-memory` did (`freed_mb` can be negative when others used RAM). */
export interface MemoryReleaseReport {
  available_before_mb: number | null;
  available_after_mb: number | null;
  freed_mb: number | null;
  actions: ReleaseAction[];
}
