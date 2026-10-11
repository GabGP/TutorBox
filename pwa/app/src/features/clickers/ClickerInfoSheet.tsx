import React from 'react';
import { Sheet } from '../../shared/ui/Sheet/Sheet';
import styles from './clickers.module.css';
import { formatClickerDate } from './clickerFormat';
import type { ClickerDevice } from './clickers.types';

export interface ClickerInfoSheetProps {
  /** The clicker to describe; null = closed. */
  device: ClickerDevice | null;
  onClose: () => void;
}

interface InfoLineProps {
  label: string;
  value: string;
}

const InfoLine: React.FC<InfoLineProps> = ({ label, value }) => (
  <div className={styles.infoRow}>
    <dt className={styles.infoLabel}>{label}</dt>
    <dd className={styles.infoValue}>{value}</dd>
  </div>
);

/**
 * Read-only detail of one clicker: the student it holds, when it was added,
 * and when it was first set up over Bluetooth (Todavía no until then).
 */
export const ClickerInfoSheet: React.FC<ClickerInfoSheetProps> = ({ device, onClose }) => {
  if (!device) return null;
  return (
    <Sheet label={`Detalle clicker ${device.device_id}`} onClose={onClose}>
      <div className={styles.sheetTitle}>{device.device_id}</div>
      <dl className={styles.infoList}>
        <InfoLine label="Alumno" value={device.assigned_username ?? 'Sin alumno'} />
        <InfoLine label="Agregado" value={formatClickerDate(device.created_at)} />
        <InfoLine
          label="Configurado por Bluetooth"
          value={
            device.secret_issued_at == null
              ? 'Todavía no'
              : formatClickerDate(device.secret_issued_at)
          }
        />
      </dl>
    </Sheet>
  );
};
