export const SILENT_WAV =
  'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=';

let sharedPlayer: HTMLAudioElement | null = null;

/**
 * Returns a singleton instance of HTMLAudioElement for audio playback.
 *
 * @returns {HTMLAudioElement} The shared audio player instance.
 */
export function getAudioPlayer(): HTMLAudioElement {
  if (!sharedPlayer && typeof Audio !== 'undefined') {
    sharedPlayer = new Audio();
  }
  return sharedPlayer as HTMLAudioElement;
}

/**
 * Prime audio playback inside a user interaction (essential for mobile Safari).
 *
 * @param {HTMLAudioElement} [player=getAudioPlayer()] - Target audio player to unlock.
 * @returns {void}
 */
export function unlockAudio(player: HTMLAudioElement = getAudioPlayer()): void {
  if (!player) return;
  player.src = SILENT_WAV;
  player.play().catch(() => {});
}

/**
 * Safely pause audio, clean up source, and revoke blob URL.
 *
 * @param {HTMLAudioElement} [player=getAudioPlayer()] - Target audio player to stop.
 * @param {string | null} [blobUrl] - Optional blob URL to revoke.
 * @returns {void}
 */
export function stopAudio(
  player: HTMLAudioElement = getAudioPlayer(),
  blobUrl?: string | null
): void {
  if (!player) return;
  player.pause();
  player.removeAttribute('src');
  try {
    player.load();
  } catch {
    // Ignore in headless/jsdom testing environments
  }
  if (blobUrl && blobUrl.startsWith('blob:')) {
    try {
      URL.revokeObjectURL(blobUrl);
    } catch {
      // Ignore revoke errors
    }
  }
}
