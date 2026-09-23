// Module 3, Lesson 1: Sort Fruits - Drag mangoes and bananas to their baskets
// Two baskets, 6 fruit items scattered, drag-and-drop interaction

import audio from '../../engine/audio.js';
import { TouchHandler } from '../../engine/touch.js';

export default class AgruparFrutasLesson {
  constructor(canvasId, config = {}) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.onComplete = config.onComplete || (() => {});
    this.correctAnswers = 0;
    this.errors = 0;
    this.isShowingFeedback = false;
    this._animTime = 0;
    this._running = false;
    this._raf = null;
    this._lastTime = null;
    this._fruits = [];
    this._baskets = [];
    this._draggedFruit = null;
    this._dragX = 0;
    this._dragY = 0;
    this._dragOffX = 0;
    this._dragOffY = 0;
    this._particles = [];
    this._sortedCount = 0;
    this._totalFruits = 6;
    this._complete = false;
    this._feedbackAlpha = 0;
    this._feedbackCorrect = false;

    this.touch = new TouchHandler(this.canvas);
    this.touch.onDragStart(pos => this._onDragStart(pos.x, pos.y));
    this.touch.onDragMove(pos => this._onDragMove(pos.x, pos.y));
    this.touch.onDragEnd(pos => this._onDragEnd(pos.x, pos.y));

    this._resizeBound = () => { this._resize(); this._layoutScene(); };
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

  _layoutScene() {
    const W = this.W, H = this.H;
    if (!W) return;

    const basketSize = Math.min(W * 0.28, 90);

    // Two baskets at bottom
    this._baskets = [
      {
        id: 'mango',
        x: W * 0.18, y: H * 0.7,
        w: basketSize, h: basketSize * 0.8,
        color: '#FF6F00',
        label: '🥭',
        emoji: '🥭',
        fruits: [],
        maxFruits: 3
      },
      {
        id: 'banana',
        x: W * 0.7, y: H * 0.7,
        w: basketSize, h: basketSize * 0.8,
        color: '#F9A825',
        label: '🍌',
        emoji: '🍌',
        fruits: [],
        maxFruits: 3
      }
    ];

    // Only re-create fruits if not already created
    if (this._fruits.length === 0) {
      const fruitSize = Math.min(W * 0.1, 44);
      const fruitPositions = [
        { x: W*0.15, y: H*0.35 },
        { x: W*0.42, y: H*0.28 },
        { x: W*0.72, y: H*0.33 },
        { x: W*0.55, y: H*0.48 },
        { x: W*0.28, y: H*0.5 },
        { x: W*0.82, y: H*0.45 }
      ];

      const fruitTypes = ['mango', 'banana', 'mango', 'banana', 'mango', 'banana'];
      fruitTypes.sort(() => Math.random() - 0.5); // shuffle

      this._fruits = fruitPositions.map((pos, i) => ({
        id: i,
        type: fruitTypes[i],
        emoji: fruitTypes[i] === 'mango' ? '🥭' : '🍌',
        x: pos.x,
        y: pos.y,
        homeX: pos.x,
        homeY: pos.y,
        size: fruitSize,
        sorted: false,
        inBasket: null,
        bobOffset: Math.random() * Math.PI * 2
      }));
    }
  }

  _onDragStart(x, y) {
    if (this._complete) return;
    const hitSize = (this._fruits[0]?.size || 40) * 1.2;
    for (const fruit of this._fruits) {
      if (fruit.sorted) continue;
      if (Math.abs(x - fruit.x) < hitSize && Math.abs(y - fruit.y) < hitSize) {
        this._draggedFruit = fruit;
        this._dragOffX = x - fruit.x;
        this._dragOffY = y - fruit.y;
        audio.playTap && audio.playTap();
        break;
      }
    }
  }

  _onDragMove(x, y) {
    if (!this._draggedFruit) return;
    this._dragX = x - this._dragOffX;
    this._dragY = y - this._dragOffY;
    this._draggedFruit.x = this._dragX;
    this._draggedFruit.y = this._dragY;
  }

