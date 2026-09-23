// Module 6, Lesson 1: Shape Identification in Antigua Guatemala streetscape
// Canvas scene with buildings, child taps shapes of the requested type

import audio from '../../engine/audio.js';
import { TouchHandler } from '../../engine/touch.js';

export default class IdentificarFormasLesson {
  constructor(canvasId, config = {}) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.onComplete = config.onComplete || (() => {});
    this.totalRounds = 3;
    this.round = 0;
    this.correctAnswers = 0;
    this.errors = 0;
    this.isShowingFeedback = false;
    this._animTime = 0;
    this._running = false;
    this._raf = null;
    this._lastTime = null;
    this._particles = [];
    this._shapes = [];
    this._targetShape = null;
    this._foundShapes = new Set();
    this._feedbackAlpha = 0;
    this._feedbackCorrect = false;
    this._shakeShape = null;
    this._shakeT = 0;

    this.touch = new TouchHandler(this.canvas);
    this.touch.onTap(pos => this._onTap(pos.x, pos.y));
    this._resizeBound = () => { this._resize(); this._buildScene(); };
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

  _buildScene() {
    const W = this.W, H = this.H;
    if (!W) return;

    // Build all clickable shapes in the Antigua scene
    this._shapes = [
      // Circles: windows, sun, wheel, fountain
      { id: 'c1', type: 'circle', x: W*0.18, y: H*0.38, r: W*0.045, found: false },
      { id: 'c2', type: 'circle', x: W*0.52, y: H*0.34, r: W*0.04, found: false },
      { id: 'c3', type: 'circle', x: W*0.82, y: H*0.4, r: W*0.038, found: false },

      // Triangles: rooftops, volcano
      { id: 't1', type: 'triangle', x: W*0.12, y: H*0.22, r: W*0.065, found: false },
      { id: 't2', type: 'triangle', x: W*0.5, y: H*0.18, r: W*0.07, found: false },
      { id: 't3', type: 'triangle', x: W*0.85, y: H*0.2, r: W*0.06, found: false },

      // Rectangles: doors, windows
      { id: 'r1', type: 'rect', x: W*0.22, y: H*0.55, w: W*0.1, h: H*0.14, found: false },
      { id: 'r2', type: 'rect', x: W*0.55, y: H*0.52, w: W*0.12, h: H*0.1, found: false },
      { id: 'r3', type: 'rect', x: W*0.78, y: H*0.56, w: W*0.09, h: H*0.12, found: false },
    ];
  }

  _setupRound() {
    const shapeTypes = ['circle', 'triangle', 'rect'];
    const shapeNames = { circle: 'círculos', triangle: 'triángulos', rect: 'rectángulos' };
    const shapeEmojis = { circle: '⭕', triangle: '🔺', rect: '▭' };
    const shapeNarrations = {
      circle: '¡Encuentra todos los círculos! Son redondos.',
      triangle: '¡Busca todos los triángulos! Tienen 3 lados.',
      rect: '¡Encuentra todos los rectángulos! Tienen 4 lados.'
    };

    this._targetShape = shapeTypes[this.round % 3];
    this._targetName = shapeNames[this._targetShape];
    this._targetEmoji = shapeEmojis[this._targetShape];
    this._foundShapes = new Set();
    this._totalTarget = this._shapes.filter(s => s.type === this._targetShape).length;

    // Reset all shapes
    this._shapes.forEach(s => { s.found = false; s.glowT = 0; });

    setTimeout(() => {
      audio.speak(shapeNarrations[this._targetShape], { rate: 0.8 });
    }, 400);
  }

  _onTap(x, y) {
    if (this.isShowingFeedback) return;

    for (const shape of this._shapes) {
      if (shape.found) continue;
      const hit = this._hitTest(shape, x, y);
      if (hit) {
        if (shape.type === this._targetShape) {
          shape.found = true;
          shape.glowT = 1;
          this._foundShapes.add(shape.id);
          this.correctAnswers++;
          audio.playSuccess();
          this._spawnParticles(x, y);

          if (this._foundShapes.size >= this._totalTarget) {
            audio.speak('¡Encontraste todos! ¡Excelente!', { rate: 0.9 });
            setTimeout(() => {
              this.round++;
              if (this.round >= this.totalRounds) this._finish();
              else this._setupRound();
            }, 1200);
          } else {
            audio.speak('¡Bien! ¡Busca más!', { rate: 0.9 });
          }
        } else {
          // Wrong shape type
          this.errors++;
          this._shakeShape = shape;
          this._shakeT = 1;
          audio.playError();
          audio.speak('¡Ese no es! ¡Busca un ' + this._targetName.slice(0, -1) + '!', { rate: 0.85 });
          this._feedbackCorrect = false;
          this._feedbackAlpha = 0.3;
          setTimeout(() => this._feedbackAlpha = 0, 500);
        }
        return;
      }
    }
  }

