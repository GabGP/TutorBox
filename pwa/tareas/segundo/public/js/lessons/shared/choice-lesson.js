// Shared engine for "look, listen, tap the answer" lessons. A lesson only describes its rounds;
// this base handles layout, taps, retries, praise, the replay button and the star rating.
//
// Round shape:
//   { say, ask, hint?, scene?(ctx, box, t), choices: [{ correct, draw(ctx, box, t), hint?, at? }] }
//   - say:   what Q'uq' says (the child may not read yet, so this carries the question)
//   - ask:   short text in the question bar, for the adult next to the child
//   - scene: optional picture above the answer cards; without it the cards fill the screen
//   - at:    optional { x, y, w, h } as fractions of the canvas, to place a choice in the picture
//
// A wrong tap never ends the round: the child hears a hint and tries again. Stars count the
// rounds answered right on the first try.

import audio from '../../engine/audio.js';
import { Scene } from '../../engine/scene.js';
import { center, drawNumeral, drawText, inset } from './draw.js';

const PRAISE = ['¡Muy bien!', '¡Excelente!', '¡Así se hace!', '¡Lo lograste!'];
const TRY_AGAIN = '¡Casi! Inténtalo otra vez.';

export function shuffle(list) {
  const out = [...list];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

/**
 * Three numeral choices: the answer plus its nearest neighbours inside [min, max].
 * The answer is always computed by the caller (a + b, n - k, ...), never typed by hand.
 */
export function numberChoices(answer, { min = 0, max = 20, draw } = {}) {
  const near = [answer - 1, answer + 1, answer - 2, answer + 2, answer + 3, answer - 3]
    .filter((n) => n >= min && n <= max);
  return [answer, near[0], near[1]].map((value) => ({
    value,
    correct: value === answer,
    draw: draw ? (ctx, box) => draw(ctx, value, box) : (ctx, box) => drawNumeral(ctx, value, box),
  }));
}

/**
 * The answer plus hand-picked wrong answers, each one a real mistake (e.g. 32 - 7 -> 35 from
 * subtracting the small digit from the big one). Values may be numbers or short labels;
 * `draw(ctx, value, box)` defaults to fitted text. Duplicates of the answer are dropped.
 */
export function pickChoices(answer, wrongs, { draw = drawText } = {}) {
  const values = [answer, ...wrongs.filter((v, i, all) => v !== answer && all.indexOf(v) === i)];
  return values.map((value) => ({ value, correct: value === answer, draw: (ctx, box) => draw(ctx, value, box) }));
}

/**
 * Up to three wide pictures (clocks, woven designs, money) as wide cards, one under another, for a
 * round without a scene. Placed cards are not shuffled, so put the right one where you want it.
 */
export function stacked(choices) {
  return choices.map((c, i) => ({ ...c, at: { x: 0.18, y: 0.11 + i * 0.245, w: 0.64, h: 0.22 } }));
}

const inside = (b, x, y) => x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h;

export class ChoiceLesson extends Scene {
  /** Override: spoken once, before the first question. */
  get intro() { return ''; }

  /** Override: background gradient, top to bottom. */
  get colors() { return ['#B3E5FC', '#E8F5E9']; }

  /** Override: the list of rounds (see the header comment). */
  makeRounds() { return []; }

  setup() {
    this.rounds = this.makeRounds();
    this.totalRounds = this.rounds.length;
    this.firstTry = 0;
    this._t = 0;
    this._particles = [];
    this._startRound(this.intro);
  }

  _startRound(prefix = '') {
    const r = this.rounds[this.round];
    this._missed = false;
    this._locked = false;
    this._marks = new Map();
    this._shake = null;
    this._choices = r.choices.some((c) => c.at) ? r.choices : shuffle(r.choices);
    setTimeout(() => this._say(prefix), 500);
  }

  _say(prefix = '') {
    audio.speak(`${prefix} ${this.rounds[this.round].say}`.trim(), { rate: 0.85 });
  }

  get _layout() {
    const { W, H } = this;
    const scene = this.rounds[this.round]?.scene;
    return {
      replay: { x: W * 0.03, y: H * 0.01, w: 48, h: 48 },
      scene: { x: W * 0.04, y: H * 0.09, w: W * 0.92, h: H * 0.49 },
      cards: scene
        ? { x: W * 0.04, y: H * 0.61, w: W * 0.92, h: H * 0.22 }
        : { x: W * 0.04, y: H * 0.12, w: W * 0.92, h: H * 0.7 },
      bar: { x: W * 0.04, y: H * 0.86, w: W * 0.74, h: H * 0.11 },
    };
  }

  _box(choice, i, n) {
    const { W, H } = this;
    if (choice.at) return { x: choice.at.x * W, y: choice.at.y * H, w: choice.at.w * W, h: choice.at.h * H };
    const area = this._layout.cards;
    const gap = area.w * 0.04;
    const w = (area.w - gap * (n - 1)) / n;
    const h = Math.min(area.h, w * 1.8);
    const x0 = area.x + (area.w - (w * n + gap * (n - 1))) / 2;
    return { x: x0 + i * (w + gap), y: area.y + (area.h - h) / 2, w, h };
  }

  onTap(x, y) {
    if (this.isComplete || this._locked) return;
    const L = this._layout;
    if (inside(L.replay, x, y) || inside(L.bar, x, y)) return this._say();
    const n = this._choices.length;
    this._choices.forEach((c, i) => {
      const box = this._box(c, i, n);
      if (inside(box, x, y) && this._marks.get(c) !== 'wrong') this._answer(c, box);
    });
  }

  _answer(choice, box) {
    if (choice.correct) {
      this._locked = true;
      if (!this._missed) this.firstTry++;
      this._marks.set(choice, 'right');
      audio.playSuccess();
      audio.speak(PRAISE[Math.floor(Math.random() * PRAISE.length)], { rate: 0.9 });
      this._burst(center(box));
      setTimeout(() => {
        this.round++;
        if (this.round >= this.rounds.length) this._finish();
        else this._startRound();
      }, 1600);
    } else {
      this._missed = true;
      this._marks.set(choice, 'wrong');
      this._shake = { choice, until: this._t + 0.4 };
      audio.playError();
      audio.speak(choice.hint || this.rounds[this.round].hint || TRY_AGAIN, { rate: 0.85 });
    }
  }

  _finish() {
    this.isComplete = true;
    const accuracy = this.firstTry / this.rounds.length;
    this.completeLesson(accuracy >= 0.85 ? 3 : accuracy >= 0.6 ? 2 : 1);
  }

  _burst({ cx, cy }) {
    const colors = ['#FFD700', '#FF6F00', '#4CAF50', '#E91E63'];
    for (let i = 0; i < 14; i++) {
      const a = (Math.PI * 2 * i) / 14;
      const sp = 3 + Math.random() * 3;
      this._particles.push({ x: cx, y: cy, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - 1, life: 1, color: colors[i % 4], size: 5 + Math.random() * 5 });
    }
  }

  update(dt) {
    this._t += dt / 1000;
    this._particles = this._particles.filter((p) => {
      p.x += p.vx; p.y += p.vy; p.vy += 0.25; p.life -= dt * 0.0015;
      return p.life > 0;
    });
  }

  render() {
    const { ctx, W, H } = this;
    if (!W || !H || !this.rounds) return;
    const r = this.rounds[Math.min(this.round, this.rounds.length - 1)];
    const L = this._layout;

    const bg = ctx.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, this.colors[0]);
    bg.addColorStop(1, this.colors[1]);
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);

    if (r.scene) {
      ctx.fillStyle = 'rgba(255,255,255,0.45)';
      ctx.beginPath(); ctx.roundRect(L.scene.x, L.scene.y, L.scene.w, L.scene.h, 18); ctx.fill();
      r.scene(ctx, L.scene, this._t);
    }

    const n = this._choices.length;
    this._choices.forEach((c, i) => this._drawChoice(c, this._box(c, i, n)));

    this._drawChrome(r, L);

    this._particles.forEach((p) => {
      ctx.save(); ctx.globalAlpha = p.life; ctx.fillStyle = p.color;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2); ctx.fill(); ctx.restore();
    });
  }

  _drawChoice(c, box) {
    const { ctx } = this;
    const mark = this._marks.get(c);
    const shaking = this._shake && this._shake.choice === c && this._t < this._shake.until;
    ctx.save();
    if (shaking) ctx.translate(Math.sin(this._t * 60) * 6, 0);
    if (mark === 'wrong') ctx.globalAlpha = 0.4;
    ctx.fillStyle = mark === 'right' ? '#E8F5E9' : '#FFFFFF';
    ctx.strokeStyle = mark === 'right' ? '#43A047' : mark === 'wrong' ? '#E53935' : 'rgba(0,0,0,0.12)';
    ctx.lineWidth = mark ? 5 : 2;
    ctx.beginPath(); ctx.roundRect(box.x, box.y, box.w, box.h, 16); ctx.fill(); ctx.stroke();
    c.draw(ctx, inset(box, 0.08), this._t);
    ctx.restore();
  }

  _drawChrome(r, L) {
    const { ctx, W, H } = this;
    // Replay: the question again, for a child who could not read the bar.
    ctx.save();
    ctx.fillStyle = 'rgba(255,255,255,0.9)';
    ctx.beginPath(); ctx.arc(L.replay.x + 24, L.replay.y + 24, 22, 0, Math.PI * 2); ctx.fill();
    ctx.font = '24px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('🔊', L.replay.x + 24, L.replay.y + 25);
    ctx.restore();

    for (let i = 0; i < this.rounds.length; i++) {
      ctx.beginPath();
      ctx.arc(W / 2 - (this.rounds.length - 1) * 12 + i * 24, H * 0.045, 6, 0, Math.PI * 2);
      ctx.fillStyle = i < this.round ? '#4CAF50' : i === this.round ? '#FFD700' : 'rgba(255,255,255,0.6)';
      ctx.fill();
    }

    ctx.save();
    ctx.fillStyle = 'rgba(0,0,0,0.72)';
    ctx.beginPath(); ctx.roundRect(L.bar.x, L.bar.y, L.bar.w, L.bar.h, 14); ctx.fill();
    ctx.fillStyle = 'white';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    let size = Math.min(20, W * 0.05);
    do {
      ctx.font = `bold ${size}px Nunito, sans-serif`;
      size -= 1;
    } while (size > 11 && ctx.measureText(r.ask).width > L.bar.w - 20);
    ctx.fillText(r.ask, L.bar.x + L.bar.w / 2, L.bar.y + L.bar.h / 2);
    ctx.restore();
  }
}
