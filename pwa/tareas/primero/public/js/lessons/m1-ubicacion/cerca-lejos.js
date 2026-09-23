// Module 1, Lesson 3: Cerca y Lejos (Near and Far)
import audio from '../../engine/audio.js';
import { TouchHandler } from '../../engine/touch.js';

export default class CercaLejosLesson {
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
    this._setupRound();
    this._loop();
    setTimeout(() => audio.speak('¡Mira! ¿Cuál está cerca y cuál está lejos?', { rate: 0.8 }), 600);
  }

  _getSceneObjects() {
    const W = this.W, H = this.H;
    return [
      // Near objects (big, bottom of screen)
      { id: 'close_bird', emoji: '🐦', x: W*0.25, y: H*0.68, scale: 1.4, isClose: true, label: 'pájaro' },
      { id: 'close_flower', emoji: '🌺', x: W*0.6, y: H*0.72, scale: 1.4, isClose: true, label: 'flor' },
      // Far objects (small, top of screen)
      { id: 'far_mountain', emoji: '⛰️', x: W*0.2, y: H*0.3, scale: 0.6, isClose: false, label: 'montaña' },
      { id: 'far_tree', emoji: '🌲', x: W*0.75, y: H*0.28, scale: 0.6, isClose: false, label: 'árbol' }
    ];
  }

  _setupRound() {
    const questions = [
      { narration: '¿Qué está CERCA de ti? ¡Tócalo!', ask: '¿Qué está cerca? ¡Toca el grande!', correctProp: true },
      { narration: '¿Qué está LEJOS? ¡Toca lo que está lejos!', ask: '¿Qué está lejos? ¡Toca el pequeño!', correctProp: false },
      { narration: '¿El pájaro está cerca o lejos?', ask: '¿El pájaro está cerca? ¡Tócalo!', targetId: 'close_bird', correctProp: true }
    ];
    this._currentQuestion = questions[this.round];
    setTimeout(() => audio.speak(this._currentQuestion.narration, { rate: 0.8 }), 400);
  }

  _onTap(x, y) {
    if (this.isShowingFeedback) return;
    const objects = this._getSceneObjects();
    const W = this.W;
    const hitSize = W * 0.12;
    for (const obj of objects) {
      if (Math.abs(x - obj.x) < hitSize * obj.scale && Math.abs(y - obj.y) < hitSize * obj.scale) {
        const q = this._currentQuestion;
        let correct;
        if (q.targetId) correct = obj.id === q.targetId;
        else correct = obj.isClose === q.correctProp;
        this._showFeedback(correct, x, y);
        return;
      }
    }
  }

  _showFeedback(correct, x, y) {
    this.isShowingFeedback = true;
    this._feedbackCorrect = correct;
    this._feedbackAlpha = 0.5;
    if (correct) { this.correctAnswers++; audio.playSuccess(); audio.speak('¡Correcto! ¡Muy bien!'); this._spawnParticles(x, y); }
    else { audio.playError(); audio.speak('¡Inténtalo de nuevo!'); }
    setTimeout(() => {
      this.isShowingFeedback = false; this._feedbackAlpha = 0;
      this.round++;
      if (this.round >= this.totalRounds) this._finish();
      else this._setupRound();
    }, correct ? 1200 : 900);
  }

  _spawnParticles(x, y) {
    const colors = ['#FFD700', '#FF6F00', '#4CAF50', '#E91E63'];
    for (let i = 0; i < 10; i++) {
      const a = (Math.PI * 2 * i) / 10;
      const sp = 3 + Math.random() * 3;
      this._particles.push({ x, y, vx: Math.cos(a)*sp, vy: Math.sin(a)*sp-1, life:1, color:colors[i%4], size:5+Math.random()*5 });
    }
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
    ctx.clearRect(0,0,W,H);

    // Sky gradient with depth
    const sky = ctx.createLinearGradient(0,0,0,H*0.7);
    sky.addColorStop(0,'#4FC3F7'); sky.addColorStop(1,'#B3E5FC');
    ctx.fillStyle = sky; ctx.fillRect(0,0,W,H*0.7);

    // Ground
    ctx.fillStyle = '#66BB6A'; ctx.fillRect(0,H*0.7,W,H*0.3);
    ctx.fillStyle = '#4CAF50'; ctx.fillRect(0,H*0.68,W,H*0.04);

    // Far mountains (background)
    [0.15, 0.5, 0.82].forEach((mx, i) => {
      const h = H*0.2 + i*H*0.03;
      ctx.fillStyle = `rgba(100,120,180,${0.4-i*0.1})`;
      ctx.beginPath();
      ctx.moveTo(W*mx - W*0.15, H*0.55);
      ctx.lineTo(W*mx, H*0.35 - i*H*0.03);
      ctx.lineTo(W*mx + W*0.15, H*0.55);
      ctx.closePath(); ctx.fill();
    });

    // Path showing near-far perspective
    const pathGrad = ctx.createLinearGradient(W/2, H*0.5, W/2, H*0.9);
    pathGrad.addColorStop(0,'rgba(139,90,43,0.5)'); pathGrad.addColorStop(1,'rgba(139,90,43,0.9)');
    ctx.fillStyle = pathGrad;
    ctx.beginPath();
    ctx.moveTo(W*0.42, H*0.5);
    ctx.lineTo(W*0.58, H*0.5);
    ctx.lineTo(W*0.75, H*0.9);
    ctx.lineTo(W*0.25, H*0.9);
    ctx.closePath(); ctx.fill();

    // Objects
    const objects = this._getSceneObjects();
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    objects.forEach(obj => {
      const emojiSz = Math.round(W * 0.1 * obj.scale);
      ctx.font = `${emojiSz}px sans-serif`;
      ctx.save();
      ctx.globalAlpha = 0.85 + Math.sin(this._animTime * 1.5 + objects.indexOf(obj)) * 0.1;
      ctx.fillText(obj.emoji, obj.x, obj.y);
      // Label
      ctx.font = `bold ${Math.round(W*0.03*obj.scale)}px Nunito,sans-serif`;
      ctx.globalAlpha = 0.85;
      ctx.fillStyle = 'rgba(255,255,255,0.9)';
      const bw = ctx.measureText(obj.label).width + 8;
      ctx.beginPath();
      ctx.roundRect(obj.x-bw/2, obj.y+emojiSz*0.5, bw, 14*obj.scale, 4);
      ctx.fill();
      ctx.fillStyle = '#2C2C2C';
      ctx.fillText(obj.label, obj.x, obj.y+emojiSz*0.57+7*obj.scale);
      ctx.restore();
    });

    // Question
    if (this._currentQuestion) {
      ctx.save();
      ctx.fillStyle = 'rgba(0,0,0,0.7)';
      ctx.beginPath(); ctx.roundRect(W*0.04,H*0.88,W*0.92,H*0.1,14); ctx.fill();
      ctx.fillStyle = 'white';
      ctx.font = `bold ${Math.min(16,W*0.042)}px Nunito,sans-serif`;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(this._currentQuestion.ask, W/2, H*0.933);
      ctx.restore();
    }

    // Labels CERCA / LEJOS
    ctx.save();
    ctx.font = `bold ${Math.round(W*0.05)}px Nunito,sans-serif`;
    ctx.textAlign = 'left';
    ctx.fillStyle = 'rgba(255,255,255,0.85)';
    ctx.fillText('CERCA ▼', W*0.04, H*0.84);
    ctx.fillText('LEJOS ▲', W*0.04, H*0.25);
    ctx.restore();

    // Round dots
    ctx.save();
    for (let i=0;i<this.totalRounds;i++) {
      ctx.beginPath(); ctx.arc(W/2-(this.totalRounds-1)*12+i*24, H*0.04, 6, 0, Math.PI*2);
      ctx.fillStyle = i<this.round?'#4CAF50':i===this.round?'#FFD700':'rgba(255,255,255,0.4)'; ctx.fill();
    }
    ctx.restore();

    if (this._feedbackAlpha > 0) {
      ctx.save(); ctx.globalAlpha = this._feedbackAlpha * 0.3;
      ctx.fillStyle = this._feedbackCorrect ? '#4CAF50' : '#F44336';
      ctx.fillRect(0,0,W,H); ctx.restore();
    }
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
