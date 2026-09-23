// Module 5, Lesson 1: Word Problem - María's Chickens
// Audio narration + visual chickens walking in, child counts and answers

import audio from '../../engine/audio.js';
import { TouchHandler } from '../../engine/touch.js';

export default class ProblemaGallinasLesson {
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
    this._chickens = [];
    this._phase = 'narrate'; // narrate -> count -> answer
    this._narrateStep = 0;
    this._narrateTimer = 0;
    this._choices = [];
    this._choiceBtns = [];
    this._feedbackAlpha = 0;
    this._feedbackCorrect = false;
    this._countHighlighted = [];
    this._problem = null;

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

  _getProblems() {
    return [
      { a: 3, b: 2, op: 'add', answer: 5, choices: [4, 5, 6], narration1: 'María tiene 3 gallinas.', narration2: '¡Le regalan 2 gallinas más!', question: '¿Cuántas gallinas tiene María ahora?' },
      { a: 4, b: 1, op: 'add', answer: 5, choices: [3, 5, 6], narration1: 'Don Pedro tiene 4 pollitos.', narration2: 'Nace 1 pollito más.', question: '¿Cuántos pollitos hay ahora?' },
      { a: 6, b: 3, op: 'sub', answer: 3, choices: [2, 3, 4], narration1: 'Hay 6 gallinas en el corral.', narration2: 'Se van 3 gallinas al campo.', question: '¿Cuántas gallinas quedan?' }
    ];
  }

  _setupRound() {
    const problems = this._getProblems();
    this._problem = problems[this.round];
    this._chickens = [];
    this._phase = 'narrate';
    this._narrateStep = 0;
    this._narrateTimer = 0;
    this._countHighlighted = [];

    // Create initial chickens
    this._spawnChickens(this._problem.a, 0);

    // Answer choices
    const p = this._problem;
    this._choices = [...p.choices].sort(() => Math.random() - 0.5);
    this._buildChoiceBtns();

    setTimeout(() => audio.speak(this._problem.narration1, { rate: 0.8 }), 600);
  }

  _spawnChickens(count, startIndex) {
    const W = this.W, H = this.H;
    const cols = Math.min(count, 4);
    const rows = Math.ceil(count / cols);
    const spacing = W * 0.18;
    const startX = W/2 - (cols-1)*spacing/2;

    for (let i = 0; i < count; i++) {
      const col = i % cols;
      const row = Math.floor(i / cols);
      const finalX = startX + col * spacing;
      const finalY = H * 0.55 - row * H * 0.1;
      const fromRight = this._problem.op === 'sub';
      this._chickens.push({
        id: startIndex + i,
        x: fromRight ? W * 1.2 + i * 60 : -W * 0.2 - i * 60,
        y: finalY,
        targetX: finalX,
        targetY: finalY,
        size: W * 0.06,
        color: `hsl(${40 + i * 15}, 70%, ${50 + (i%3)*10}%)`,
        walkPhase: Math.random() * Math.PI * 2,
        isLeaving: false,
        leaveProgress: 0,
        tapped: false,
        highlighted: false,
        arrived: false
      });
    }
  }

  _buildChoiceBtns() {
    const W = this.W, H = this.H;
    const btnSize = Math.min(W * 0.22, 78);
    const total = this._choices.length;
    const startX = (W - total * (btnSize + 12) + 12) / 2;

    this._choiceBtns = this._choices.map((num, i) => ({
      x: startX + i * (btnSize + 12),
      y: H * 0.78,
      w: btnSize, h: btnSize,
      num,
      color: ['#E53935', '#1E88E5', '#43A047'][i]
    }));
  }

