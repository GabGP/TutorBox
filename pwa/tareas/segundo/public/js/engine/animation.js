// Simple Tweening Engine
// Used for canvas-based animations in lessons

export class Tween {
  /**
   * @param {Object} target - Object with numeric properties to animate
   * @param {Object} props - Target values { prop: targetValue }
   * @param {number} duration - Duration in milliseconds
   * @param {Function} easing - Easing function (t) => t'
   * @param {Function} onComplete - Called when done
   */
  constructor(target, props, duration, easing = Tween.easeOut, onComplete = null) {
    this.target = target;
    this.props = props;
    this.duration = duration;
    this.easing = easing;
    this.onComplete = onComplete;
    this.elapsed = 0;
    this.done = false;

    // Store starting values
    this.startValues = {};
    for (const key in props) {
      this.startValues[key] = target[key] || 0;
    }
  }

  update(dt) {
    if (this.done) return;
    this.elapsed += dt;
    const t = Math.min(1, this.elapsed / this.duration);
    const e = this.easing(t);

    for (const key in this.props) {
      this.target[key] = this.startValues[key] + (this.props[key] - this.startValues[key]) * e;
    }

    if (t >= 1) {
      this.done = true;
      if (this.onComplete) this.onComplete();
    }
  }

  static lerp(a, b, t) { return a + (b - a) * t; }

  static linear(t) { return t; }

  static easeOut(t) { return 1 - Math.pow(1 - t, 3); }

  static easeIn(t) { return t * t * t; }

  static easeInOut(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  static easeElastic(t) {
    if (t === 0 || t === 1) return t;
    const c4 = (2 * Math.PI) / 3;
    return Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * c4) + 1;
  }

  static easeBounce(t) {
    if (t < 1 / 2.75) {
      return 7.5625 * t * t;
    } else if (t < 2 / 2.75) {
      t -= 1.5 / 2.75;
      return 7.5625 * t * t + 0.75;
    } else if (t < 2.5 / 2.75) {
      t -= 2.25 / 2.75;
      return 7.5625 * t * t + 0.9375;
    } else {
      t -= 2.625 / 2.75;
      return 7.5625 * t * t + 0.984375;
    }
  }
}

class AnimationManager {
  constructor() {
    this.tweens = [];
    this._running = false;
    this._lastTime = null;
    this._raf = null;
    this._externalUpdate = false;
  }

  add(tween) {
    this.tweens.push(tween);
    if (!this._running && !this._externalUpdate) {
      this._start();
    }
    return tween;
  }

  /**
   * Create and add a tween in one call
   */
  tween(target, props, duration, easing, onComplete) {
    return this.add(new Tween(target, props, duration, easing, onComplete));
  }

  /**
   * Update all tweens with delta time (ms)
   * Call this from your own loop if _externalUpdate=true
   */
  update(dt) {
    this.tweens = this.tweens.filter(tw => {
      tw.update(dt);
      return !tw.done;
    });
  }

  _start() {
    this._running = true;
    this._lastTime = performance.now();
    this._loop();
  }

  _loop() {
    const now = performance.now();
    const dt = now - this._lastTime;
    this._lastTime = now;

    this.update(dt);

    if (this.tweens.length > 0) {
      this._raf = requestAnimationFrame(() => this._loop());
    } else {
      this._running = false;
    }
  }

  clearAll() {
    this.tweens = [];
    if (this._raf) cancelAnimationFrame(this._raf);
    this._running = false;
  }

  /**
   * Promise-based delay
   */
  wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Animate a value from 0 to 1 over duration, calling fn each frame
   */
  animate(duration, fn, easing = Tween.easeOut) {
    return new Promise(resolve => {
      const proxy = { t: 0 };
      this.add(new Tween(proxy, { t: 1 }, duration, easing, resolve));
      // Update fn through separate mechanism
      const startTime = performance.now();
      const tick = () => {
        const elapsed = performance.now() - startTime;
        const t = Math.min(1, elapsed / duration);
        fn(easing(t));
        if (t < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  }
}

const animationManager = new AnimationManager();
export default animationManager;
