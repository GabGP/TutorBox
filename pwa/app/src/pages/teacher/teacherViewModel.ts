import type { SessionModel } from '../../features/session-engine/session.types';
import {
  getPrimaryActionLabel,
  SECONDARY_ACTION_LABELS,
  TEACHER_STEP_TITLES,
  type TeacherStep,
} from './teacherViewConfig';

export interface TeacherViewModelInput {
  session: SessionModel | null;
  wizard: string;
  bankIds: string[];
  isGenerating: boolean;
  roundClosed: boolean;
  isLast: boolean;
}

export interface TeacherViewModel {
  step: string;
  title: string;
  subtitle: string;
  primaryText: string;
  secondaryText: string | undefined;
  /** Cancelar mid-game ends the match for the whole class, so it is a press-and-hold. */
  isSecondaryHold: boolean;
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
 * The count step is the bank pick: the game starts from the chosen questions,
 * and not while the Generar tab is still adding to them.
 */
export function getTeacherViewModel(input: TeacherViewModelInput): TeacherViewModel {
  const { session, wizard, bankIds, isGenerating, roundClosed, isLast } = input;
  const step = getTeacherStep(session, wizard);
  const key = step as TeacherStep;
  const [subtitle, title] = TEACHER_STEP_TITLES[key] ?? ["Utz'tutor", 'Panel'];
  const isBankStep = step === 'count';
  const isBankEmpty = isBankStep && bankIds.length === 0;
  const primaryText = isBankStep
    ? bankIds.length > 0
      ? `Jugar con ${bankIds.length}`
      : 'Elige preguntas del banco'
    : getPrimaryActionLabel(step, roundClosed, isLast);
  return {
    step,
    title,
    subtitle,
    primaryText,
    secondaryText: SECONDARY_ACTION_LABELS[key],
    isSecondaryHold: step === 'question' || step === 'reveal',
    wizardIdx: ['topic', 'count', 'lobby'].indexOf(step),
    isBankEmpty,
    isPrimaryDisabled: isBankEmpty || (isBankStep && isGenerating),
    isLobbySuccess: step === 'lobby',
  };
}
