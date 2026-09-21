/**
 * Canonical role labels. Replaces ROLE_LABELS copies in RosterTable/UserEditSheet
 * and the ad-hoc ternaries in AccountCard/TelemetryView.
 */
export const ROLE_LABELS: Record<string, string> = {
  student: 'Alumno',
  teacher: 'Docente',
  admin: 'Admin',
};

/** Resolves a role slug to its Spanish label, falling back to the raw value. */
export function getRoleLabel(role?: string | null): string {
  if (!role) return '';
  return ROLE_LABELS[role] || role;
}