  _onDragEnd(x, y) {
    if (!this._draggedFruit) return;
    const fruit = this._draggedFruit;
    this._draggedFruit = null;

    // Check if dropped in a basket
    let dropped = false;
    for (const basket of this._baskets) {
      if (
        x >= basket.x && x <= basket.x + basket.w &&
        y >= basket.y - basket.h * 0.3 && y <= basket.y + basket.h
      ) {
        const correct = fruit.type === basket.id;
        if (correct) {
          fruit.sorted = true;
          fruit.inBasket = basket.id;
          basket.fruits.push(fruit);
          // Snap to basket position
          const slot = basket.fruits.length - 1;
          fruit.x = basket.x + basket.w * 0.25 + slot * basket.w * 0.25;
          fruit.y = basket.y - basket.h * 0.1;
          this.correctAnswers++;
          this._sortedCount++;
          audio.playSuccess();
          this._spawnParticles(x, y, basket.color);
          this._feedbackCorrect = true;
          this._feedbackAlpha = 0.4;
          dropped = true;

          if (this._sortedCount >= this._totalFruits) {
            setTimeout(() => this._finish(), 800);
          }
        } else {
          // Bounce back
          fruit.x = fruit.homeX;
          fruit.y = fruit.homeY;
          this.errors++;
          audio.playError();
          this._feedbackCorrect = false;
          this._feedbackAlpha = 0.35;
          audio.speak('¡Esa fruta va en la otra canasta!', { rate: 0.9 });
        }
        break;
      }
    }

    if (!dropped && !fruit.sorted) {
      // Bounce back to home
      fruit.x = fruit.homeX;
      fruit.y = fruit.homeY;
    }

    setTimeout(() => this._feedbackAlpha = 0, 600);
  }

  _spawnParticles(x, y, color) {
    for (let i = 0; i < 12; i++) {
      const a = (Math.PI * 2 * i) / 12;
      const sp = 3 + Math.random() * 4;
      this._particles.push({ x, y, vx: Math.cos(a)*sp, vy: Math.sin(a)*sp-2, life:1, color, size:6+Math.random()*8 });
    }
  }