  _onTap(x, y) {
    if (this.isShowingFeedback) return;

    if (this._phase === 'count') {
      // Tap chickens to count them
      for (const ch of this._chickens) {
        if (!ch.isLeaving && !ch.tapped) {
          const dist = Math.hypot(x - ch.x, y - ch.y);
          if (dist < ch.size * 2.5) {
            ch.tapped = true;
            ch.highlighted = true;
            this._countHighlighted.push(ch.id);
            audio.playCount(this._countHighlighted.length);
            audio.speak(String(this._countHighlighted.length), { rate: 0.9 });

            if (this._countHighlighted.length >= this._problem.answer) {
              setTimeout(() => {
                this._phase = 'answer';
                audio.speak(this._problem.question, { rate: 0.8 });
              }, 600);
            }
            return;
          }
        }
      }
    } else if (this._phase === 'answer') {
      for (const btn of this._choiceBtns) {
        if (x >= btn.x && x <= btn.x + btn.w && y >= btn.y && y <= btn.y + btn.h) {
          const correct = btn.num === this._problem.answer;
          this._showFeedback(correct, btn.x + btn.w/2, btn.y + btn.h/2);
          return;
        }
      }
    } else if (this._phase === 'narrate' && this._narrateStep >= 2) {
      this._phase = 'count';
      audio.speak('¡Ahora toca cada gallina para contarlas!', { rate: 0.8 });
    }
  }

  _showFeedback(correct, x, y) {
    this.isShowingFeedback = true;
    this._feedbackCorrect = correct;
    this._feedbackAlpha = 0.5;
    if (correct) {
      if (!this._missed) this.correctAnswers++; this._missed = false;
      audio.playSuccess();
      audio.speak(`¡Correcto! ¡${this._problem.answer} gallinas!`, { rate: 0.9 });
      this._spawnParticles(x, y);
    } else {
      this._missed = true;
      audio.playError();
      audio.speak('¡Casi! Cuenta las gallinas otra vez, una por una.', { rate: 0.85 });
    }
    setTimeout(() => {
      this.isShowingFeedback = false; this._feedbackAlpha = 0;
      if (!correct) return; // same question again until it is right
      this.round++;
      if (this.round >= this.totalRounds) this._finish();
      else this._setupRound();
    }, correct ? 1400 : 1000);
  }