  _hitTest(shape, x, y) {
    if (shape.type === 'circle') {
      return Math.hypot(x - shape.x, y - shape.y) < shape.r * 1.8;
    }
    if (shape.type === 'triangle') {
      return Math.hypot(x - shape.x, y - shape.y) < shape.r * 1.6;
    }
    if (shape.type === 'rect') {
      return x >= shape.x - shape.w*0.2 && x <= shape.x + shape.w*1.2 &&
             y >= shape.y - shape.h*0.2 && y <= shape.y + shape.h*1.2;
    }
    return false;
  }

  _spawnParticles(x, y) {
    for (let i=0;i<12;i++) {
      const a=(Math.PI*2*i)/12; const sp=3+Math.random()*4;
      this._particles.push({x,y,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp-2,life:1,color:['#FFD700','#4CAF50','#2196F3'][i%3],size:6+Math.random()*7});
    }
  }

  start() {
    this._resize();
    this._buildScene();
    this._running = true;
    this._lastTime = performance.now();
    this._setupRound();
    this._loop();
    setTimeout(() => audio.speak('¡Mira la Antigua Guatemala! ¿Puedes encontrar las formas?', { rate: 0.8 }), 600);
  }

  update(dt) {
    this._animTime += dt * 0.001;
    if (this._shakeT > 0) this._shakeT = Math.max(0, this._shakeT - dt * 0.006);
    this._shapes.forEach(s => { if (s.glowT) s.glowT = Math.max(0, s.glowT - dt * 0.001); });
    this._particles = this._particles.filter(p => {
      p.x += p.vx; p.y += p.vy; p.vy += 0.25; p.life -= dt * 0.002; return p.life > 0;
    });
  }

