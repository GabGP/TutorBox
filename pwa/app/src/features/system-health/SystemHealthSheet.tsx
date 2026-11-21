import React from 'react';
import { Sheet } from '../../shared/ui/Sheet/Sheet';
import { SystemHealthView } from './SystemHealthView';

export interface SystemHealthSheetProps {
  onClose: () => void;
}

/**
 * The Jetson health panel in its own floating sheet, opened from the teacher header.
 * Mounted only while open, so closing it stops the samples.
 */
export const SystemHealthSheet: React.FC<SystemHealthSheetProps> = ({ onClose }) => (
  <Sheet label="Estado del Jetson" onClose={onClose}>
    <SystemHealthView />
  </Sheet>
);
