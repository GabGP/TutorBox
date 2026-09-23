// Module 4, Lesson 1: Count 1-9 with jocotes (tropical fruit)
// Jocote tree, tap to count, Maya dots + Arabic numerals

import audio from '../../engine/audio.js';
import { TouchHandler } from '../../engine/touch.js';

const COUNTING_WORDS = ['uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve'];

export default class Contar19Lesson {
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
    this._particles = [];
    this._jocotes = [];
    this._tappedCount = 0;
    this._targetCount = 0;
    this._jocoteAnimations = [];
    this._currentPhase = 'tap'; // 'tap' or 'answer'
    this._choices = [];
    this._feedbackAlpha = 0;
    this._feedbackCorrect = false;
    this._numberScale = 1;
    this._countDisplayScale = 1;

    this.touch = new TouchHandler(this.canvas);
    this.touch.onTap(pos => this._onTap(pos.x, pos.y));
    this._resizeBound = () => { this._resize(); this._setupJocotes(); };
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

  _setupJocotes() {
    const W = this.W, H = this.H;
    if (!W) return;
    const targets = [3, 5, 8];
    this._targetCount = targets[this.round] || 3;
    const jSize = Math.min(W * 0.065, 28);

    // Arrange jocotes on tree branches
    this._jocotes = [];
    const positions = this._getJocotePositions(W, H, this._targetCount);

    for (let i = 0; i < this._targetCount; i++) {
      this._jocotes.push({
        id: i,
        x: positions[i].x,
        y: positions[i].y,
        size: jSize,
        tapped: false,
        scale: 1,
        opacity: 1,
        phase: 'idle', // 'idle', 'bounce', 'glow'
        bounceT: 0,
        glowRadius: 0
      });
    }
    this._tappedCount = 0;
    this._currentPhase = 'tap';
    this._setupChoices();
  }

