// Module 2, Lesson 1: Patterns in Güipil (Guatemalan textile)
// Shows a weaving loom with color sequences - child picks the next color

import audio from '../../engine/audio.js';
import { TouchHandler } from '../../engine/touch.js';

const GUIPIL_COLORS = ['#E53935', '#1E88E5', '#F9A825', '#43A047', '#8E24AA', '#FF7043'];
const COLOR_NAMES = ['rojo', 'azul', 'amarillo', 'verde', 'morado', 'naranja'];

export default class PatronesGuipilLesson {
  constructor(canvasId, config = {}) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.onComplete = config.onComplete || (() => {});
    this.totalRounds = 4;
    this.round = 0;
    this.correctAnswers = 0;
    this.isShowingFeedback = false;
    this._animTime = 0;
    this._running = false;
    this._raf = null;
    this._lastTime = null;
    this._feedbackAlpha = 0;
    this._feedbackCorrect = false;
    this._particles = [];
    this._pattern = [];
    this._choices = [];
    this._selectedBtn = null;
    this._weavingAnim = 0;

    this.touch = new TouchHandler(this.canvas);
    this.touch.onTap(pos => this._onTap(pos.x, pos.y));
    this._resizeBound = () => { this._resize(); this._buildButtons(); };
    window.addEventListener('resize', this._resizeBound);
  }

  _resize() {
    const parent = this.canvas.parentElement;
    if (!parent) return;
    const rect = parent.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.canvas.style.width = rect.width + 'px';
    this.canvas.style.height = rect.height + 'px';
    this.ctx.scale(dpr, dpr);
    this.W = rect.width;
    this.H = rect.height;
  }

  _buildButtons() {
    if (!this.W) return;
    const W = this.W, H = this.H;
    const btnSize = Math.min(W * 0.2, 70);
    const totalW = this._choices.length * (btnSize + 12) - 12;
    const startX = (W - totalW) / 2;

    this._choiceBtns = this._choices.map((colorIdx, i) => ({
      x: startX + i * (btnSize + 12),
      y: H * 0.76,
      w: btnSize,
      h: btnSize,
      colorIdx,
      color: GUIPIL_COLORS[colorIdx]
    }));
  }

  _setupRound() {
    // Increasingly complex patterns
    const patterns = [
      [0, 1, 0, 1, 0],         // R B R B ?R (answer: R)
      [0, 1, 2, 0, 1],         // R B Y R B ?Y
      [0, 0, 1, 0, 0],         // R R B R R ?B
      [0, 1, 2, 3, 0, 1, 2],   // R B Y G R B Y ?G
    ];
    const roundPattern = patterns[this.round % patterns.length];
    this._pattern = roundPattern;
    this._correctColor = roundPattern[roundPattern.length - 1];
    this._displayPattern = roundPattern.slice(0, -1); // show all but last

    // Build 3 answer choices (correct + 2 wrong)
    const wrong = GUIPIL_COLORS.map((_, i) => i)
      .filter(i => i !== this._correctColor)
      .sort(() => Math.random() - 0.5)
      .slice(0, 2);
    this._choices = [this._correctColor, ...wrong].sort(() => Math.random() - 0.5);
    this._buildButtons();
    this._weavingAnim = 0;

    const first = this.round === 0 && !this._missed ? '¡Mira el güipil maya! ' : '';
    setTimeout(() => audio.speak(first + '¿Qué color sigue en el patrón? ¡Toca el correcto!', { rate: 0.8 }), 400);
  }

  _onTap(x, y) {
    if (this.isShowingFeedback || !this._choiceBtns) return;
    for (const btn of this._choiceBtns) {
      if (x >= btn.x && x <= btn.x + btn.w && y >= btn.y && y <= btn.y + btn.h) {
        const correct = btn.colorIdx === this._correctColor;
        this._selectedBtn = btn;
        this._showFeedback(correct, x + btn.w/2, y + btn.h/2);
        return;
      }
    }
  }

  _showFeedback(correct, x, y) {
    this.isShowingFeedback = true;
    this._feedbackCorrect = correct;
    this._feedbackAlpha = 0.5;
    if (correct) {
      if (!this._missed) this.correctAnswers++; this._missed = false;
      audio.playSuccess();
      audio.speak(`¡Muy bien! Es ${COLOR_NAMES[this._correctColor]}`, { rate: 0.9 });
      this._spawnParticles(x, y);
      this._weavingAnim = 1; // trigger complete weave animation
    } else {
      this._missed = true;
      audio.playError();
      audio.speak('¡Casi! Di los colores desde el principio. ¿Qué color sigue?', { rate: 0.85 });
    }
    setTimeout(() => {
      this.isShowingFeedback = false;
      this._feedbackAlpha = 0;
      this._selectedBtn = null;
      if (!correct) return; // same question again until it is right
      this.round++;
      if (this.round >= this.totalRounds) this._finish();
      else this._setupRound();
    }, correct ? 1300 : 900);
  }

  _spawnParticles(x, y) {
    for (let i = 0; i < 14; i++) {
      const a = (Math.PI * 2 * i) / 14;
      const sp = 3 + Math.random() * 4;
      this._particles.push({
        x, y, vx: Math.cos(a)*sp, vy: Math.sin(a)*sp - 2, life: 1,
        color: GUIPIL_COLORS[Math.floor(Math.random() * GUIPIL_COLORS.length)], size: 7 + Math.random() * 7
      });
    }
  }

  start() {
    this._resize();
    this._running = true;
    this._lastTime = performance.now();
    this._setupRound();
    this._loop();
  }

  update(dt) {
    this._animTime += dt * 0.001;
    this._particles = this._particles.filter(p => {
      p.x += p.vx; p.y += p.vy; p.vy += 0.25; p.life -= dt * 0.002; return p.life > 0;
    });
  }

  render() {
    const ctx = this.ctx; const W = this.W; const H = this.H;
    if (!W || !H) return;
    ctx.clearRect(0, 0, W, H);

    // Background - warm textile workshop
    const bg = ctx.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, '#3E2723');
    bg.addColorStop(0.5, '#4E342E');
    bg.addColorStop(1, '#5D4037');
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);

    // Wood grain effect on background
    ctx.save();
    ctx.globalAlpha = 0.05;
    for (let y = 0; y < H; y += 12) {
      ctx.fillStyle = y % 24 === 0 ? '#6D4C41' : '#3E2723';
      ctx.fillRect(0, y, W, 6);
    }
    ctx.restore();

    // ── Loom frame ────────────────────────────────────────────────────────
    const loomX = W * 0.06;
    const loomY = H * 0.08;
    const loomW = W * 0.88;
    const loomH = H * 0.55;

    // Loom vertical posts
    ctx.fillStyle = '#8D6E63';
    ctx.fillRect(loomX, loomY, W*0.04, loomH);
    ctx.fillRect(loomX + loomW - W*0.04, loomY, W*0.04, loomH);

    // Loom horizontal bars
    ctx.fillStyle = '#6D4C41';
    ctx.fillRect(loomX, loomY, loomW, H*0.03);
    ctx.fillRect(loomX, loomY + loomH - H*0.03, loomW, H*0.03);

    // ── Warp threads ──────────────────────────────────────────────────────
    const threadW = loomW * 0.85;
    const threadX = loomX + loomW * 0.075;
    const numThreads = 20;
    for (let i = 0; i <= numThreads; i++) {
      const tx = threadX + (threadW / numThreads) * i;
      ctx.strokeStyle = '#D7CCC8';
      ctx.lineWidth = 1;
      ctx.globalAlpha = 0.5;
      ctx.beginPath();
      ctx.moveTo(tx, loomY + H*0.03);
      ctx.lineTo(tx, loomY + loomH - H*0.03);
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    // ── Woven pattern rows ────────────────────────────────────────────────
    const patternToShow = this._displayPattern;
    const rowH = Math.min(40, (loomH * 0.6) / Math.max(patternToShow.length, 1));
    const patternAreaY = loomY + H*0.04;

    patternToShow.forEach((colorIdx, i) => {
      const ry = patternAreaY + i * (rowH + 3);
      const wave = Math.sin(this._animTime * 2 + i * 0.5) * 2;

      // Woven row
      ctx.fillStyle = GUIPIL_COLORS[colorIdx];
      ctx.save();
      ctx.shadowColor = 'rgba(0,0,0,0.3)';
      ctx.shadowBlur = 4;
      ctx.beginPath();
      ctx.roundRect(threadX, ry + wave, threadW, rowH, 2);
      ctx.fill();
      ctx.restore();

      // Texture lines on row
      ctx.save();
      ctx.globalAlpha = 0.25;
      ctx.strokeStyle = 'white';
      ctx.lineWidth = 1;
      for (let tx = threadX + 10; tx < threadX + threadW; tx += 12) {
        ctx.beginPath();
        ctx.moveTo(tx, ry + wave + 2);
        ctx.lineTo(tx, ry + wave + rowH - 2);
        ctx.stroke();
      }
      ctx.restore();

      // Pattern position label (number)
      ctx.save();
      ctx.fillStyle = 'rgba(255,255,255,0.7)';
      ctx.font = `bold ${Math.round(rowH*0.5)}px Nunito,sans-serif`;
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      ctx.fillText(String(i + 1), loomX + W*0.005, ry + rowH/2 + wave);
      ctx.restore();
    });

    // ── Question mark row ─────────────────────────────────────────────────
    const qy = patternAreaY + patternToShow.length * (rowH + 3);
    const questionPulse = 0.5 + Math.sin(this._animTime * 3) * 0.3;

    ctx.save();
    ctx.globalAlpha = questionPulse;
    ctx.setLineDash([6, 4]);
    ctx.strokeStyle = '#FFD700';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.roundRect(threadX, qy, threadW, rowH, 2);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = '#FFD700';
    ctx.font = `bold ${Math.round(rowH * 0.65)}px Nunito,sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('?', threadX + threadW/2, qy + rowH/2);
    ctx.restore();

    // ── Color choice buttons ───────────────────────────────────────────────
    if (this._choiceBtns) {
      const btnLabel = document.createElement;
      ctx.save();
      ctx.font = `bold ${Math.round(W*0.04)}px Nunito,sans-serif`;
      ctx.fillStyle = 'rgba(255,255,255,0.7)';
      ctx.textAlign = 'center';
      ctx.fillText('¿Cuál sigue?', W/2, H * 0.71);
      ctx.restore();

      this._choiceBtns.forEach((btn, i) => {
        const isSelected = this._selectedBtn === btn;
        const pulse = 1 + Math.sin(this._animTime * 2.5 + i) * 0.04;

        ctx.save();
        // Shadow
        ctx.shadowColor = 'rgba(0,0,0,0.4)';
        ctx.shadowBlur = 10;

        // Button
        ctx.fillStyle = btn.color;
        ctx.beginPath();
        ctx.roundRect(
          btn.x + (btn.w * (1-pulse))/2,
          btn.y + (btn.h * (1-pulse))/2,
          btn.w * pulse,
          btn.h * pulse,
          14
        );
        ctx.fill();

        // Border
        ctx.shadowBlur = 0;
        ctx.strokeStyle = isSelected ? '#FFD700' : 'rgba(255,255,255,0.4)';
        ctx.lineWidth = isSelected ? 4 : 2;
        ctx.stroke();

        // Color name below
        ctx.fillStyle = 'rgba(255,255,255,0.8)';
        ctx.font = `bold ${Math.round(W*0.03)}px Nunito,sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(COLOR_NAMES[btn.colorIdx], btn.x + btn.w/2, btn.y + btn.h + 4);

        ctx.restore();
      });
    }

    // Round dots
    ctx.save();
    for (let i=0;i<this.totalRounds;i++) {
      ctx.beginPath();
      ctx.arc(W/2-(this.totalRounds-1)*12+i*24, H*0.04, 6, 0, Math.PI*2);
      ctx.fillStyle = i<this.round?'#4CAF50':i===this.round?'#FFD700':'rgba(255,255,255,0.3)'; ctx.fill();
    }
    ctx.restore();

    // Feedback overlay
    if (this._feedbackAlpha > 0) {
      ctx.save(); ctx.globalAlpha = this._feedbackAlpha * 0.3;
      ctx.fillStyle = this._feedbackCorrect ? '#4CAF50' : '#F44336';
      ctx.fillRect(0,0,W,H); ctx.restore();
    }

    // Particles
    this._particles.forEach(p => {
      ctx.save(); ctx.globalAlpha = p.life; ctx.fillStyle = p.color;
      ctx.beginPath(); ctx.arc(p.x,p.y,p.size*p.life,0,Math.PI*2); ctx.fill(); ctx.restore();
    });
  }

  _loop() {
    if (!this._running) return;
    const now = performance.now();
    const dt = Math.min(50, now - this._lastTime);
    this._lastTime = now;
    this.update(dt); this.render();
    this._raf = requestAnimationFrame(() => this._loop());
  }

  _finish() {
    const stars = this.correctAnswers >= 4 ? 3 : this.correctAnswers >= 3 ? 2 : 1;
    if (this.onComplete) setTimeout(() => this.onComplete(stars), 600);
  }

  destroy() {
    this._running = false;
    if (this._raf) cancelAnimationFrame(this._raf);
    this.touch.destroy();
    window.removeEventListener('resize', this._resizeBound);
  }
}