  render() {
    const ctx = this.ctx; const W = this.W; const H = this.H;
    if (!W || !H) return;
    ctx.clearRect(0,0,W,H);

    // Sky
    const sky = ctx.createLinearGradient(0,0,0,H*0.5);
    sky.addColorStop(0,'#4FC3F7'); sky.addColorStop(1,'#B3E5FC');
    ctx.fillStyle=sky; ctx.fillRect(0,0,W,H*0.5);

    // Ground
    ctx.fillStyle='#8D6E63'; ctx.fillRect(0,H*0.65,W,H*0.35);
    ctx.fillStyle='#795548'; ctx.fillRect(0,H*0.62,W,H*0.05);

    // Cobblestone street
    ctx.fillStyle='#9E9E9E';
    for (let row=0;row<3;row++) for (let col=0;col<8;col++) {
      ctx.beginPath();
      ctx.roundRect(W*0.04+col*W*0.12+(row%2?W*0.06:0),H*0.67+row*H*0.055,W*0.1,H*0.045,3);
      ctx.fill();
      ctx.strokeStyle='#757575'; ctx.lineWidth=0.5; ctx.stroke();
    }

    // ── Buildings ──────────────────────────────────────────────────────────
    // Building 1 (left)
    ctx.fillStyle='#FFF9C4';
    ctx.fillRect(W*0.02,H*0.3,W*0.28,H*0.35);
    ctx.fillStyle='#F9A825'; ctx.lineWidth=2; ctx.strokeStyle='#F57F17';
    ctx.strokeRect(W*0.02,H*0.3,W*0.28,H*0.35);

    // Building 2 (center)
    ctx.fillStyle='#FFCCBC';
    ctx.fillRect(W*0.32,H*0.26,W*0.36,H*0.39);
    ctx.strokeStyle='#E64A19'; ctx.strokeRect(W*0.32,H*0.26,W*0.36,H*0.39);

    // Building 3 (right)
    ctx.fillStyle='#E8F5E9';
    ctx.fillRect(W*0.7,H*0.3,W*0.28,H*0.35);
    ctx.strokeStyle='#388E3C'; ctx.strokeRect(W*0.7,H*0.3,W*0.28,H*0.35);

    // ── Interactive Shapes (drawn over buildings) ─────────────────────────
    this._shapes.forEach(shape => {
      const isTarget = shape.type === this._targetShape;
      const isShaking = this._shakeShape === shape && this._shakeT > 0;
      const shakeX = isShaking ? Math.sin(this._shakeT * 20) * 5 : 0;

      ctx.save();
      ctx.translate(shakeX, 0);

      if (shape.found) {
        ctx.shadowColor = '#4CAF50';
        ctx.shadowBlur = 18 + Math.sin(this._animTime * 4) * 6;
      } else if (isTarget) {
        ctx.shadowColor = '#FFD700';
        ctx.shadowBlur = 4 + Math.sin(this._animTime * 3) * 3;
      }

      if (shape.type === 'circle') {
        ctx.fillStyle = shape.found ? '#A5D6A7' : '#B3E5FC';
        ctx.strokeStyle = shape.found ? '#4CAF50' : '#1976D2';
        ctx.lineWidth = shape.found ? 3 : 2;
        ctx.beginPath(); ctx.arc(shape.x, shape.y, shape.r, 0, Math.PI*2); ctx.fill(); ctx.stroke();
        // Window cross
        if (!shape.found) {
          ctx.strokeStyle='rgba(25,118,210,0.5)'; ctx.lineWidth=1.5;
          ctx.beginPath(); ctx.moveTo(shape.x-shape.r,shape.y); ctx.lineTo(shape.x+shape.r,shape.y); ctx.stroke();
          ctx.beginPath(); ctx.moveTo(shape.x,shape.y-shape.r); ctx.lineTo(shape.x,shape.y+shape.r); ctx.stroke();
        }
      } else if (shape.type === 'triangle') {
        ctx.fillStyle = shape.found ? '#A5D6A7' : '#C62828';
        ctx.strokeStyle = shape.found ? '#4CAF50' : '#8B0000';
        ctx.lineWidth = shape.found ? 3 : 2;
        ctx.beginPath();
        ctx.moveTo(shape.x, shape.y - shape.r);
        ctx.lineTo(shape.x + shape.r * 1.1, shape.y + shape.r * 0.7);
        ctx.lineTo(shape.x - shape.r * 1.1, shape.y + shape.r * 0.7);
        ctx.closePath(); ctx.fill(); ctx.stroke();
      } else if (shape.type === 'rect') {
        ctx.fillStyle = shape.found ? '#A5D6A7' : '#8D6E63';
        ctx.strokeStyle = shape.found ? '#4CAF50' : '#5D4037';
        ctx.lineWidth = shape.found ? 3 : 2;
        ctx.beginPath(); ctx.roundRect(shape.x, shape.y, shape.w, shape.h, 4); ctx.fill(); ctx.stroke();
        // Door knob
        if (!shape.found) {
          ctx.fillStyle='#FFD700';
          ctx.beginPath(); ctx.arc(shape.x+shape.w*0.8, shape.y+shape.h*0.5, shape.w*0.08, 0, Math.PI*2); ctx.fill();
        }
      }

      if (shape.found) {
        ctx.fillStyle='#4CAF50'; ctx.font=`bold ${Math.round(W*0.05)}px sans-serif`;
        ctx.textAlign='center'; ctx.textBaseline='middle';
        ctx.fillText('✓', shape.type==='rect'?shape.x+shape.w/2:shape.x, shape.type==='rect'?shape.y+shape.h/2:shape.y);
      }
      ctx.restore();
    });

    // ── HUD - Current target shape ────────────────────────────────────────
    ctx.save();
    ctx.fillStyle='rgba(0,0,0,0.7)';
    ctx.beginPath(); ctx.roundRect(W*0.04,H*0.03,W*0.92,H*0.12,14); ctx.fill();

    ctx.fillStyle='white'; ctx.font=`bold ${Math.min(16,W*0.043)}px Nunito,sans-serif`;
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText(`¡Toca todos los ${this._targetName}! (${this._foundShapes.size}/${this._totalTarget})`, W/2, H*0.09);

    // Shape icon indicator
    const iconX = W*0.85; const iconY = H*0.09;
    const pulse = 1+Math.sin(this._animTime*3)*0.1;
    ctx.font=`${Math.round(W*0.08*pulse)}px sans-serif`;
    ctx.fillText(this._targetEmoji, iconX, iconY);
    ctx.restore();

    // Round dots
    ctx.save();
    for (let i=0;i<this.totalRounds;i++) {
      ctx.beginPath(); ctx.arc(W/2-(this.totalRounds-1)*12+i*24,H*0.88,6,0,Math.PI*2);
      ctx.fillStyle=i<this.round?'#4CAF50':i===this.round?'#FFD700':'rgba(255,255,255,0.4)'; ctx.fill();
    }
    ctx.restore();

    if (this._feedbackAlpha>0) {
      ctx.save(); ctx.globalAlpha=this._feedbackAlpha*0.3;
      ctx.fillStyle=this._feedbackCorrect?'#4CAF50':'#F44336'; ctx.fillRect(0,0,W,H); ctx.restore();
    }
    this._particles.forEach(p=>{
      ctx.save(); ctx.globalAlpha=p.life; ctx.fillStyle=p.color;
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
    const accuracy = this.correctAnswers / (this.correctAnswers + this.errors);
    const stars = accuracy >= 0.85 ? 3 : accuracy >= 0.6 ? 2 : 1;
    if (this.onComplete) setTimeout(() => this.onComplete(stars), 600);
  }

  destroy() {
    this._running = false;
    if (this._raf) cancelAnimationFrame(this._raf);
    this.touch.destroy();
    window.removeEventListener('resize', this._resizeBound);
  }
}
