// Base Scene class for all lesson activities
// All interactive lessons extend this class

import audio from './audio.js';
import { TouchHandler } from './touch.js';
import { clearCanvas, scaleCanvas } from './canvas.js';

export class Scene {
  /**
   * @param {string} canvasId - ID of the canvas element
   * @param {Object} config - { totalRounds, onComplete }
   */
  constructor(canvasId, config = {}) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) throw new Error(`Canvas #${canvasId} not found`);

    this.ctx = this.canvas.getContext('2d');
    this.config = config;
    this.onCompleteCallback = config.onComplete || null;

    // Game state
    this.round = 0;
    this.totalRounds = config.totalRounds || 3;
    this.correctAnswers = 0;
    this.errors = 0;
    this.isComplete = false;
    this.isShowingFeedback = false;

    // Animation loop
    this._raf = null;
    this._lastTime = null;
    this._running = false;

    // Touch handler
    this.touch = new TouchHandler(this.canvas);
    this.touch.onTap((pos) => this.onTap(pos.x, pos.y));
    this.touch.onDragStart((pos) => this.onDragStart(pos.x, pos.y));
    this.touch.onDragMove((pos) => this.onDragMove(pos.x, pos.y));
    this.touch.onDragEnd((pos) => this.onDragEnd(pos.x, pos.y));

    // Scale for DPR
    this._dpr = window.devicePixelRatio || 1;
    this._resize();
    this._resizeBound = this._resize.bind(this);
    window.addEventListener('resize', this._resizeBound);
  }

  _resize() {
    const rect = this.canvas.parentElement
      ? this.canvas.parentElement.getBoundingClientRect()
      : { width: window.innerWidth, height: window.innerHeight * 0.75 };
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.canvas.style.width = rect.width + 'px';
    this.canvas.style.height = rect.height + 'px';
    this.ctx.scale(dpr, dpr);
    this._W = rect.width;
    this._H = rect.height;
    if (this._running) this.render();
  }

  get W() { return this._W || this.canvas.clientWidth; }
  get H() { return this._H || this.canvas.clientHeight; }

  /**
   * Override in subclass: initial setup
   */
  setup() {}

  /**
   * Override in subclass: called each frame with delta time (ms)
   */
  update(dt) {}

  /**
   * Override in subclass: draw everything
   */
  render() {}

  /**
   * Start the game loop
   */
  start() {
    this.setup();
    this._running = true;
    this._lastTime = performance.now();
    this._loop();
  }

  _loop() {
    if (!this._running) return;
    const now = performance.now();
    const dt = Math.min(50, now - this._lastTime); // cap at 50ms
    this._lastTime = now;

    this.update(dt);
    this.render();

    this._raf = requestAnimationFrame(() => this._loop());
  }

  /**
   * Show feedback for correct/incorrect answer
   */
  showFeedback(correct) {
    if (this.isShowingFeedback) return;
    this.isShowingFeedback = true;

    if (correct) {
      this.correctAnswers++;
      audio.playSuccess();
      audio.speak('¡Muy bien!', { rate: 0.9 });
    } else {
      this.errors++;
      audio.playError();
      audio.speak('¡Inténtalo de nuevo!', { rate: 0.85 });
    }

    setTimeout(() => {
      this.isShowingFeedback = false;
      this.round++;
      if (this.round >= this.totalRounds) {
        this._finishLesson();
      } else {
        this.nextRound();
      }
    }, correct ? 1200 : 900);
  }

  /**
   * Called when lesson is complete
   */
  _finishLesson() {
    this.isComplete = true;
    const accuracy = this.correctAnswers / this.totalRounds;
    const stars = accuracy >= 0.85 ? 3 : accuracy >= 0.6 ? 2 : 1;
    this.completeLesson(stars);
  }

  /**
   * Award stars and notify parent
   */
  completeLesson(stars) {
    audio.playVictory();
    audio.playStars();
    if (this.onCompleteCallback) {
      setTimeout(() => this.onCompleteCallback(stars), 800);
    }
  }

  /**
   * Override: advance to next round
   */
  nextRound() {}

  /**
   * Override: handle tap
   */
  onTap(x, y) {}

  /**
   * Override: handle drag events
   */
  onDragStart(x, y) {}
  onDragMove(x, y) {}
  onDragEnd(x, y) {}

  /**
   * Utility: draw a feedback flash on the canvas
   */
  flashFeedback(correct) {
    const color = correct ? 'rgba(76,175,80,0.3)' : 'rgba(244,67,54,0.25)';
    this.ctx.save();
    this.ctx.fillStyle = color;
    this.ctx.fillRect(0, 0, this.W, this.H);
    this.ctx.restore();
  }

  /**
   * Draw star rating on canvas
   */
  drawStars(count, x, y, size = 24) {
    const ctx = this.ctx;
    for (let i = 0; i < 3; i++) {
      const cx = x + i * (size * 2.2);
      const cy = y;
      const color = i < count ? '#FFD700' : 'rgba(255,255,255,0.3)';
      ctx.save();
      ctx.fillStyle = color;
      ctx.beginPath();
      const s = size;
      for (let j = 0; j < 5; j++) {
        const outerAngle = (Math.PI * 2 * j) / 5 - Math.PI / 2;
        const innerAngle = outerAngle + Math.PI / 5;
        if (j === 0) ctx.moveTo(cx + s * Math.cos(outerAngle), cy + s * Math.sin(outerAngle));
        else ctx.lineTo(cx + s * Math.cos(outerAngle), cy + s * Math.sin(outerAngle));
        ctx.lineTo(cx + (s * 0.4) * Math.cos(innerAngle), cy + (s * 0.4) * Math.sin(innerAngle));
      }
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    }
  }

  /**
   * Clean up resources
   */
  destroy() {
    this._running = false;
    if (this._raf) cancelAnimationFrame(this._raf);
    this.touch.destroy();
    window.removeEventListener('resize', this._resizeBound);
    clearCanvas(this.ctx);
  }
}
