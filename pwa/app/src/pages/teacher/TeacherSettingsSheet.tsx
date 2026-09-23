import React from 'react';
import { Sheet } from '../../shared/ui/Sheet/Sheet';
import { SettingsView, type SettingsRosterBundle } from '../../features/settings/SettingsView';
import type { User } from '../../features/auth/auth.types';

export interface TeacherSettingsSheetProps {
  user: User;
  onProfileChanged: () => Promise<unknown>;
  onSessionInvalidated: () => Promise<unknown> | void;
  onClose: () => void;
  roster?: SettingsRosterBundle;
  staffEnabled?: boolean;
}

/**
 * Teacher settings overlay.
 * Renders the settings accordion inside the shared floating Sheet so the
 * underlying console page (header, workspace, footer) stays visible behind.
 */
export const TeacherSettingsSheet: React.FC<TeacherSettingsSheetProps> = ({
  user,
  onProfileChanged,
  onSessionInvalidated,
  onClose,
  roster,
  staffEnabled,
}) => {
  return (
    <Sheet label="Ajustes" onClose={onClose}>
      <SettingsView
        user={user}
        onProfileChanged={onProfileChanged}
        onSessionInvalidated={onSessionInvalidated}
        roster={roster}
        staffEnabled={staffEnabled}
      />
    </Sheet>
  );
};