  _getJocotePositions(W, H, count) {
    // Distribute on tree branches
    const treeX = W / 2;
    const treeTopY = H * 0.12;
    const canopyR = W * 0.28;
    const positions = [];

    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 1.4 * i) / Math.max(count - 1, 1) - Math.PI * 0.7;
      const r = canopyR * (0.3 + Math.random() * 0.6);
      positions.push({
        x: treeX + Math.cos(angle) * r + (Math.random() - 0.5) * W * 0.05,
        y: treeTopY + canopyR * 0.5 + Math.sin(angle) * r * 0.6 + (Math.random() - 0.5) * H * 0.05
      });
    }
    return positions;
  }

  _setupChoices() {
    const target = this._targetCount;
    const wrong1 = target > 1 ? target - 1 : target + 1;
    const wrong2 = target < 9 ? target + 1 : target - 2;
    this._choices = [target, wrong1, wrong2].sort(() => Math.random() - 0.5);

    // Position choice buttons
    const W = this.W, H = this.H;
    const btnSize = Math.min(W * 0.22, 80);
    const total = this._choices.length;
    const startX = (W - total * (btnSize + 12) + 12) / 2;

    this._choiceBtns = this._choices.map((num, i) => ({
      x: startX + i * (btnSize + 12),
      y: H * 0.76,
      w: btnSize, h: btnSize,
      num,
      color: ['#E53935', '#1E88E5', '#43A047'][i]
    }));
  }

  _onTap(x, y) {
    if (this.isShowingFeedback) return;

    if (this._currentPhase === 'tap') {
      // Check jocote taps
      for (const joc of this._jocotes) {
        if (joc.tapped) continue;
        const dist = Math.hypot(x - joc.x, y - joc.y);
        if (dist < joc.size * 2) {
          joc.tapped = true;
          joc.phase = 'bounce';
          joc.bounceT = 0;
          this._tappedCount++;
          audio.playCount(this._tappedCount);
          audio.speak(COUNTING_WORDS[this._tappedCount - 1], { rate: 0.9 });
          this._countDisplayScale = 1.4;
          this._spawnTinyParticles(joc.x, joc.y);

          if (this._tappedCount >= this._targetCount) {
            this._currentPhase = 'answer';
            setTimeout(() => {
              audio.speak(`¿Cuántos jocotes contaste? ¡Toca el número!`, { rate: 0.8 });
            }, 500);
          }
          return;
        }
      }
    } else if (this._currentPhase === 'answer') {
      // Check answer buttons
      for (const btn of this._choiceBtns) {
        if (x >= btn.x && x <= btn.x + btn.w && y >= btn.y && y <= btn.y + btn.h) {
          const correct = btn.num === this._targetCount;
          this._showFeedback(correct, btn.x + btn.w/2, btn.y + btn.h/2);
          return;
        }
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
      audio.speak(`¡Correcto! ¡${COUNTING_WORDS[this._targetCount-1].charAt(0).toUpperCase() + COUNTING_WORDS[this._targetCount-1].slice(1)}!`, { rate: 0.9 });
      this._spawnParticles(x, y);
    } else {
      this._missed = true;
      audio.playError();
      audio.speak('¡Casi! Cuenta los jocotes otra vez, uno por uno.', { rate: 0.85 });
    }
    setTimeout(() => {
      this.isShowingFeedback = false;
      this._feedbackAlpha = 0;
      if (!correct) return; // same question again until it is right
      this.round++;
      if (this.round >= this.totalRounds) this._finish();
      else this._setupJocotes();
    }, correct ? 1300 : 1000);
  }

  _spawnParticles(x, y) {
    for (let i=0;i<14;i++) {
      const a=(Math.PI*2*i)/14; const sp=3+Math.random()*4;
      this._particles.push({x,y,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp-2,life:1,color:['#FFD700','#FF6F00','#4CAF50','#E91E63'][i%4],size:7+Math.random()*7});
    }
  }

  _spawnTinyParticles(x, y) {
    for (let i=0;i<6;i++) {
      const a=(Math.PI*2*i)/6; const sp=2+Math.random()*2;
      this._particles.push({x,y,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp-1,life:0.8,color:'#FFD700',size:4+Math.random()*4});
    }
  }

  start() {
    this._resize();
    this._setupJocotes();
    this._running = true;
    this._lastTime = performance.now();
    this._loop();
    setTimeout(() => audio.speak('¡Toca los jocotes para contarlos!', { rate: 0.8 }), 700);
  }

  update(dt) {
    this._animTime += dt * 0.001;
    this._countDisplayScale = Math.max(1, this._countDisplayScale - dt * 0.003);

    this._jocotes.forEach(joc => {
      if (joc.phase === 'bounce') {
        joc.bounceT = Math.min(1, joc.bounceT + dt * 0.006);
        joc.scale = 1 + Math.sin(joc.bounceT * Math.PI) * 0.5;
        joc.glowRadius = Math.sin(joc.bounceT * Math.PI) * 20;
        if (joc.bounceT >= 1) { joc.phase = 'glow'; joc.scale = 1; }
      }
      if (joc.phase === 'glow') {
        joc.glowRadius = Math.max(0, joc.glowRadius - dt * 0.04);
      }
    });

    this._particles = this._particles.filter(p => {
      p.x += p.vx; p.y += p.vy; p.vy += 0.25; p.life -= dt * 0.0025; return p.life > 0;
    });
  }

  render() {
    const ctx = this.ctx; const W = this.W; const H = this.H;
    if (!W || !H) return;
    ctx.clearRect(0, 0, W, H);

    // Sky + ground
    const sky = ctx.createLinearGradient(0,0,0,H);
    sky.addColorStop(0,'#87CEEB'); sky.addColorStop(0.65,'#AED581'); sky.addColorStop(1,'#8D6E63');
    ctx.fillStyle = sky; ctx.fillRect(0,0,W,H);
    ctx.fillStyle = '#6D4C41'; ctx.fillRect(0,H*0.72,W,H*0.28);
    ctx.fillStyle = '#4CAF50'; ctx.fillRect(0,H*0.7,W,H*0.04);

    // ── Jocote Tree ────────────────────────────────────────────────────────
    const treeX = W/2;
    const trunkTop = H*0.42;
    const trunkBot = H*0.7;
    const trunkW = W*0.06;
    const canopyR = W*0.28;
    const canopyY = H*0.22;

    // Trunk
    ctx.fillStyle = '#5D4037';
    ctx.beginPath(); ctx.roundRect(treeX-trunkW/2, trunkTop, trunkW, trunkBot-trunkTop, 4); ctx.fill();

    // Canopy layers
    [['#1B5E20',canopyY+14,canopyR],['#2E7D32',canopyY-4,canopyR*0.9],
     ['#388E3C',canopyY-20,canopyR*0.75],['#4CAF50',canopyY-32,canopyR*0.58]].forEach(([c,y,r]) => {
      ctx.fillStyle = c;
      ctx.beginPath(); ctx.ellipse(treeX, y, r, r*0.72, 0, 0, Math.PI*2); ctx.fill();
    });

    // Ground roots
    ctx.strokeStyle = '#4E342E'; ctx.lineWidth = 3;
    [[-1,0.7],[1,0.75]].forEach(([dir,t]) => {
      ctx.beginPath();
      ctx.moveTo(treeX, trunkBot);
      ctx.quadraticCurveTo(treeX+dir*trunkW*2, trunkBot+H*0.02, treeX+dir*trunkW*3, trunkBot-H*0.02);
      ctx.stroke();
    });

    // ── Jocotes ────────────────────────────────────────────────────────────
    this._jocotes.forEach((joc, idx) => {
      ctx.save();
      const bob = !joc.tapped ? Math.sin(this._animTime*2 + idx*0.8)*3 : 0;

      // Glow for tapped jocotes
      if (joc.glowRadius > 0) {
        ctx.shadowColor = '#FFD700';
        ctx.shadowBlur = joc.glowRadius;
      }

      // Draw jocote (small red/orange tropical fruit)
      const jx = joc.x, jy = joc.y + bob;
      const s = joc.size * joc.scale;

      // Fruit body
      ctx.fillStyle = joc.tapped ? '#FFD700' : '#D32F2F';
      ctx.beginPath(); ctx.ellipse(jx, jy, s, s*1.1, 0, 0, Math.PI*2); ctx.fill();

      // Highlight
      ctx.fillStyle = joc.tapped ? 'rgba(255,255,255,0.5)' : 'rgba(255,255,255,0.35)';
      ctx.beginPath(); ctx.ellipse(jx-s*0.25, jy-s*0.3, s*0.3, s*0.2, -0.5, 0, Math.PI*2); ctx.fill();

      // Stem
      ctx.strokeStyle = '#2E7D32'; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(jx, jy-s); ctx.lineTo(jx+s*0.1, jy-s*1.4); ctx.stroke();

      // Number for counted jocotes
      if (joc.tapped) {
        ctx.fillStyle = '#1A237E';
        ctx.font = `bold ${Math.round(s*0.9)}px Nunito,sans-serif`;
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(String(idx+1), jx, jy);
      }

      ctx.restore();
    });

    // ── Count display (big number + Maya dots) ─────────────────────────────
    if (this._tappedCount > 0) {
      ctx.save();
      const numScale = this._countDisplayScale;
      const numX = W*0.85; const numY = H*0.5;

      ctx.shadowColor = 'rgba(0,0,0,0.3)'; ctx.shadowBlur = 8;
      ctx.fillStyle = 'rgba(0,0,0,0.6)';
      ctx.beginPath();
      ctx.roundRect(numX-W*0.12, numY-H*0.1, W*0.24, H*0.2, 14);
      ctx.fill();

      // Big number
      ctx.font = `bold ${Math.round(W*0.14*numScale)}px Nunito,sans-serif`;
      ctx.fillStyle = '#FFD700';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(String(this._tappedCount), numX, numY-H*0.02);

      // Maya dot system
      this._drawMayaDots(ctx, numX, numY+H*0.06, this._tappedCount, W*0.03);

      ctx.restore();
    }

    // ── Instruction text ───────────────────────────────────────────────────
    ctx.save();
    const instrText = this._currentPhase === 'tap'
      ? `¡Toca ${this._targetCount} jocotes! (${this._tappedCount}/${this._targetCount})`
      : '¿Cuántos contaste? ¡Toca el número!';
    ctx.fillStyle = 'rgba(0,0,0,0.65)';
    ctx.beginPath(); ctx.roundRect(W*0.04,H*0.88,W*0.92,H*0.1,12); ctx.fill();
    ctx.fillStyle = 'white'; ctx.font = `bold ${Math.min(15,W*0.04)}px Nunito,sans-serif`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(instrText, W/2, H*0.933);
    ctx.restore();

    // ── Answer choice buttons ──────────────────────────────────────────────
    if (this._currentPhase === 'answer' && this._choiceBtns) {
      this._choiceBtns.forEach((btn, i) => {
        ctx.save();
        const pulse = 1 + Math.sin(this._animTime*2.5+i)*0.04;
        ctx.shadowColor = 'rgba(0,0,0,0.35)'; ctx.shadowBlur = 10;
        ctx.fillStyle = btn.color;
        ctx.beginPath();
        ctx.roundRect(btn.x+(btn.w*(1-pulse))/2, btn.y+(btn.h*(1-pulse))/2, btn.w*pulse, btn.h*pulse, 14);
        ctx.fill();
        ctx.strokeStyle = 'rgba(255,255,255,0.5)'; ctx.lineWidth = 2; ctx.shadowBlur=0; ctx.stroke();

        // Large number
        ctx.fillStyle = 'white'; ctx.font = `bold ${Math.round(btn.h*0.55*pulse)}px Nunito,sans-serif`;
        ctx.textAlign='center'; ctx.textBaseline='middle';
        ctx.fillText(String(btn.num), btn.x+btn.w/2, btn.y+btn.h*0.42);

        // Dots under number
        this._drawMayaDots(ctx, btn.x+btn.w/2, btn.y+btn.h*0.78, btn.num, btn.h*0.07);
        ctx.restore();
      });
    }

    // Round dots
    ctx.save();
    for (let i=0;i<this.totalRounds;i++) {
      ctx.beginPath(); ctx.arc(W/2-(this.totalRounds-1)*12+i*24, H*0.04, 6, 0, Math.PI*2);
      ctx.fillStyle = i<this.round?'#4CAF50':i===this.round?'#FFD700':'rgba(255,255,255,0.4)'; ctx.fill();
    }
    ctx.restore();

    // Feedback
    if (this._feedbackAlpha>0) {
      ctx.save(); ctx.globalAlpha=this._feedbackAlpha*0.3;
      ctx.fillStyle=this._feedbackCorrect?'#4CAF50':'#F44336';
      ctx.fillRect(0,0,W,H); ctx.restore();
    }

    // Particles
    this._particles.forEach(p=>{
      ctx.save(); ctx.globalAlpha=p.life; ctx.fillStyle=p.color;
      ctx.beginPath(); ctx.arc(p.x,p.y,p.size*p.life,0,Math.PI*2); ctx.fill(); ctx.restore();
    });
  }

  _drawMayaDots(ctx, cx, cy, n, dotSize) {
    // Maya vigesimal: groups of 5 (bar=5, dot=1)
    ctx.save();
    const bars = Math.floor(n / 5);
    const dots = n % 5;
    let xOffset = cx - (Math.max(dots, 4) * (dotSize*1.8)) / 2;

    // Draw dots
    for (let i=0;i<dots;i++) {
      ctx.fillStyle = 'rgba(255,255,255,0.9)';
      ctx.beginPath(); ctx.arc(xOffset + i*(dotSize*1.8)+dotSize, cy, dotSize, 0, Math.PI*2); ctx.fill();
    }
    // Draw bars
    for (let b=0;b<bars;b++) {
      ctx.fillStyle = 'rgba(255,255,255,0.9)';
      ctx.fillRect(cx-dotSize*3, cy+(b*dotSize*2.5)+(dots>0?dotSize*2.5:0), dotSize*6, dotSize*0.8);
    }
    ctx.restore();
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
