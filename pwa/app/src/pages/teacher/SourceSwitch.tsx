import { Library, Zap } from 'lucide-react';
import {
  SegmentedSwitch,
  type SwitchOption,
} from '../../shared/ui/SegmentedSwitch/SegmentedSwitch';

export type QuestionSource = 'generate' | 'bank';

export type { SwitchOption };
export { SegmentedSwitch as SourceSwitch };
export type { SegmentedSwitchProps as SourceSwitchProps } from '../../shared/ui/SegmentedSwitch/SegmentedSwitch';

export const QUESTION_SOURCE_OPTIONS: SwitchOption<QuestionSource>[] = [
  { value: 'generate', icon: Zap, label: 'Generar' },
  { value: 'bank', icon: Library, label: 'Banco' },
];
