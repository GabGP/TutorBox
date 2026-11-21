import React, { useState } from 'react';
import { toErrorMessage } from '../../shared/lib/errors';
import { ProgressBar } from '../../shared/ui/ProgressBar/ProgressBar';
import { Spinner } from '../../shared/ui/Spinner/Spinner';
import { ToastViewport } from '../../shared/ui/Toast/ToastViewport';
import { useErrorToast } from '../../shared/ui/Toast/useErrorToast';
import { useToastQueue } from '../../shared/ui/Toast/useToastQueue';
import { HealthCard } from './HealthCard';
import { SampleAge } from './SampleAge';
import { HEALTH_COPY } from './systemHealthCopy';
import { systemHealthApi } from './systemHealthApi';
import {
  formatCelsius,
  formatGigabytes,
  formatLoadAverage,
  formatMhz,
  formatPercent,
  formatUptime,
  formatWatts,
  worstStatus,
} from './systemHealthFormat';
import { summarizeRelease } from './releaseSummary';
import type { HealthStatus, SystemHealthSnapshot } from './systemHealth.types';
import { useSystemHealth } from './useSystemHealth';
import styles from './systemHealth.module.css';

const RELEASE_ERROR = 'No se pudo liberar la memoria. Inténtalo otra vez.';
const MB_PER_GB = 1024;

/** The rail that carries the whole board's input is the one to show as the total. */
function totalPower(snapshot: SystemHealthSnapshot): string {
  if (snapshot.power.length === 0) return '—';
  const input = snapshot.power.find((rail) => rail.rail === 'VDD_IN') ?? snapshot.power[0];
  return formatWatts(input.milliwatts);
}

function cardsOf(snapshot: SystemHealthSnapshot): React.ReactNode {
  const { cpu, memory, gpu, temperatures, power, disk, models, voices } = snapshot;
  const hottest = temperatures.length > 0 ? Math.max(...temperatures.map((zone) => zone.celsius)) : null;
  const temperatureStatus: HealthStatus = worstStatus(temperatures.map((zone) => zone.status));
  return (
    <>
      <HealthCard
        title="Procesador"
        status={cpu.status}
        value={`${formatPercent(cpu.usage_percent)} de uso`}
        barPercent={cpu.usage_percent}
        barLabel="Uso del procesador"
        explanation={HEALTH_COPY.cpu}
      >
        {cpu.per_core.map((core) => (
          <div key={core.index} className={styles.coreRow}>
            <span>Núcleo {core.index + 1}</span>
            {core.usage_percent === null ? (
              <span className={styles.muted}>—</span>
            ) : (
              <ProgressBar
                value={core.usage_percent}
                size="sm"
                animated={false}
                label={`Uso del núcleo ${core.index + 1}`}
              />
            )}
            <span className={styles.muted}>{formatMhz(core.freq_mhz)}</span>
          </div>
        ))}
        <div className={styles.muted}>Carga media (1, 5 y 15 min): {formatLoadAverage(snapshot.load_average)}</div>
        <div className={styles.muted}>Encendido hace {formatUptime(snapshot.uptime_seconds)}</div>
      </HealthCard>

      <HealthCard
        title="GPU"
        status={gpu?.status ?? 'unknown'}
        value={`${formatPercent(gpu?.load_percent ?? null)} de carga`}
        barPercent={gpu?.load_percent ?? null}
        barLabel="Carga de la GPU"
        explanation={HEALTH_COPY.gpu}
      >
        <div className={styles.muted}>
          Reloj: {formatMhz(gpu?.freq_mhz ?? null)} de {formatMhz(gpu?.max_freq_mhz ?? null)}
        </div>
      </HealthCard>

      <HealthCard
        title="Memoria"
        status={memory?.status ?? 'unknown'}
        value={memory ? `${formatGigabytes(memory.available_mb / MB_PER_GB)} libres` : '—'}
        barPercent={memory?.used_percent ?? null}
        barLabel="Memoria en uso"
        explanation={HEALTH_COPY.memory}
      >
        {memory && (
          <>
            <div className={styles.muted}>
              Total {formatGigabytes(memory.total_mb / MB_PER_GB)} · en uso {formatPercent(memory.used_percent)}
            </div>
            <div className={styles.muted}>
              {memory.swap_total_mb > 0
                ? `Intercambio: ${formatGigabytes(memory.swap_used_mb / MB_PER_GB)} de ${formatGigabytes(memory.swap_total_mb / MB_PER_GB)}`
                : 'Sin intercambio (swap)'}
            </div>
          </>
        )}
      </HealthCard>

      <HealthCard
        title="Temperaturas"
        status={temperatureStatus}
        value={hottest === null ? '—' : `${formatCelsius(hottest)} la más caliente`}
        explanation={HEALTH_COPY.temperatures}
      >
        {temperatures.map((zone) => (
          <div key={zone.zone} className={styles.row}>
            <span>{zone.zone}</span>
            <span className={`${styles.badge} ${styles[zone.status]}`}>{formatCelsius(zone.celsius)}</span>
          </div>
        ))}
      </HealthCard>

      <HealthCard title="Energía" value={`${totalPower(snapshot)} en total`} explanation={HEALTH_COPY.power}>
        {power.map((rail) => (
          <div key={rail.rail} className={styles.row}>
            <span>{rail.rail}</span>
            <span className={styles.muted}>{formatWatts(rail.milliwatts)}</span>
          </div>
        ))}
      </HealthCard>

      <HealthCard
        title="Disco"
        status={disk?.status ?? 'unknown'}
        value={disk ? `${formatGigabytes(disk.free_gb)} libres` : '—'}
        barPercent={disk ? 100 - disk.free_percent : null}
        barLabel="Disco en uso"
        explanation={HEALTH_COPY.disk}
      >
        {disk && (
          <div className={styles.muted}>
            Total {formatGigabytes(disk.total_gb)} · libre {formatPercent(disk.free_percent)}
          </div>
        )}
      </HealthCard>

      <HealthCard
        title="Modelos en memoria"
        value={models.length === 0 ? 'Ninguno' : `${models.length} cargado${models.length === 1 ? '' : 's'}`}
        explanation={HEALTH_COPY.models}
      >
        {models.map((model) => (
          <div key={model.name} className={styles.row}>
            <span className={styles.modelName}>{model.name}</span>
            <span className={styles.muted}>GPU {formatPercent(model.gpu_percent)}</span>
          </div>
        ))}
      </HealthCard>

      <HealthCard
        title="Voz cargada"
        value={voices.length === 0 ? 'Ninguna' : voices.join(', ')}
        explanation={HEALTH_COPY.voices}
      />
    </>
  );
}

