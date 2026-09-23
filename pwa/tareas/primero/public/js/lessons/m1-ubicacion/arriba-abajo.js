// Module 1, Lesson 1: Arriba y Abajo (Up and Down)
// A tall tree scene with quetzal at top and rabbit at bottom
// Child taps to identify which is UP and which is DOWN

import audio from '../../engine/audio.js';
import { TouchHandler } from '../../engine/touch.js';
import { drawQuq } from '../shared/draw.js';

export default class ArriababajoLesson {
  constructor(canvasId, config = {}) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.onComplete = config.onComplete || (() => {});
    this.totalRounds = 3;
    this.round = 0;
    this.correctAnswers = 0;
    this.errors = 0;
    this.isShowingFeedback = false;

    this._running = false;
    this._raf = null;
    this._lastTime = null;
    this._feedbackAlpha = 0;
    this._feedbackCorrect = false;
    this._animTime = 0;
    this._quetzalY = 0;
    this._rabbitY = 0;
    this._particles = [];
    this._tapZones = [];
    this._currentQuestion = null;

    this.touch = new TouchHandler(this.canvas);
    this.touch.onTap(pos => this._onTap(pos.x, pos.y));

    this._resizeBound = () => this._resize();
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

  start() {
    this._resize();
    this._running = true;
    this._lastTime = performance.now();

    // Set initial positions
    this._quetzalY = this.H * 0.2;
    this._rabbitY = this.H * 0.78;

    this._intro = '¡Mira el árbol! '; // spoken with the first question
    this._setupRound();
    this._loop();

  }

  _setupRound() {
    // Three rounds: identify quetzal (UP), rabbit (DOWN), then choose quetzal
    const questions = [
      {
        ask: '¿Dónde está el quetzal? ¡Tócalo!',
        narration: '¿Dónde está el quetzal? ¡Tócalo!',
        correctZone: 'top'
      },
      {
        ask: '¿Dónde está el conejo? ¡Tócalo!',
        narration: '¿Dónde está el conejo? ¡Tócalo!',
        correctZone: 'bottom'
      },
      {
        ask: '¿Quién está ARRIBA?',
        narration: '¿Quién está arriba? ¡Toca el que está arriba!',
        correctZone: 'top'
      }
    ];

    this._currentQuestion = questions[this.round];

    // Define tap zones (top half = quetzal area, bottom = rabbit area)
    this._tapZones = [
      { id: 'top', x: 0, y: 0, w: this.W, h: this.H * 0.55, label: '⬆️ ARRIBA', color: '#E3F2FD' },
      { id: 'bottom', x: 0, y: this.H * 0.55, w: this.W, h: this.H * 0.45, label: '⬇️ ABAJO', color: '#F3E5F5' }
    ];

    setTimeout(() => {
      if (this._currentQuestion) {
        audio.speak((this._intro || '') + this._currentQuestion.narration, { rate: 0.8 });
        this._intro = '';
      }
    }, 400);
  }

  _onTap(x, y) {
    if (this.isShowingFeedback || this.round >= this.totalRounds) return;

    // Check which zone was tapped
    let tappedZone = null;
    for (const zone of this._tapZones) {
      if (x >= zone.x && x <= zone.x + zone.w && y >= zone.y && y <= zone.y + zone.h) {
        tappedZone = zone;
        break;
      }
    }
    if (!tappedZone) return;

    const correct = tappedZone.id === this._currentQuestion.correctZone;
    this._showFeedback(correct, x, y);
  }

  _showFeedback(correct, x, y) {
    if (this.isShowingFeedback) return;
    this.isShowingFeedback = true;
    this._feedbackCorrect = correct;
    this._feedbackAlpha = 0.6;

    if (correct) {
      if (!this._missed) this.correctAnswers++; this._missed = false;
      audio.playSuccess();
      audio.speak('¡Muy bien! ¡Correcto!', { rate: 0.9 });
      this._spawnParticles(x, y);
    } else {
      this.errors++;
      this._missed = true;
      audio.playError();
      audio.speak('¡Casi! ' + this._currentQuestion.narration, { rate: 0.85 });
    }

    setTimeout(() => {
      this._feedbackAlpha = 0;
      this.isShowingFeedback = false;
      if (!correct) return; // same question again until it is right
      this.round++;
      if (this.round >= this.totalRounds) {
        this._finish();
      } else {
        this._setupRound();
      }
    }, correct ? 1300 : 900);
  }

  _spawnParticles(x, y) {
    const colors = ['#FFD700', '#FF6F00', '#E91E63', '#2196F3', '#4CAF50'];
    for (let i = 0; i < 16; i++) {
      const angle = (Math.PI * 2 * i) / 16;
      const speed = 3 + Math.random() * 4;
      this._particles.push({
        x, y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - 3,
        life: 1,
        color: colors[i % colors.length],
        size: 6 + Math.random() * 8
      });
    }
  }