  start() {
    this._resize();
    this._layoutScene();
    this._running = true;
    this._lastTime = performance.now();
    this._loop();
    setTimeout(() => audio.speak('¡Pon cada fruta en su canasta! Mangos con mangos, bananos con bananos.', { rate: 0.8 }), 700);
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

    // Background - market scene
    const bg = ctx.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, '#87CEEB');
    bg.addColorStop(0.55, '#AED581');
    bg.addColorStop(1, '#8D6E63');
    ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);

    // Ground
    ctx.fillStyle = '#795548'; ctx.fillRect(0, H*0.72, W, H*0.28);
    ctx.fillStyle = '#6D4C41'; ctx.fillRect(0, H*0.7, W, H*0.03);

    // Market stall canopy
    ctx.fillStyle = '#E53935';
    ctx.beginPath();
    ctx.moveTo(0, H*0.16);
    for (let i = 0; i <= 10; i++) {
      const scallop = i % 2 === 0 ? H*0.16 : H*0.22;
      ctx.lineTo(W * i / 10, scallop);
    }
    ctx.lineTo(W, H*0.16); ctx.closePath(); ctx.fill();

    ctx.fillStyle = '#B71C1C';
    ctx.fillRect(0, H*0.12, W, H*0.06);

    // Counter / table
    ctx.fillStyle = '#A1887F';
    ctx.fillRect(W*0.05, H*0.6, W*0.9, H*0.08);
    ctx.fillStyle = '#8D6E63';
    ctx.fillRect(W*0.05, H*0.66, W*0.9, H*0.03);

    // Score bar
    const sorted = this._sortedCount;
    ctx.save();
    ctx.fillStyle = 'rgba(0,0,0,0.5)';
    ctx.beginPath(); ctx.roundRect(W*0.1, H*0.22, W*0.8, H*0.06, 10); ctx.fill();
    const fillPct = sorted / this._totalFruits;
    const fillGrad = ctx.createLinearGradient(W*0.1, 0, W*0.9, 0);
    fillGrad.addColorStop(0, '#4CAF50'); fillGrad.addColorStop(1, '#FFD700');
    ctx.fillStyle = fillGrad;
    ctx.beginPath(); ctx.roundRect(W*0.1, H*0.22, W*0.8*fillPct, H*0.06, 10); ctx.fill();
    ctx.fillStyle = 'white'; ctx.font = `bold ${Math.round(W*0.035)}px Nunito,sans-serif`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(`${sorted} / ${this._totalFruits}`, W/2, H*0.25);
    ctx.restore();

    // Baskets
    this._baskets.forEach(basket => {
      const isHover = this._draggedFruit &&
        this._dragX >= basket.x && this._dragX <= basket.x + basket.w;

      ctx.save();
      if (isHover) { ctx.shadowColor = basket.color; ctx.shadowBlur = 20; }

      // Basket body (trapezoid)
      ctx.fillStyle = '#8D6E63';
      ctx.beginPath();
      ctx.moveTo(basket.x + basket.w * 0.1, basket.y);
      ctx.lineTo(basket.x + basket.w * 0.9, basket.y);
      ctx.lineTo(basket.x + basket.w, basket.y + basket.h);
      ctx.lineTo(basket.x, basket.y + basket.h);
      ctx.closePath(); ctx.fill();

      // Basket rim
      ctx.fillStyle = '#6D4C41';
      ctx.beginPath();
      ctx.ellipse(basket.x + basket.w/2, basket.y, basket.w*0.45, basket.h*0.15, 0, 0, Math.PI*2);
      ctx.fill();

      // Basket weave pattern
      ctx.strokeStyle = '#A1887F'; ctx.lineWidth = 1.5;
      for (let i = 0; i < 4; i++) {
        ctx.beginPath();
        ctx.moveTo(basket.x + basket.w*0.1, basket.y + basket.h*0.25*i);
        ctx.lineTo(basket.x + basket.w*0.9, basket.y + basket.h*0.25*i);
        ctx.stroke();
      }

      // Basket label emoji
      ctx.font = `${Math.round(basket.w * 0.5)}px sans-serif`;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(basket.emoji, basket.x + basket.w/2, basket.y - basket.h*0.35);

      // Highlight ring
      ctx.strokeStyle = isHover ? '#FFD700' : basket.color;
      ctx.lineWidth = isHover ? 3 : 2;
      ctx.setLineDash(isHover ? [] : [4, 3]);
      ctx.beginPath();
      ctx.ellipse(basket.x + basket.w/2, basket.y, basket.w*0.45, basket.h*0.15, 0, 0, Math.PI*2);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.restore();
    });

    // Fruits
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    this._fruits.forEach(fruit => {
      if (this._draggedFruit === fruit) return; // draw dragged last
      const bob = fruit.sorted ? 0 : Math.sin(this._animTime * 2 + fruit.bobOffset) * 4;
      ctx.save();
      ctx.globalAlpha = fruit.sorted ? 0.85 : 1;
      ctx.font = `${fruit.size * 1.6}px sans-serif`;
      ctx.fillText(fruit.emoji, fruit.x, fruit.y + bob);
      // Shadow under fruit
      ctx.globalAlpha = 0.25;
      ctx.fillStyle = 'rgba(0,0,0,0.5)';
      ctx.beginPath();
      ctx.ellipse(fruit.x, fruit.y + fruit.size * 0.65 + bob, fruit.size * 0.35, fruit.size * 0.1, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    });

    // Draw dragged fruit on top
    if (this._draggedFruit) {
      const fruit = this._draggedFruit;
      ctx.save();
      ctx.font = `${fruit.size * 1.9}px sans-serif`;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.shadowColor = 'rgba(0,0,0,0.4)'; ctx.shadowBlur = 16;
      ctx.fillText(fruit.emoji, fruit.x, fruit.y);
      ctx.restore();
    }

    // Instructions if not started
    if (this._sortedCount === 0) {
      ctx.save();
      ctx.fillStyle = 'rgba(0,0,0,0.65)';
      ctx.beginPath(); ctx.roundRect(W*0.05, H*0.3, W*0.9, H*0.08, 12); ctx.fill();
      ctx.fillStyle = 'white'; ctx.font = `bold ${Math.min(15,W*0.04)}px Nunito,sans-serif`;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText('¡Arrastra las frutas a su canasta!', W/2, H*0.34);
      ctx.restore();
    }

    // Feedback
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
    this._complete = true;
    const accuracy = (this.correctAnswers) / (this.correctAnswers + this.errors);
    const stars = accuracy >= 0.85 ? 3 : accuracy >= 0.6 ? 2 : 1;
    audio.playVictory && audio.playVictory();
    audio.speak('¡Excelente! ¡Todas las frutas en su lugar!', { rate: 0.9 });
    if (this.onComplete) setTimeout(() => this.onComplete(stars), 1000);
  }

  destroy() {
    this._running = false;
    if (this._raf) cancelAnimationFrame(this._raf);
    this.touch.destroy();
    window.removeEventListener('resize', this._resizeBound);
  }
}
