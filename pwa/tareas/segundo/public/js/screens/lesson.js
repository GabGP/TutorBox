// Lesson Screen - Wraps individual lesson scenes
// Handles progress dots, back button, victory animation

import audio from '../engine/audio.js';
import { saveLesson } from '../data/progress.js';

let _currentScene = null;
let _currentModule = null;
let _currentLesson = null;

export async function renderLesson(navigate, params = {}) {
  const screen = document.getElementById('lesson-screen');
  screen.innerHTML = '';

  _currentModule = params.module;
  _currentLesson = params.lesson;

  if (!_currentModule || !_currentLesson) {
    navigate('map');
    return;
  }

  const mod = _currentModule;
  const lesson = _currentLesson;

  // ── Header ───────────────────────────────────────────────────────────────
  const header = document.createElement('div');
  header.className = 'lesson-header';

  const backBtn = document.createElement('button');
  backBtn.className = 'lesson-back-btn';
  backBtn.innerHTML = '←';
  backBtn.setAttribute('aria-label', 'Volver al mapa');
  backBtn.addEventListener('click', () => {
    destroyCurrentScene();
    navigate('map');
  });
  header.appendChild(backBtn);

  // Progress dots (lesson index within module)
  const dotsEl = document.createElement('div');
  dotsEl.className = 'lesson-progress-dots';
  const lessonIndex = mod.lessons.findIndex(l => l.id === lesson.id);
  mod.lessons.forEach((l, i) => {
    const dot = document.createElement('div');
    dot.className = 'lesson-dot' + (i === lessonIndex ? ' active' : i < lessonIndex ? ' done' : '');
    dotsEl.appendChild(dot);
  });
  header.appendChild(dotsEl);

  // Module emoji
  const modEmoji = document.createElement('div');
  modEmoji.style.cssText = 'font-size:1.6rem; padding-right:4px;';
  modEmoji.textContent = mod.emoji;
  header.appendChild(modEmoji);

  screen.appendChild(header);

  // ── Canvas Area ──────────────────────────────────────────────────────────
  const canvasWrap = document.createElement('div');
  canvasWrap.className = 'lesson-canvas-wrap';
  canvasWrap.style.cssText = 'position:relative; flex:1; width:100%; display:flex; align-items:center; justify-content:center;';

  const canvas = document.createElement('canvas');
  canvas.id = 'lesson-canvas';
  canvas.className = 'lesson-canvas';
  canvas.style.cssText = 'width:100%; height:100%; touch-action:none; display:block;';
  canvas.tabIndex = -1;
  canvasWrap.appendChild(canvas);

  screen.appendChild(canvasWrap);

  // ── Kuk Guide (in lesson context) ────────────────────────────────────────
  const kukEl = document.createElement('div');
  kukEl.style.cssText = `
    position: fixed;
    bottom: 12px;
    right: 12px;
    width: 72px;
    height: 72px;
    z-index: 50;
    animation: kukBounce 2s ease-in-out infinite;
    filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.4));
  `;
  kukEl.innerHTML = '<img src="icons/quq.svg" alt="" draggable="false" style="width:100%;height:100%;object-fit:contain" />';
  screen.appendChild(kukEl);

  // ── Load lesson module ───────────────────────────────────────────────────
  try {
    const lessonMod = await lesson.module();
    const LessonClass = lessonMod.default;

    if (LessonClass && typeof LessonClass === 'function') {
      // It's a class - instantiate with canvas
      _currentScene = new LessonClass('lesson-canvas', {
        totalRounds: 3,
        onComplete: (stars) => onLessonComplete(stars, navigate, mod, lesson)
      });
      _currentScene.start();
    } else if (typeof LessonClass === 'function') {
      // It's a factory function
      _currentScene = LessonClass('lesson-canvas', {
        onComplete: (stars) => onLessonComplete(stars, navigate, mod, lesson)
      });
    } else {
      throw new Error('Invalid lesson module export');
    }
  } catch (err) {
    console.error('Failed to load lesson:', err);
    showLessonError(screen, navigate);
  }
}

function showLessonError(screen, navigate) {
  const errEl = document.createElement('div');
  errEl.style.cssText = 'color:white; text-align:center; padding:40px; font-size:1.2rem;';
  errEl.innerHTML = '<div style="font-size:3rem">😕</div><br>No se pudo cargar la lección';
  screen.appendChild(errEl);
  setTimeout(() => navigate('map'), 2500);
}

async function onLessonComplete(stars, navigate, mod, lesson) {
  // Save progress
  saveLesson(mod.id, lesson.id, stars);

  // Show victory overlay
  showVictory(stars, () => {
    destroyCurrentScene();
    navigate('map');
  });
}

function showVictory(stars, onContinue) {
  const overlay = document.createElement('div');
  overlay.className = 'victory-overlay';

  const starsRow = document.createElement('div');
  starsRow.className = 'victory-stars';
  for (let i = 0; i < 3; i++) {
    const s = document.createElement('div');
    s.className = 'victory-star';
    s.textContent = i < stars ? '⭐' : '☆';
    s.style.animationDelay = `${i * 0.15}s`;
    if (i >= stars) s.style.opacity = '0.4';
    starsRow.appendChild(s);
  }
  overlay.appendChild(starsRow);

  const text = document.createElement('div');
  text.className = 'victory-text';
  text.textContent = stars === 3 ? '¡Excelente!' : stars === 2 ? '¡Muy bien!' : '¡Lo lograste!';
  overlay.appendChild(text);

  const subText = document.createElement('div');
  subText.style.cssText = 'color:rgba(255,255,255,0.8); font-size:1rem; font-weight:600;';
  subText.textContent = `${stars} estrella${stars !== 1 ? 's' : ''} ganada${stars !== 1 ? 's' : ''}`;
  overlay.appendChild(subText);

  const continueBtn = document.createElement('button');
  continueBtn.className = 'btn-large btn-gold victory-btn';
  continueBtn.style.cssText = 'margin-top:8px; max-width:260px;';
  continueBtn.textContent = '¡Continuar! →';
  continueBtn.addEventListener('click', () => {
    overlay.remove();
    onContinue();
  });
  continueBtn.addEventListener('touchend', e => { e.preventDefault(); overlay.remove(); onContinue(); });
  overlay.appendChild(continueBtn);

  document.body.appendChild(overlay);
  requestAnimationFrame(() => overlay.classList.add('active'));

  audio.playStars();
}

function destroyCurrentScene() {
  if (_currentScene && typeof _currentScene.destroy === 'function') {
    _currentScene.destroy();
    _currentScene = null;
  }
}
