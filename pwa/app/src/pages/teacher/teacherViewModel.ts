import type { SessionModel } from '../../features/session-engine/session.types';
import type { QuestionSource } from './useWizardSelection';
import {
  getPrimaryActionLabel,
  SECONDARY_ACTION_LABELS,
  TEACHER_STEP_TITLES,
  type TeacherStep,
} from './teacherViewConfig';

export interface TeacherViewModelInput {
  session: SessionModel | null;
  wizard: string;
  source: QuestionSource;
  bankIds: string[];
  isGenerating: boolean;
  roundClosed: boolean;
  isLast: boolean;
  hasSessionForLobby: boolean;
}

export interface TeacherViewModel {
  step: string;
  title: string;
  subtitle: string;
  primaryText: string;
  secondaryText: string | undefined;
  wizardIdx: number;
  isBankEmpty: boolean;
  isPrimaryDisabled: boolean;
  isLobbySuccess: boolean;
}

/** Derives the active teacher step from session status over the wizard. */
export function getTeacherStep(
  session: SessionModel | null,
  wizard: string
): string {
  if (!session) return wizard;
  if (session.status === 'active') {
    return session.current_round?.status === 'revealed' ? 'reveal' : 'question';
  }
  if (session.status === 'completed') return 'stats';
  return 'lobby';
}

/**
 * Pure derivation of every label and flag the teacher header/footer need.
 * Extracted from TeacherView so step logic is testable without rendering.
 */
export function getTeacherViewModel(input: TeacherViewModelInput): TeacherViewModel {
  const { session, wizard, source, bankIds, isGenerating, roundClosed, isLast } = input;
  const step = getTeacherStep(session, wizard);
  const key = step as TeacherStep;
  const [subtitle, title] = TEACHER_STEP_TITLES[key] ?? ['TutorBox', 'Panel'];
  const isBankSource = step === 'count' && source === 'bank';
  const isBankEmpty = isBankSource && bankIds.length === 0;
  const primaryText = isBankSource
    ? bankIds.length > 0
      ? `Jugar con ${bankIds.length}`
      : 'Elige preguntas del banco'
    : getPrimaryActionLabel(step, isGenerating, roundClosed, isLast);
  return {
    step,
    title,
    subtitle,
    primaryText,
    secondaryText: SECONDARY_ACTION_LABELS[key],
    wizardIdx: ['topic', 'count', 'lobby'].indexOf(step),
    isBankEmpty,
    isPrimaryDisabled:
      isGenerating || isBankEmpty || (step === 'lobby' && !input.hasSessionForLobby),
    isLobbySuccess: step === 'lobby' && input.hasSessionForLobby,
  };
}
