import type { RosterStudent } from '../roster/roster.types';
import type { ClickerDevice } from './clickers.types';

export interface ClickerStudentOption {
  /** Student id, as the select sends it. */
  value: string;
  label: string;
}

/**
 * The select's value for a student. The server sends numeric ids while the
 * roster type says string, so every comparison goes through this string form.
 * Numeric comparisons (assigned_user_id) use Number(student.id) instead.
 */
export function studentKey(student: RosterStudent): string {
  return String(student.id);
}

/**
 * Options for the student picker of one clicker. Students who hold no clicker
 * come first, then students who hold one, labelled with that clicker.
 * Both groups are alphabetical. The clicker's own student is listed plainly
 * among the holders, because that is the choice already in place.
 *
 * @param {RosterStudent[]} students - Every student account.
 * @param {ClickerDevice[]} devices - The live clicker list (who holds what).
 * @param {number | null} ownerUserId - The student this clicker holds now, if any.
 * @returns {ClickerStudentOption[]} Options in display order.
 */
export function buildStudentOptions(
  students: RosterStudent[],
  devices: ClickerDevice[],
  ownerUserId: number | null
): ClickerStudentOption[] {
  const clickerByStudent = new Map<number, string>();
  for (const device of devices) {
    if (device.assigned_user_id !== null) {
      clickerByStudent.set(device.assigned_user_id, device.device_id);
    }
  }
  const byUsername = (a: RosterStudent, b: RosterStudent) =>
    a.username.localeCompare(b.username, 'es');
  const holdsClicker = (student: RosterStudent) => clickerByStudent.has(Number(student.id));

  const free = students.filter((student) => !holdsClicker(student)).sort(byUsername);
  const holders = students.filter(holdsClicker).sort(byUsername);

  return [
    ...free.map((student) => ({ value: studentKey(student), label: student.username })),
    ...holders.map((student) => {
      const isOwner = Number(student.id) === ownerUserId;
      const heldClicker = clickerByStudent.get(Number(student.id));
      return {
        value: studentKey(student),
        label: isOwner ? student.username : `${student.username} (tiene ${heldClicker})`,
      };
    }),
  ];
}
