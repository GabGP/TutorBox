// Module 7, Lesson 1: Interactive Clock - Set the clock hands
// Large analog clock, drag hour hand to the correct hour position

import audio from '../../engine/audio.js';
import { TouchHandler } from '../../engine/touch.js';

export default class RelojInteractivoLesson {
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
    this._feedbackAlpha = 0;
    this._feedbackCorrect = false;
    this._targetHour = 3;
    this._currentHourAngle = 0; // radians from 12 o'clock
    this._draggingHand = false;
    this._dragOffAngle = 0;
    this._checkTimer = 0;
    this._showDigital = true;
    this._correctSnap = false;
    this._activities = [];

    this.touch = new TouchHandler(this.canvas);
    this.touch.onDragStart(pos => this._onDragStart(pos.x, pos.y));
    this.touch.onDragMove(pos => this._onDragMove(pos.x, pos.y));
    this.touch.onDragEnd(pos => this._onDragEnd(pos.x, pos.y));
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
    this._clockR = Math.min(this.W, this.H) * 0.3;
    this._clockX = this.W / 2;
    this._clockY = this.H * 0.45;
  }

  _setupRound() {
    const targets = [3, 6, 9];
    const activities = [
      { hour: 3, icon: '🌤️', label: 'Tres en punto', narration: '¡Pon las manecillas a las 3 en punto!' },
      { hour: 6, icon: '🌆', label: 'Seis en punto', narration: '¡Pon las manecillas a las 6 en punto!' },
      { hour: 9, icon: '🌙', label: 'Nueve en punto', narration: '¡Pon las manecillas a las 9 en punto!' }
    ];

    this._targetHour = targets[this.round];
    this._activity = activities[this.round];
    this._currentHourAngle = 0; // Start at 12
    this._correctSnap = false;
    this._checkTimer = 0;

    setTimeout(() => audio.speak(this._activity.narration, { rate: 0.8 }), 400);
  }

  _hourToAngle(hour) {
    return ((hour % 12) / 12) * Math.PI * 2 - Math.PI / 2;
  }

  _angleToHour(angle) {
    let a = angle + Math.PI / 2;
    if (a < 0) a += Math.PI * 2;
    a = a % (Math.PI * 2);
    return Math.round((a / (Math.PI * 2)) * 12) % 12 || 12;
  }

  _getHandTip(angle, length) {
    return {
      x: this._clockX + Math.cos(angle) * length,
      y: this._clockY + Math.sin(angle) * length
    };
  }

  _isOnHand(x, y) {
    const r = this._clockR;
    const handLen = r * 0.55;
    const tip = this._getHandTip(this._currentHourAngle, handLen);
    // Check if tap is near the hand line
    const handX = this._clockX, handY = this._clockY;
    // Distance from point to line segment
    const dx = tip.x - handX, dy = tip.y - handY;
    const len2 = dx*dx + dy*dy;
    let t = ((x-handX)*dx + (y-handY)*dy) / len2;
    t = Math.max(0, Math.min(1, t));
    const px = handX + t*dx, py = handY + t*dy;
    const dist = Math.hypot(x-px, y-py);
    return dist < r * 0.18;
  }

  _onDragStart(x, y) {
    if (this.isShowingFeedback) return;
    if (this._isOnHand(x, y) || Math.hypot(x - this._clockX, y - this._clockY) < this._clockR) {
      this._draggingHand = true;
    }
  }

  _onDragMove(x, y) {
    if (!this._draggingHand || this.isShowingFeedback) return;
    const angle = Math.atan2(y - this._clockY, x - this._clockX);
    this._currentHourAngle = angle;

    // Check proximity to target
    const currentHour = this._angleToHour(this._currentHourAngle);
    const targetAngle = this._hourToAngle(this._targetHour);
    const diff = Math.abs(this._currentHourAngle - targetAngle);
    const normDiff = Math.min(diff, Math.PI * 2 - diff);

    if (normDiff < 0.18) {
      this._correctSnap = true;
    } else {
      this._correctSnap = false;
    }
  }

  _onDragEnd(x, y) {
    if (!this._draggingHand) return;
    this._draggingHand = false;

    if (this._correctSnap) {
      // Snap to exact position
      this._currentHourAngle = this._hourToAngle(this._targetHour);
      this._showFeedback(true, this._clockX, this._clockY - this._clockR * 0.3);
    }
  }

  _onTap(x, y) {
    // Submit button area check
    if (this.isShowingFeedback) return;
    const btnY = this.H * 0.8;
    const btnH = this.H * 0.1;
    if (y >= btnY && y <= btnY + btnH && x >= this.W * 0.2 && x <= this.W * 0.8) {
      const currentHour = this._angleToHour(this._currentHourAngle);
      const correct = currentHour === this._targetHour;
      this._showFeedback(correct, this.W/2, this.H*0.85);
    }
  }

  _showFeedback(correct, x, y) {
    this.isShowingFeedback = true;
    this._feedbackCorrect = correct;
    this._feedbackAlpha = 0.5;
    if (correct) {
      this.correctAnswers++;
      audio.playSuccess();
      audio.speak(`¡Correcto! ¡Las ${this._targetHour} en punto!`, { rate: 0.9 });
      this._spawnParticles(x, y);
    } else {
      this.errors++;
      audio.playError();
      audio.speak(`¡Inténtalo de nuevo! Busca las ${this._targetHour}.`, { rate: 0.85 });
    }
    setTimeout(() => {
      this.isShowingFeedback = false; this._feedbackAlpha = 0; this._correctSnap = false;
      this.round++;
      if (this.round >= this.totalRounds) this._finish();
      else this._setupRound();
    }, correct ? 1400 : 1000);
  }

  _spawnParticles(x, y) {
    for (let i=0;i<14;i++) {
      const a=(Math.PI*2*i)/14; const sp=3+Math.random()*4;
      this._particles.push({x,y,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp-2,life:1,color:['#FFD700','#4CAF50','#2196F3','#E91E63'][i%4],size:7+Math.random()*7});
    }
  }

  start() {
    this._resize();
    this._running = true;
    this._lastTime = performance.now();
    this._setupRound();
    this._loop();
    setTimeout(() => audio.speak('¡Mueve la manecilla del reloj al número correcto!', { rate: 0.8 }), 600);
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

    const cx = this._clockX, cy = this._clockY, r = this._clockR;

    // Background
    const bg = ctx.createLinearGradient(0,0,0,H);
    bg.addColorStop(0,'#0D47A1'); bg.addColorStop(1,'#1565C0');
    ctx.fillStyle=bg; ctx.fillRect(0,0,W,H);

    // Stars in background
    for (let i=0;i<20;i++) {
      const sx = (Math.sin(i*137.5)*0.5+0.5)*W;
      const sy = (Math.cos(i*97.3)*0.5+0.5)*H*0.4;
      const star = 1+Math.sin(this._animTime*2+i)*0.4;
      ctx.fillStyle='rgba(255,255,255,0.7)';
      ctx.beginPath(); ctx.arc(sx,sy,star,0,Math.PI*2); ctx.fill();
    }

    // Activity icon and label
    if (this._activity) {
      ctx.font=`${Math.round(W*0.1)}px sans-serif`;
      ctx.textAlign='center'; ctx.textBaseline='middle';
      const iconPulse = 1+Math.sin(this._animTime*2)*0.05;
      ctx.save(); ctx.scale(iconPulse,iconPulse);
      ctx.fillText(this._activity.icon, W/2/iconPulse, H*0.12/iconPulse);
      ctx.restore();

      ctx.fillStyle='white'; ctx.font=`bold ${Math.min(18,W*0.048)}px Nunito,sans-serif`;
      ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText(`¡Pon las ${this._targetHour} en punto!`, W/2, H*0.2);
    }

    // ── Clock face ──────────────────────────────────────────────────────────
    // Outer shadow
    ctx.save();
    ctx.shadowColor='rgba(0,0,0,0.5)'; ctx.shadowBlur=24;
    ctx.fillStyle='white';
    ctx.beginPath(); ctx.arc(cx,cy,r+4,0,Math.PI*2); ctx.fill();
    ctx.restore();

    // Clock face gradient
    const faceGrad = ctx.createRadialGradient(cx-r*0.2,cy-r*0.2,0,cx,cy,r);
    faceGrad.addColorStop(0,'#FAFAFA'); faceGrad.addColorStop(1,'#F5F5F5');
    ctx.fillStyle=faceGrad;
    ctx.beginPath(); ctx.arc(cx,cy,r,0,Math.PI*2); ctx.fill();

    // Clock border
    ctx.strokeStyle = this._correctSnap ? '#4CAF50' : '#1565C0';
    ctx.lineWidth = this._correctSnap ? 5 : 4;
    if (this._correctSnap) { ctx.shadowColor='#4CAF50'; ctx.shadowBlur=16; }
    ctx.stroke();
    ctx.shadowBlur=0;

    // Hour markers
    for (let h=1;h<=12;h++) {
      const angle = ((h/12)*Math.PI*2) - Math.PI/2;
      const isMajor = h % 3 === 0;
      const innerR = r*(isMajor?0.78:0.85);

      // Number
      ctx.fillStyle = h === this._targetHour ? '#E53935' : '#1565C0';
      ctx.font=`bold ${Math.round(r*(isMajor?0.2:0.15))}px Nunito,sans-serif`;
      ctx.textAlign='center'; ctx.textBaseline='middle';
      const nx = cx + Math.cos(angle)*r*0.75;
      const ny = cy + Math.sin(angle)*r*0.75;
      if (h === this._targetHour) {
        const pulse = 1+Math.sin(this._animTime*4)*0.08;
        ctx.save(); ctx.scale(pulse,pulse);
        ctx.fillText(String(h), nx/pulse, ny/pulse);
        ctx.restore();
        // Target glow
        ctx.strokeStyle='rgba(229,57,53,0.3)'; ctx.lineWidth=14;
        ctx.beginPath(); ctx.arc(nx,ny,r*0.13,0,Math.PI*2); ctx.stroke();
      } else {
        ctx.fillText(String(h), nx, ny);
      }

      // Tick marks
      ctx.strokeStyle = isMajor ? '#333' : '#bbb';
      ctx.lineWidth = isMajor ? 2 : 1;
      ctx.beginPath();
      ctx.moveTo(cx+Math.cos(angle)*innerR, cy+Math.sin(angle)*innerR);
      ctx.moveTo(cx+Math.cos(angle)*r*0.93, cy+Math.sin(angle)*r*0.93);
      ctx.stroke();
    }

    // ── Clock hands ─────────────────────────────────────────────────────────
    // Minute hand (always at 12)
    const minAngle = -Math.PI/2;
    ctx.strokeStyle='#333'; ctx.lineWidth=Math.max(2, r*0.04); ctx.lineCap='round';
    ctx.beginPath();
    ctx.moveTo(cx,cy);
    ctx.lineTo(cx+Math.cos(minAngle)*r*0.75, cy+Math.sin(minAngle)*r*0.75);
    ctx.stroke();

    // Hour hand (draggable)
    const handColor = this._draggingHand ? '#E53935' : this._correctSnap ? '#4CAF50' : '#1565C0';
    ctx.strokeStyle=handColor; ctx.lineWidth=Math.max(3, r*0.065);
    if (this._correctSnap || this._draggingHand) { ctx.shadowColor=handColor; ctx.shadowBlur=14; }
    ctx.lineCap='round';
    ctx.beginPath();
    ctx.moveTo(cx,cy);
    ctx.lineTo(cx+Math.cos(this._currentHourAngle)*r*0.55, cy+Math.sin(this._currentHourAngle)*r*0.55);
    ctx.stroke();
    ctx.shadowBlur=0;

    // Center dot
    ctx.fillStyle='#333';
    ctx.beginPath(); ctx.arc(cx,cy,r*0.06,0,Math.PI*2); ctx.fill();
    ctx.fillStyle='white';
    ctx.beginPath(); ctx.arc(cx,cy,r*0.03,0,Math.PI*2); ctx.fill();

    // Drag hint arrow at hand tip
    if (!this._draggingHand && !this._correctSnap) {
      const tipX = cx+Math.cos(this._currentHourAngle)*r*0.55;
      const tipY = cy+Math.sin(this._currentHourAngle)*r*0.55;
      const pulse=0.7+Math.sin(this._animTime*4)*0.3;
      ctx.fillStyle=`rgba(229,57,53,${pulse})`;
      ctx.beginPath(); ctx.arc(tipX,tipY,r*0.1,0,Math.PI*2); ctx.fill();
      ctx.strokeStyle='white'; ctx.lineWidth=2;
      ctx.stroke();
      ctx.fillStyle='white'; ctx.font=`bold ${Math.round(r*0.12)}px sans-serif`;
      ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText('↕', tipX, tipY);
    }

    // ── Digital hint ─────────────────────────────────────────────────────────
    if (this._showDigital && this._activity) {
      ctx.save();
      ctx.fillStyle='rgba(0,0,0,0.6)';
      ctx.beginPath(); ctx.roundRect(W*0.35,H*0.73,W*0.3,H*0.075,10); ctx.fill();
      ctx.fillStyle=this._correctSnap?'#A5D6A7':'white';
      ctx.font=`bold ${Math.round(W*0.065)}px Nunito,sans-serif`;
      ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText(`${this._targetHour}:00`, W/2, H*0.768);
      ctx.restore();
    }

    // Submit button
    const currentHour = this._angleToHour(this._currentHourAngle);
    ctx.save();
    ctx.fillStyle = this._correctSnap ? '#4CAF50' : 'rgba(255,255,255,0.2)';
    ctx.beginPath(); ctx.roundRect(W*0.2,H*0.82,W*0.6,H*0.09,20); ctx.fill();
    ctx.fillStyle='white'; ctx.font=`bold ${Math.min(16,W*0.042)}px Nunito,sans-serif`;
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText(this._correctSnap ? '¡Perfecto! ✓' : '¡Verificar!', W/2, H*0.865);
    ctx.restore();

    // Round dots
    ctx.save();
    for (let i=0;i<this.totalRounds;i++) {
      ctx.beginPath(); ctx.arc(W/2-(this.totalRounds-1)*12+i*24,H*0.95,6,0,Math.PI*2);
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
