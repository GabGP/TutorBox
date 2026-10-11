import React from 'react';
import { Sheet } from '../../shared/ui/Sheet/Sheet';
import { ClickerFleetView } from './ClickerFleetView';

export interface ClickerFleetSheetProps {
  onClose: () => void;
}

/**
 * The clicker fleet in its own floating sheet, opened from the teacher
 * header (not from the settings accordion).
 */
export const ClickerFleetSheet: React.FC<ClickerFleetSheetProps> = ({ onClose }) => (
  <Sheet label="Clickers" onClose={onClose}>
    <ClickerFleetView />
  </Sheet>
);
