import React, { useState } from 'react';
import formStyles from '../../shared/styles/forms.module.css';
import utils from '../../shared/styles/utils.module.css';
import { Sheet } from '../../shared/ui/Sheet/Sheet';
import type { RosterStudent } from '../roster/roster.types';
import { buildStudentOptions, studentKey } from './clickerStudentOptions';
import styles from './clickers.module.css';
import type { ClickerDevice } from './clickers.types';

export interface ClickerEditSheetProps {
  /** The clicker being edited; null = closed. */
  device: ClickerDevice | null;
  /** The live clicker list, so the picker shows who holds which clicker. */
  devices: ClickerDevice[];
  students: RosterStudent[];
  onClose: () => void;
  /** Resolves when the student is assigned; rejects after the parent toasted. */
  onAssign: (deviceId: string, student: RosterStudent) => Promise<unknown>;
  /** Resolves when the student is taken off; rejects after the parent toasted. */
  onUnassign: (deviceId: string) => Promise<unknown>;
}

type ClickerEditFormProps = Omit<ClickerEditSheetProps, 'device'> & { device: ClickerDevice };

/**
 * The picker and its actions for one open clicker. Mounted per opening (keyed
 * by device id), so the choice always starts from the clicker's current student.
 * A failed action keeps the sheet open; the parent's toast says why.
 */
const ClickerEditForm: React.FC<ClickerEditFormProps> = ({
  device,
  devices,
  students,
  onClose,
  onAssign,
  onUnassign,
}) => {
  const currentStudentId = device.assigned_user_id === null ? '' : String(device.assigned_user_id);
  const [choice, setChoice] = useState(currentStudentId);
  const [busy, setBusy] = useState(false);
  const options = buildStudentOptions(students, devices, device.assigned_user_id);
  const noStudents = students.length === 0;
  const chosenStudent = students.find((candidate) => studentKey(candidate) === choice);
  // Enabled only when a click will send an assign request.
  const canAssign = chosenStudent !== undefined && choice !== currentStudentId && !busy;

  /** Runs one action; the sheet closes only when it succeeds. */
  const runAction = async (action: () => Promise<unknown>) => {
    setBusy(true);
    try {
      await action();
      onClose();
    } catch {
      // The parent hook already showed the error toast; stay open.
    } finally {
      setBusy(false);
    }
  };

  const handleAssign = () => {
    if (chosenStudent) void runAction(() => onAssign(device.device_id, chosenStudent));
  };

  return (
    <Sheet label={`Editar clicker ${device.device_id}`} onClose={onClose}>
      <div className={styles.sheetTitle}>{device.device_id}</div>
      <select
        className={`${formStyles.addInput} ${utils.stretch}`}
        aria-label="Alumno del clicker"
        value={choice}
        onChange={(event) => setChoice(event.target.value)}
        disabled={noStudents || busy}
      >
        <option value="" disabled>
          Elija un alumno
        </option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {noStudents && <div className={styles.sheetHint}>No hay alumnos registrados.</div>}
      <button type="button" className={styles.sheetAction} onClick={handleAssign} disabled={!canAssign}>
        Asignar
      </button>
      {device.assigned_user_id !== null && (
        <button
          type="button"
          className={styles.sheetAction}
          onClick={() => void runAction(() => onUnassign(device.device_id))}
          disabled={busy}
        >
          Quitar alumno
        </button>
      )}
      <div className={styles.sheetHint}>
        El clicker vota como el alumno elegido. Cambiarlo no necesita Bluetooth.
      </div>
    </Sheet>
  );
};

/**
 * Edit card for one clicker: pick a student to assign it to, or take the
 * student off. Delete is not offered here; it is the row's swipe action.
 */
export const ClickerEditSheet: React.FC<ClickerEditSheetProps> = ({ device, ...rest }) => {
  if (!device) return null;
  return <ClickerEditForm key={device.device_id} device={device} {...rest} />;
};
