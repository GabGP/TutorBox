// Module 1, Lesson 2: Adentro y Afuera (Inside and Outside)
// House scene - child taps objects inside or outside the house

import audio from '../../engine/audio.js';
import { TouchHandler } from '../../engine/touch.js';

export default class AdentroAfueraLesson {
  constructor(canvasId, config = {}) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.onComplete = config.onComplete || (() => {});
    this.totalRounds = 3;
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
    this._objects = [];
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
    this._setupObjects();
  }

  _setupObjects() {
    const W = this.W, H = this.H;
    // House bounds
    this.houseX = W * 0.2;
    this.houseY = H * 0.3;
    this.houseW = W * 0.6;
    this.houseH = H * 0.45;

    // Objects: some inside, some outside the house
    this._objects = [
      { id: 'cat', emoji: '🐱', x: W * 0.45, y: H * 0.52, inside: true, label: 'gato' },
      { id: 'flower', emoji: '🌸', x: W * 0.08, y: H * 0.65, inside: false, label: 'flor' },
      { id: 'table', emoji: '🪑', x: W * 0.62, y: H * 0.55, inside: true, label: 'silla' },
      { id: 'tree', emoji: '🌳', x: W * 0.88, y: H * 0.6, inside: false, label: 'árbol' },
      { id: 'dog', emoji: '🐶', x: W * 0.1, y: H * 0.58, inside: false, label: 'perro' },
      { id: 'cup', emoji: '🥤', x: W * 0.5, y: H * 0.62, inside: true, label: 'vaso' }
    ];
  }

  _setupRound() {
    const questions = [
      { ask: '¿Qué está ADENTRO de la casa? ¡Toca uno!', correctProp: true, narration: '¿Qué está adentro de la casa?' },
      { ask: '¿Qué está AFUERA de la casa? ¡Tócalo!', correctProp: false, narration: '¿Qué está afuera de la casa?' },
      { ask: '¿El gato está adentro o afuera?', correctProp: true, targetId: 'cat', narration: '¿El gato está adentro o afuera de la casa?' }
    ];
    this._currentQuestion = questions[this.round];
    setTimeout(() => {
      audio.speak((this._intro || '') + this._currentQuestion.narration, { rate: 0.8 });
      this._intro = '';
    }, 400);
  }

  _onTap(x, y) {
    if (this.isShowingFeedback) return;
    const size = this.W * 0.1;
    for (const obj of this._objects) {
      if (Math.abs(x - obj.x) < size && Math.abs(y - obj.y) < size) {
        const q = this._currentQuestion;
        let correct;
        if (q.targetId) {
          correct = obj.id === q.targetId;
        } else {
          correct = obj.inside === q.correctProp;
        }
        this._showFeedback(correct, x, y);
        return;
      }
    }
  }

  _showFeedback(correct, x, y) {
    this.isShowingFeedback = true;
    this._feedbackCorrect = correct;
    this._feedbackAlpha = 0.5;
    if (correct) { if (!this._missed) this.correctAnswers++; this._missed = false; audio.playSuccess(); audio.speak('¡Correcto! ¡Muy bien!'); this._spawnParticles(x, y); }
    else { this._missed = true; audio.playError(); audio.speak('¡Casi! ' + this._currentQuestion.narration, { rate: 0.85 }); }
    setTimeout(() => {
      this.isShowingFeedback = false;
      this._feedbackAlpha = 0;
      if (!correct) return; // same question again until it is right
      this.round++;
      if (this.round >= this.totalRounds) this._finish();
      else this._setupRound();
    }, correct ? 1200 : 900);
  }

  _spawnParticles(x, y) {
    const colors = ['#FFD700', '#FF6F00', '#4CAF50', '#E91E63'];
    for (let i = 0; i < 12; i++) {
      const a = (Math.PI * 2 * i) / 12;
      const sp = 3 + Math.random() * 4;
      this._particles.push({ x, y, vx: Math.cos(a)*sp, vy: Math.sin(a)*sp-2, life:1, color:colors[i%4], size:6+Math.random()*6 });
    }
  }

  start() {
    this._resize();
    this._running = true;
    this._lastTime = performance.now();
    this._intro = '¡Mira la casa! '; // spoken with the first question
    this._setupRound();
    this._loop();
  }

  update(dt) {
    this._animTime += dt * 0.001;
    this._particles = this._particles.filter(p => {
      p.x += p.vx; p.y += p.vy; p.vy += 0.3; p.life -= dt * 0.002; return p.life > 0;
    });
  }

  render() {
    const ctx = this.ctx; const W = this.W; const H = this.H;
    if (!W || !H) return;
    ctx.clearRect(0, 0, W, H);

    // Sky
    const sky = ctx.createLinearGradient(0,0,0,H);
    sky.addColorStop(0,'#87CEEB'); sky.addColorStop(1,'#A5D6A7');
    ctx.fillStyle = sky; ctx.fillRect(0,0,W,H);

    // Ground
    ctx.fillStyle = '#66BB6A'; ctx.fillRect(0, H*0.75, W, H*0.25);
    ctx.fillStyle = '#4CAF50'; ctx.fillRect(0, H*0.73, W, H*0.04);

    // Sun
    ctx.fillStyle = '#FFD700';
    ctx.beginPath(); ctx.arc(W*0.88, H*0.1, W*0.06, 0, Math.PI*2); ctx.fill();

    // House walls
    ctx.fillStyle = '#FFF9C4';
    ctx.strokeStyle = '#F9A825';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.roundRect(this.houseX, this.houseY, this.houseW, this.houseH, [0,0,8,8]);
    ctx.fill(); ctx.stroke();

    // Roof
    ctx.fillStyle = '#C62828';
    ctx.beginPath();
    ctx.moveTo(this.houseX - W*0.04, this.houseY);
    ctx.lineTo(W/2, this.houseY - H*0.16);
    ctx.lineTo(this.houseX + this.houseW + W*0.04, this.houseY);
    ctx.closePath(); ctx.fill();

    // Door
    ctx.fillStyle = '#8D6E63';
    ctx.beginPath();
    ctx.roundRect(W/2 - W*0.08, this.houseY + this.houseH*0.55, W*0.16, this.houseH*0.45, [8,8,0,0]);
    ctx.fill();
    ctx.fillStyle = '#FFD700';
    ctx.beginPath(); ctx.arc(W/2 + W*0.05, this.houseY + this.houseH*0.78, W*0.015, 0, Math.PI*2); ctx.fill();

    // Windows
    [[0.3, 0.4], [0.7, 0.4]].forEach(([wx, wy]) => {
      ctx.fillStyle = '#B3E5FC';
      ctx.strokeStyle = '#F9A825';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.roundRect(this.houseX + this.houseW*wx - W*0.06, this.houseY + this.houseH*wy - H*0.04, W*0.12, H*0.09, 4);
      ctx.fill(); ctx.stroke();
      // Cross
      ctx.strokeStyle = '#F9A825'; ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(this.houseX + this.houseW*wx, this.houseY + this.houseH*wy - H*0.04);
      ctx.lineTo(this.houseX + this.houseW*wx, this.houseY + this.houseH*wy + H*0.05);
      ctx.moveTo(this.houseX + this.houseW*wx - W*0.06, this.houseY + this.houseH*wy);
      ctx.lineTo(this.houseX + this.houseW*wx + W*0.06, this.houseY + this.houseH*wy);
      ctx.stroke();
    });

    // House outline (inside boundary visual)
    ctx.save();
    ctx.strokeStyle = 'rgba(255,215,0,0.4)';
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.roundRect(this.houseX+4, this.houseY+4, this.houseW-8, this.houseH-8, [0,0,6,6]);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.restore();

    // Objects
    const emojiSize = Math.round(W * 0.1);
    ctx.font = `${emojiSize}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    this._objects.forEach(obj => {
      ctx.save();
      // Glow effect for object type
      const pulse = 0.8 + Math.sin(this._animTime * 2 + this._objects.indexOf(obj)) * 0.15;
      ctx.globalAlpha = pulse;
      ctx.fillText(obj.emoji, obj.x, obj.y);

      // Label below
      ctx.globalAlpha = 0.8;
      ctx.font = `bold ${Math.round(W*0.032)}px Nunito,sans-serif`;
      ctx.fillStyle = 'rgba(0,0,0,0.75)';
      const bg = ctx.measureText(obj.label);
      ctx.fillStyle = 'rgba(255,255,255,0.85)';
      ctx.beginPath();
      ctx.roundRect(obj.x - bg.width/2 - 4, obj.y + emojiSize*0.45, bg.width + 8, 16, 4);
      ctx.fill();
      ctx.fillStyle = '#2C2C2C';
      ctx.font = `bold ${Math.round(W*0.032)}px Nunito,sans-serif`;
      ctx.fillText(obj.label, obj.x, obj.y + emojiSize*0.55);
      ctx.restore();
    });

    // Question prompt
    if (this._currentQuestion) {
      ctx.save();
      ctx.fillStyle = 'rgba(0,0,0,0.7)';
      ctx.beginPath();
      ctx.roundRect(W*0.04, H*0.88, W*0.92, H*0.1, 14);
      ctx.fill();
      ctx.fillStyle = 'white';
      ctx.font = `bold ${Math.min(16, W*0.042)}px Nunito,sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(this._currentQuestion.ask, W/2, H*0.933);
      ctx.restore();
    }

    // Round dots
    ctx.save();
    for (let i=0;i<this.totalRounds;i++) {
      ctx.beginPath();
      ctx.arc(W/2-(this.totalRounds-1)*12+i*24, H*0.04, 6, 0, Math.PI*2);
      ctx.fillStyle = i<this.round?'#4CAF50':i===this.round?'#FFD700':'rgba(255,255,255,0.4)';
      ctx.fill();
    }
    ctx.restore();

    // Feedback
    if (this._feedbackAlpha > 0) {
      ctx.save();
      ctx.globalAlpha = this._feedbackAlpha * 0.3;
      ctx.fillStyle = this._feedbackCorrect ? '#4CAF50' : '#F44336';
      ctx.fillRect(0,0,W,H);
      ctx.restore();
    }

    // Particles
    this._particles.forEach(p => {
      ctx.save(); ctx.globalAlpha = p.life; ctx.fillStyle = p.color;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.size*p.life, 0, Math.PI*2); ctx.fill(); ctx.restore();
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
    const stars = this.correctAnswers >= 3 ? 3 : this.correctAnswers >= 2 ? 2 : 1;
    if (this.onComplete) setTimeout(() => this.onComplete(stars), 600);
  }

  destroy() {
    this._running = false;
    if (this._raf) cancelAnimationFrame(this._raf);
    this.touch.destroy();
    window.removeEventListener('resize', this._resizeBound);
  }
}
