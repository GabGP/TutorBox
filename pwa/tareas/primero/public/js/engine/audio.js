// Audio Engine - Web Audio API
// Marimba-like tones for Guatemalan educational context

class AudioEngine {
  constructor() {
    this.ctx = null;
    this.masterGain = null;
    this.volume = 0.7;
    this._muted = false;
    this._initialized = false;
    this._speechSynth = typeof speechSynthesis !== 'undefined' ? speechSynthesis : null;
    this._spanishVoice = null;
    this._voicesReady = false;
    this._initVoices();
  }

  _initVoices() {
    if (!this._speechSynth) return;

    const pickVoice = () => {
      const voices = this._speechSynth.getVoices();
      if (!voices.length) return;

      // Priority: es-GT → es-419 (Latin America) → es-US → es-ES → any es-*
      const priority = ['es-GT', 'es-419', 'es-US', 'es-MX', 'es-ES'];
      for (const lang of priority) {
        const v = voices.find(v => v.lang === lang);
        if (v) { this._spanishVoice = v; this._voicesReady = true; return; }
      }
      // Fallback: any Spanish voice
      const any = voices.find(v => v.lang.startsWith('es'));
      if (any) { this._spanishVoice = any; this._voicesReady = true; }
    };

    // Voices may already be available (Chrome desktop loads them sync)
    pickVoice();

    // On most browsers (especially Android) voices load async
    this._speechSynth.addEventListener('voiceschanged', () => pickVoice());
  }

  async init() {
    if (this._initialized) return;
    try {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.value = this.volume;
      this.masterGain.connect(this.ctx.destination);
      this._initialized = true;
    } catch (e) {
      console.warn('AudioEngine: Web Audio API not available', e);
    }
  }

  // Resume audio context (needed after user gesture)
  async resume() {
    if (this.ctx && this.ctx.state === 'suspended') {
      await this.ctx.resume();
    }
  }

  /**
   * Play a single tone
   * @param {number} freq - Frequency in Hz
   * @param {number} duration - Duration in seconds
   * @param {string} type - Oscillator type: sine, square, sawtooth, triangle
   * @param {number} startTime - When to start (ctx.currentTime offset)
   */
  playTone(freq, duration, type = 'sine', startTime = 0, volume = 1) {
    if (!this._initialized || this._muted || !this.ctx) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime + startTime);

      // Marimba-like envelope: quick attack, fast decay
      const t = this.ctx.currentTime + startTime;
      gain.gain.setValueAtTime(0, t);
      gain.gain.linearRampToValueAtTime(volume * 0.8, t + 0.01);
      gain.gain.exponentialRampToValueAtTime(0.001, t + duration);

      osc.start(t);
      osc.stop(t + duration + 0.05);
    } catch (e) {
      // Silent fail
    }
  }

  /**
   * Play success sound - ascending marimba-like tones
   */
  playSuccess() {
    if (!this._initialized || this._muted) return;
    const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
    notes.forEach((freq, i) => {
      this.playTone(freq, 0.25, 'sine', i * 0.12, 0.9);
      // Add harmonic for richer marimba sound
      this.playTone(freq * 2, 0.2, 'sine', i * 0.12, 0.3);
    });
  }

  /**
   * Play error sound - gentle descending tones
   */
  playError() {
    if (!this._initialized || this._muted) return;
    const notes = [392, 349.23]; // G4, F4
    notes.forEach((freq, i) => {
      this.playTone(freq, 0.35, 'triangle', i * 0.18, 0.5);
    });
  }

  /**
   * Play star sparkle sound
   */
  playStars() {
    if (!this._initialized || this._muted) return;
    const freqs = [1046.5, 1318.5, 1567.98, 2093];
    freqs.forEach((freq, i) => {
      this.playTone(freq, 0.18, 'sine', i * 0.08, 0.6);
      // Shimmer effect
      this.playTone(freq * 1.01, 0.18, 'sine', i * 0.08 + 0.01, 0.3);
    });
  }

  /**
   * Play a simple click/tap sound
   */
  playTap() {
    if (!this._initialized || this._muted) return;
    this.playTone(800, 0.08, 'sine', 0, 0.5);
  }

  /**
   * Play counting tone for each number
   */
  playCount(n) {
    if (!this._initialized || this._muted) return;
    const scale = [261.63, 293.66, 329.63, 349.23, 392, 440, 493.88, 523.25, 587.33];
    const freq = scale[Math.min(n - 1, scale.length - 1)] || 261.63;
    this.playTone(freq, 0.2, 'sine', 0, 0.8);
  }

  /**
   * Narrate text using Web Speech API
   * @param {string} text - Text to speak
   * @param {Object} opts - Options { rate, pitch, lang }
   */
  speak(text, opts = {}) {
    // Android app: WebView has no speechSynthesis, so MainActivity exposes the phone's own
    // offline text-to-speech as window.AndroidTTS.
    if (window.AndroidTTS) {
      if (!this._muted) window.AndroidTTS.speak(String(text), opts.rate || 0.85, opts.pitch || 1.1);
      return;
    }
    if (!this._speechSynth) return;
    this._speechSynth.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = opts.lang || 'es-GT';
    utterance.rate = opts.rate || 0.85;
    utterance.pitch = opts.pitch || 1.1;
    utterance.volume = this._muted ? 0 : this.volume;

    if (this._spanishVoice) {
      utterance.voice = this._spanishVoice;
    }

    this._speechSynth.speak(utterance);
  }

  /**
   * Play a victory jingle
   */
  playVictory() {
    if (!this._initialized || this._muted) return;
    // Short fanfare
    const melody = [
      [523.25, 0.1], [659.25, 0.1], [783.99, 0.1],
      [1046.5, 0.3], [1046.5, 0.1], [1174.66, 0.4]
    ];
    let t = 0;
    melody.forEach(([freq, dur]) => {
      this.playTone(freq, dur + 0.1, 'sine', t, 1.0);
      t += dur;
    });
  }

  setVolume(v) {
    this.volume = Math.max(0, Math.min(1, v));
    if (this.masterGain) {
      this.masterGain.gain.setValueAtTime(this._muted ? 0 : this.volume, this.ctx.currentTime);
    }
  }

  mute() {
    this._muted = true;
    if (this.masterGain) this.masterGain.gain.setValueAtTime(0, this.ctx.currentTime);
  }

  unmute() {
    this._muted = false;
    if (this.masterGain) this.masterGain.gain.setValueAtTime(this.volume, this.ctx.currentTime);
  }

  get isMuted() { return this._muted; }
}

const audioEngine = new AudioEngine();
export default audioEngine;