/**
 * The health panel's contents: the readings, the release button and its toasts. It samples
 * only while it is mounted (see useSystemHealth), so the sheet's close stops the reads.
 */
export const SystemHealthView: React.FC = () => {
  const { snapshot, error, refresh } = useSystemHealth(true);
  const { toasts, pushToast, dismissToast } = useToastQueue();
  const [releasing, setReleasing] = useState(false);
  useErrorToast(error, pushToast);

  const releaseMemory = async () => {
    setReleasing(true);
    try {
      const report = await systemHealthApi.freeMemory();
      pushToast(summarizeRelease(report));
      refresh();
    } catch (err) {
      pushToast({ message: toErrorMessage(err, RELEASE_ERROR), tone: 'error' });
    } finally {
      setReleasing(false);
    }
  };

  return (
    <div className={styles.view}>
      <h2 className={styles.title}>Estado del Jetson</h2>
      {snapshot ? (
        <div className={styles.meta}>
          <SampleAge sampledAt={snapshot.sampled_at} />
        </div>
      ) : (
        <div className={styles.meta}>Leyendo el estado…</div>
      )}

      <div className={styles.releaseBox}>
        <p className={styles.explanation}>{HEALTH_COPY.release}</p>
        <button
          type="button"
          className={styles.releaseButton}
          onClick={() => void releaseMemory()}
          disabled={releasing}
        >
          {releasing && <Spinner label="Liberando memoria…" size={16} />}
          Liberar memoria
        </button>
      </div>

      {snapshot && <div className={styles.grid}>{cardsOf(snapshot)}</div>}
      <ToastViewport toasts={toasts} onDismiss={(id) => dismissToast(id)} />
    </div>
  );
};