  _spawnParticles(x, y) {
    for (let i=0;i<14;i++) {
      const a=(Math.PI*2*i)/14; const sp=3+Math.random()*4;
      this._particles.push({x,y,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp-2,life:1,color:['#FFD700','#FF6F00','#4CAF50'][i%3],size:7+Math.random()*7});
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

    // Narration sequence
    if (this._phase === 'narrate') {
      this._narrateTimer += dt;
      if (this._narrateStep === 0 && this._narrateTimer > 2000) {
        this._narrateStep = 1;
        this._narrateTimer = 0;
        // All initial chickens arrived - check if we need to add more
        if (this._problem.op === 'add' && this._problem.b > 0) {
          setTimeout(() => {
            audio.speak(this._problem.narration2, { rate: 0.8 });
            // Spawn additional chickens
            setTimeout(() => this._spawnChickens(this._problem.b, this._problem.a), 1000);
          }, 1200);
        } else if (this._problem.op === 'sub') {
          setTimeout(() => {
            audio.speak(this._problem.narration2, { rate: 0.8 });
            // Mark some chickens as leaving
            const toLeave = this._chickens.slice(0, this._problem.b);
            toLeave.forEach(ch => { ch.isLeaving = true; ch.leaveProgress = 0; });
          }, 1200);
        }
      }
      if (this._narrateStep === 1 && this._narrateTimer > 2500) {
        this._narrateStep = 2;
        audio.speak('¡Toca la pantalla para contar!', { rate: 0.85 });
      }
    }

    // Move chickens toward target
    this._chickens.forEach(ch => {
      if (ch.isLeaving) {
        ch.leaveProgress = Math.min(1, ch.leaveProgress + dt * 0.001);
        ch.x += (W => W * 1.2 - ch.targetX)(this.W) * dt * 0.001;
        ch.y = ch.targetY;
        return;
      }
      const dx = ch.targetX - ch.x;
      const dy = ch.targetY - ch.y;
      const d = Math.hypot(dx, dy);
      if (d > 2) {
        const spd = Math.min(d, 5);
        ch.x += (dx/d)*spd;
        ch.y += (dy/d)*spd;
      } else {
        ch.x = ch.targetX;
        ch.y = ch.targetY;
        ch.arrived = true;
      }
      ch.walkPhase += dt * 0.008;
    });

    this._particles = this._particles.filter(p => {
      p.x += p.vx; p.y += p.vy; p.vy += 0.25; p.life -= dt * 0.002; return p.life > 0;
    });
  }

  render() {
    const ctx = this.ctx; const W = this.W; const H = this.H;
    if (!W || !H) return;
    ctx.clearRect(0,0,W,H);

    // Background - Guatemalan farm yard
    const bg = ctx.createLinearGradient(0,0,0,H);
    bg.addColorStop(0,'#87CEEB'); bg.addColorStop(0.5,'#AED581'); bg.addColorStop(1,'#795548');
    ctx.fillStyle=bg; ctx.fillRect(0,0,W,H);

    // Farm house in background
    ctx.fillStyle='#FFF9C4';
    ctx.fillRect(W*0.62,H*0.15,W*0.32,H*0.28);
    ctx.fillStyle='#C62828';
    ctx.beginPath(); ctx.moveTo(W*0.59,H*0.15); ctx.lineTo(W*0.78,H*0.04); ctx.lineTo(W*0.97,H*0.15); ctx.closePath(); ctx.fill();
    // Door
    ctx.fillStyle='#8D6E63'; ctx.beginPath(); ctx.roundRect(W*0.74,H*0.3,W*0.08,H*0.13,[4,4,0,0]); ctx.fill();

    // Ground
    ctx.fillStyle='#6D4C41'; ctx.fillRect(0,H*0.68,W,H*0.32);
    ctx.fillStyle='#558B2F'; ctx.fillRect(0,H*0.66,W,H*0.04);

    // Fence
    ctx.strokeStyle='#8D6E63'; ctx.lineWidth=2;
    ctx.beginPath(); ctx.moveTo(0,H*0.62); ctx.lineTo(W,H*0.62); ctx.stroke();
    for (let fx=W*0.02;fx<W;fx+=W*0.06) {
      ctx.beginPath();
      ctx.moveTo(fx,H*0.58); ctx.lineTo(fx,H*0.65);
      ctx.stroke();
    }

    // Problem text boxes
    if (this._narrateStep >= 0) {
      ctx.save();
      ctx.fillStyle='rgba(0,0,0,0.6)';
      ctx.beginPath(); ctx.roundRect(W*0.04,H*0.04,W*0.92,H*0.11,12); ctx.fill();
      ctx.fillStyle='white'; ctx.font=`bold ${Math.min(15,W*0.04)}px Nunito,sans-serif`;
      ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText(this._problem.narration1, W/2, H*0.095);
      ctx.restore();
    }
    if (this._narrateStep >= 1) {
      ctx.save();
      ctx.fillStyle='rgba(0,60,0,0.6)';
      ctx.beginPath(); ctx.roundRect(W*0.04,H*0.17,W*0.92,H*0.11,12); ctx.fill();
      ctx.fillStyle='#C8E6C9'; ctx.font=`bold ${Math.min(15,W*0.04)}px Nunito,sans-serif`;
      ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText(this._problem.narration2, W/2, H*0.225);
      ctx.restore();
    }

    // Chickens
    ctx.textAlign='center'; ctx.textBaseline='middle';
    const visibleChickens = this._chickens.filter(ch => !ch.isLeaving || ch.leaveProgress < 1);
    visibleChickens.forEach(ch => {
      if (ch.isLeaving && ch.leaveProgress >= 1) return;
      ctx.save();
      if (ch.isLeaving) ctx.globalAlpha = 1 - ch.leaveProgress;
      if (ch.highlighted) {
        ctx.shadowColor = '#FFD700'; ctx.shadowBlur = 20;
      }
      const bob = Math.sin(ch.walkPhase) * 3;
      // Draw chicken body
      this._drawChicken(ctx, ch.x, ch.y+bob, ch.size, ch.color, ch.highlighted);

      // Count number if tapped
      if (ch.tapped) {
        ctx.fillStyle = '#FFD700';
        ctx.font = `bold ${Math.round(ch.size*0.9)}px Nunito,sans-serif`;
        ctx.fillText(String(this._countHighlighted.indexOf(ch.id)+1), ch.x, ch.y+bob-ch.size*1.8);
      }
      ctx.restore();
    });

    // Count display
    if (this._phase === 'count' && this._countHighlighted.length > 0) {
      ctx.save();
      ctx.fillStyle='rgba(0,0,0,0.65)';
      ctx.beginPath(); ctx.roundRect(W*0.37,H*0.66,W*0.26,H*0.1,12); ctx.fill();
      ctx.fillStyle='#FFD700'; ctx.font=`bold ${Math.round(W*0.1)}px Nunito,sans-serif`;
      ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText(String(this._countHighlighted.length), W/2, H*0.71);
      ctx.restore();
    }

    // Phase-based prompts
    if (this._phase === 'narrate' && this._narrateStep >= 2) {
      ctx.save();
      ctx.fillStyle='rgba(255,165,0,0.2)';
      ctx.beginPath(); ctx.roundRect(W*0.04,H*0.88,W*0.92,H*0.1,12); ctx.fill();
      ctx.fillStyle='#FFD700'; ctx.font=`bold ${Math.min(15,W*0.04)}px Nunito,sans-serif`;
      ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText('👆 ¡Toca para contar las gallinas!', W/2, H*0.933);
      ctx.restore();
    }

    if (this._phase === 'count') {
      ctx.save();
      ctx.fillStyle='rgba(0,0,0,0.65)';
      ctx.beginPath(); ctx.roundRect(W*0.04,H*0.88,W*0.92,H*0.1,12); ctx.fill();
      ctx.fillStyle='white'; ctx.font=`bold ${Math.min(15,W*0.04)}px Nunito,sans-serif`;
      ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText(`¡Toca cada gallina! (${this._countHighlighted.length}/${this._problem.answer})`, W/2, H*0.933);
      ctx.restore();
    }

    if (this._phase === 'answer') {
      // Question
      ctx.save();
      ctx.fillStyle='rgba(0,0,0,0.7)';
      ctx.beginPath(); ctx.roundRect(W*0.04,H*0.67,W*0.92,H*0.09,12); ctx.fill();
      ctx.fillStyle='white'; ctx.font=`bold ${Math.min(14,W*0.038)}px Nunito,sans-serif`;
      ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText(this._problem.question, W/2, H*0.715);
      ctx.restore();

      // Choice buttons
      this._choiceBtns.forEach((btn, i) => {
        ctx.save();
        const pulse=1+Math.sin(this._animTime*2.5+i)*0.04;
        ctx.shadowColor='rgba(0,0,0,0.35)'; ctx.shadowBlur=10;
        ctx.fillStyle=btn.color;
        ctx.beginPath();
        ctx.roundRect(btn.x+(btn.w*(1-pulse))/2,btn.y+(btn.h*(1-pulse))/2,btn.w*pulse,btn.h*pulse,14);
        ctx.fill();
        ctx.strokeStyle='rgba(255,255,255,0.5)'; ctx.lineWidth=2; ctx.shadowBlur=0; ctx.stroke();

        // Chicken dots representing the number
        const dotRows = Math.ceil(btn.num / 3);
        const dotCols = Math.min(btn.num, 3);
        const dotSize = btn.w * 0.08;
        const dotSpacing = btn.w * 0.28;
        for (let d = 0; d < btn.num; d++) {
          const dc = d % 3; const dr = Math.floor(d / 3);
          ctx.fillStyle='white';
          ctx.beginPath();
          ctx.arc(btn.x+btn.w*0.25+dc*dotSpacing, btn.y+btn.h*0.25+dr*dotSpacing, dotSize, 0, Math.PI*2);
          ctx.fill();
        }
        // Number
        ctx.fillStyle='white'; ctx.font=`bold ${Math.round(btn.h*0.4)}px Nunito,sans-serif`;
        ctx.textAlign='center'; ctx.textBaseline='bottom';
        ctx.fillText(String(btn.num), btn.x+btn.w/2, btn.y+btn.h-4);
        ctx.restore();
      });
    }

    // Round dots
    ctx.save();
    for (let i=0;i<this.totalRounds;i++) {
      ctx.beginPath(); ctx.arc(W/2-(this.totalRounds-1)*12+i*24,H*0.88,6,0,Math.PI*2);
      ctx.fillStyle=i<this.round?'#4CAF50':i===this.round?'#FFD700':'rgba(255,255,255,0.4)'; ctx.fill();
    }
    ctx.restore();

    if (this._feedbackAlpha>0) {
      ctx.save(); ctx.globalAlpha=this._feedbackAlpha*0.3;
      ctx.fillStyle=this._feedbackCorrect?'#4CAF50':'#F44336';
      ctx.fillRect(0,0,W,H); ctx.restore();
    }
    this._particles.forEach(p=>{
      ctx.save(); ctx.globalAlpha=p.life; ctx.fillStyle=p.color;
      ctx.beginPath(); ctx.arc(p.x,p.y,p.size*p.life,0,Math.PI*2); ctx.fill(); ctx.restore();
    });
  }

  _drawChicken(ctx, x, y, size, color, highlighted) {
    // Body
    ctx.fillStyle = color;
    ctx.beginPath(); ctx.ellipse(x, y, size*0.7, size*0.55, 0, 0, Math.PI*2); ctx.fill();
    // Head
    ctx.fillStyle = color;
    ctx.beginPath(); ctx.arc(x+size*0.65, y-size*0.35, size*0.35, 0, Math.PI*2); ctx.fill();
    // Beak
    ctx.fillStyle='#FF6F00';
    ctx.beginPath();
    ctx.moveTo(x+size*0.98,y-size*0.33);
    ctx.lineTo(x+size*1.2,y-size*0.22);
    ctx.lineTo(x+size*0.98,y-size*0.12);
    ctx.closePath(); ctx.fill();
    // Eye
    ctx.fillStyle='white'; ctx.beginPath(); ctx.arc(x+size*0.73,y-size*0.4,size*0.1,0,Math.PI*2); ctx.fill();
    ctx.fillStyle='black'; ctx.beginPath(); ctx.arc(x+size*0.74,y-size*0.4,size*0.055,0,Math.PI*2); ctx.fill();
    // Comb
    ctx.fillStyle='#E53935'; ctx.beginPath(); ctx.arc(x+size*0.65,y-size*0.72,size*0.12,0,Math.PI*2); ctx.fill();
    // Wing
    ctx.fillStyle=highlighted ? '#FFD700' : `${color}aa`;
    ctx.beginPath(); ctx.ellipse(x-size*0.15,y-size*0.15,size*0.35,size*0.2,-0.3,0,Math.PI*2); ctx.fill();
    // Legs
    ctx.strokeStyle='#FF8F00'; ctx.lineWidth=size*0.07; ctx.lineCap='round';
    ctx.beginPath();
    ctx.moveTo(x-size*0.1,y+size*0.5); ctx.lineTo(x-size*0.1,y+size*0.8);
    ctx.moveTo(x+size*0.2,y+size*0.5); ctx.lineTo(x+size*0.2,y+size*0.8);
    ctx.stroke();
    // Highlight glow if tapped
    if (highlighted) {
      ctx.strokeStyle='#FFD700'; ctx.lineWidth=2;
      ctx.beginPath(); ctx.ellipse(x,y,size*0.85,size*0.7,0,0,Math.PI*2); ctx.stroke();
    }
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