  update(dt) {
    this._animTime += dt * 0.001;

    // Animate quetzal floating
    this._quetzalY = this.H * 0.2 + Math.sin(this._animTime * 2) * 8;

    // Animate rabbit bouncing
    this._rabbitY = this.H * 0.78 + Math.abs(Math.sin(this._animTime * 3)) * 4;

    // Update particles
    this._particles = this._particles.filter(p => {
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.3;
      p.life -= dt * 0.002;
      return p.life > 0;
    });

    // Fade feedback
    if (this._feedbackAlpha > 0 && !this.isShowingFeedback) {
      this._feedbackAlpha = Math.max(0, this._feedbackAlpha - dt * 0.003);
    }
  }

  render() {
    const ctx = this.ctx;
    const W = this.W, H = this.H;
    if (!W || !H) return;

    ctx.clearRect(0, 0, W, H);

    // ── Sky background ────────────────────────────────────────────────────
    const skyGrad = ctx.createLinearGradient(0, 0, 0, H);
    skyGrad.addColorStop(0, '#87CEEB');
    skyGrad.addColorStop(0.6, '#B3E5FC');
    skyGrad.addColorStop(1, '#81C784');
    ctx.fillStyle = skyGrad;
    ctx.fillRect(0, 0, W, H);

    // ── Clouds ────────────────────────────────────────────────────────────
    this._drawCloud(ctx, W * 0.15 + Math.sin(this._animTime * 0.3) * 10, H * 0.08, 50);
    this._drawCloud(ctx, W * 0.75 + Math.sin(this._animTime * 0.2) * 8, H * 0.12, 40);

    // ── Ground ────────────────────────────────────────────────────────────
    ctx.fillStyle = '#5D4037';
    ctx.fillRect(0, H * 0.86, W, H * 0.14);
    ctx.fillStyle = '#4CAF50';
    ctx.fillRect(0, H * 0.84, W, H * 0.04);

    // ── Big Tree ──────────────────────────────────────────────────────────
    const treeX = W / 2;
    const trunkW = W * 0.07;
    const trunkTop = H * 0.18;
    const trunkBot = H * 0.84;

    // Trunk
    ctx.fillStyle = '#5D4037';
    ctx.beginPath();
    ctx.roundRect(treeX - trunkW / 2, trunkTop, trunkW, trunkBot - trunkTop, [6, 6, 2, 2]);
    ctx.fill();

    // Bark lines
    ctx.strokeStyle = '#4E342E';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 8]);
    ctx.beginPath();
    ctx.moveTo(treeX - 4, trunkTop + 20);
    ctx.lineTo(treeX - 4, trunkBot - 20);
    ctx.stroke();
    ctx.setLineDash([]);

    // Canopy layers
    const canopyColors = ['#1B5E20', '#2E7D32', '#388E3C', '#4CAF50'];
    const canopyRadii = [W * 0.28, W * 0.24, W * 0.2, W * 0.16];
    const canopyYPos = [trunkTop + 10, trunkTop - 15, trunkTop - 40, trunkTop - 60];

    canopyColors.forEach((col, i) => {
      ctx.fillStyle = col;
      ctx.beginPath();
      ctx.ellipse(treeX, canopyYPos[i], canopyRadii[i], canopyRadii[i] * 0.75, 0, 0, Math.PI * 2);
      ctx.fill();
    });

    // ── ARRIBA zone indicator (subtle) ────────────────────────────────────
    if (!this.isShowingFeedback) {
      // Top arrow hint
      ctx.save();
      ctx.globalAlpha = 0.25 + Math.sin(this._animTime * 3) * 0.1;
      ctx.fillStyle = '#2196F3';
      ctx.font = `bold ${Math.round(W * 0.08)}px Nunito, sans-serif`;
      ctx.textAlign = 'left';
      ctx.fillText('⬆️', W * 0.04, H * 0.3);

      // Bottom arrow hint
      ctx.fillStyle = '#9C27B0';
      ctx.textAlign = 'left';
      ctx.fillText('⬇️', W * 0.04, H * 0.75);
      ctx.restore();
    }

    // ── Quetzal bird (at top of tree) ────────────────────────────────────
    this._drawQuetzal(ctx, treeX + W * 0.15, this._quetzalY, W * 0.14);

    // ── Rabbit (at bottom of tree) ────────────────────────────────────────
    this._drawRabbit(ctx, treeX - W * 0.18, this._rabbitY, W * 0.1);

    // ── Question Prompt ────────────────────────────────────────────────────
    if (this._currentQuestion) {
      ctx.save();
      ctx.fillStyle = 'rgba(0,0,0,0.65)';
      const promptH = H * 0.1;
      ctx.beginPath();
      ctx.roundRect(W * 0.05, H * 0.86, W * 0.9, promptH, 16);
      ctx.fill();

      ctx.fillStyle = 'white';
      ctx.font = `bold ${Math.min(18, W * 0.048)}px Nunito, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(this._currentQuestion.ask, W / 2, H * 0.86 + promptH / 2);
      ctx.restore();
    }

    // ── Round indicator ────────────────────────────────────────────────────
    ctx.save();
    for (let i = 0; i < this.totalRounds; i++) {
      ctx.beginPath();
      ctx.arc(W / 2 - (this.totalRounds - 1) * 12 + i * 24, H * 0.04, 6, 0, Math.PI * 2);
      ctx.fillStyle = i < this.round ? '#4CAF50' : i === this.round ? '#FFD700' : 'rgba(255,255,255,0.4)';
      ctx.fill();
    }
    ctx.restore();

    // ── Feedback flash ────────────────────────────────────────────────────
    if (this._feedbackAlpha > 0) {
      ctx.save();
      ctx.globalAlpha = this._feedbackAlpha * 0.35;
      ctx.fillStyle = this._feedbackCorrect ? '#4CAF50' : '#F44336';
      ctx.fillRect(0, 0, W, H);
      ctx.restore();

      if (this._feedbackCorrect) {
        ctx.save();
        ctx.font = `${Math.round(W * 0.15)}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.globalAlpha = this._feedbackAlpha;
        ctx.fillText('✅', W / 2, H / 2);
        ctx.restore();
      }
    }

    // ── Particles ─────────────────────────────────────────────────────────
    this._particles.forEach(p => {
      ctx.save();
      ctx.globalAlpha = p.life;
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    });
  }

  _drawCloud(ctx, x, y, size) {
    ctx.save();
    ctx.fillStyle = 'rgba(255,255,255,0.85)';
    [[-size * 0.4, 0], [0, -size * 0.15], [size * 0.4, 0], [0, size * 0.1]].forEach(([ox, oy]) => {
      ctx.beginPath();
      ctx.arc(x + ox, y + oy, size * 0.4, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.restore();
  }

  _drawQuetzal(ctx, x, y, size) {
    // Q'uq' himself (icons/quq.svg), the same drawing as on every other screen.
    drawQuq(ctx, x, y + size * 0.3, size * 1.7);
  }

  _drawRabbit(ctx, x, y, size) {
    ctx.save();
    // Ears
    ctx.fillStyle = '#E0E0E0';
    ctx.beginPath();
    ctx.ellipse(x - size * 0.2, y - size * 0.9, size * 0.12, size * 0.35, -0.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(x + size * 0.2, y - size * 0.9, size * 0.12, size * 0.35, 0.2, 0, Math.PI * 2);
    ctx.fill();
    // Inner ears
    ctx.fillStyle = '#FFCDD2';
    ctx.beginPath();
    ctx.ellipse(x - size * 0.2, y - size * 0.9, size * 0.06, size * 0.22, -0.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.ellipse(x + size * 0.2, y - size * 0.9, size * 0.06, size * 0.22, 0.2, 0, Math.PI * 2);
    ctx.fill();
    // Body
    ctx.fillStyle = '#F5F5F5';
    ctx.beginPath();
    ctx.ellipse(x, y + size * 0.1, size * 0.45, size * 0.42, 0, 0, Math.PI * 2);
    ctx.fill();
    // Head
    ctx.fillStyle = '#F5F5F5';
    ctx.beginPath();
    ctx.arc(x, y - size * 0.35, size * 0.32, 0, Math.PI * 2);
    ctx.fill();
    // Eye
    ctx.fillStyle = '#1A237E';
    ctx.beginPath();
    ctx.arc(x + size * 0.12, y - size * 0.4, size * 0.07, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = 'white';
    ctx.beginPath();
    ctx.arc(x + size * 0.13, y - size * 0.41, size * 0.025, 0, Math.PI * 2);
    ctx.fill();
    // Nose
    ctx.fillStyle = '#E91E63';
    ctx.beginPath();
    ctx.arc(x + size * 0.2, y - size * 0.3, size * 0.05, 0, Math.PI * 2);
    ctx.fill();
    // Tail
    ctx.fillStyle = 'white';
    ctx.beginPath();
    ctx.arc(x - size * 0.42, y + size * 0.15, size * 0.12, 0, Math.PI * 2);
    ctx.fill();
    // Front paws
    ctx.fillStyle = '#EEEEEE';
    ctx.beginPath();
    ctx.ellipse(x + size * 0.25, y + size * 0.38, size * 0.12, size * 0.08, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  _loop() {
    if (!this._running) return;
    const now = performance.now();
    const dt = Math.min(50, now - this._lastTime);
    this._lastTime = now;
    this.update(dt);
    this.render();
    this._raf = requestAnimationFrame(() => this._loop());
  }

  _finish() {
    const stars = this.correctAnswers >= 3 ? 3 : this.correctAnswers >= 2 ? 2 : 1;
    audio.playVictory && audio.playVictory();
    if (this.onComplete) setTimeout(() => this.onComplete(stars), 700);
  }

  destroy() {
    this._running = false;
    if (this._raf) cancelAnimationFrame(this._raf);
    this.touch.destroy();
    window.removeEventListener('resize', this._resizeBound);
  }
}
