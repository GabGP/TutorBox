/**
 * Canonical press-and-hold durations for TutorBox HoldButton.
 *
 * Three tiers only — pick by consequence, never invent a new number:
 * - SHORT (800ms): reversible / low-risk guards (PIN change, PIN reset).
 * - MEDIUM (1200ms): session- or round-affecting (Terminar la pregunta).
 * - LONG (2000ms): destructive or session-ending (delete question,
 *   delete account, self-rename that revokes the session).
 */
export const HOLD_SHORT_MS = 800;

export const HOLD_MEDIUM_MS = 1200;

export const HOLD_LONG_MS = 2000;
