// Aprende Matemáticas con Q'uq' - Main App Entry Point
// SPA Router + Global State Management

import { renderMap } from './screens/map.js';
import { renderLesson } from './screens/lesson.js';
import { renderProfile } from './screens/profile.js';
import { renderParent } from './screens/parent.js';
import { getCurrentUser, setCurrentUser } from './data/progress.js';
import audio from './engine/audio.js';

// ── Global State ─────────────────────────────────────────────────────────────
export const state = {
  currentUser: null,
  currentScreen: 'loading',
  lessonParams: null,
  audioReady: false
};

// ── Screen Registry ───────────────────────────────────────────────────────────
const SCREENS = ['loading', 'map', 'lesson', 'profile', 'parent'];

// ── Navigate function ─────────────────────────────────────────────────────────
export function navigate(screen, params = {}) {
  if (!SCREENS.includes(screen)) {
    console.warn(`Unknown screen: ${screen}`);
    return;
  }

  const prevScreen = state.currentScreen;
  state.currentScreen = screen;

  // Hide all screens and clear their content to remove any inputs from the DOM
  SCREENS.forEach(id => {
    const el = document.getElementById(`${id}-screen`);
    if (el) {
      el.classList.remove('active');
      if (id !== 'loading' && id !== screen) {
        // Blur any focused input before removing it
        const focused = el.querySelector(':focus');
        if (focused) focused.blur();
        el.innerHTML = '';
      }
    }
  });

  // Show target screen
  const targetEl = document.getElementById(`${screen}-screen`);
  if (targetEl) {
    // Render screen content
    if (screen === 'map') {
      renderMap(navigate, null);
    } else if (screen === 'lesson') {
      state.lessonParams = params;
      renderLesson(navigate, params);
    } else if (screen === 'profile') {
      renderProfile(navigate);
    } else if (screen === 'parent') {
      renderParent(navigate);
    }

    // Activate
    requestAnimationFrame(() => {
      targetEl.classList.add('active');
    });
  }

  // Update URL hash
  if (screen !== 'loading') {
    history.replaceState(null, '', `#${screen}`);
  }
}

// ── Get Progress ───────────────────────────────────────────────────────────────
export function getProgress() {
  const { getProgress: gp } = window.__progress || {};
  if (gp) return gp();
  return {};
}

// ── Save Progress ──────────────────────────────────────────────────────────────
export function saveProgress(moduleId, lessonId, stars) {
  const { saveLesson } = window.__progress || {};
  if (saveLesson) saveLesson(moduleId, lessonId, stars);
}

// ── Init Audio on first user gesture ──────────────────────────────────────────
function initAudioOnGesture() {
  if (state.audioReady) return;
  state.audioReady = true;
  audio.init().then(() => {
    audio.resume();
  }).catch(() => {});
  document.removeEventListener('touchstart', initAudioOnGesture);
  document.removeEventListener('mousedown', initAudioOnGesture);
  document.removeEventListener('keydown', initAudioOnGesture);
}

// ── Service Worker Registration ────────────────────────────────────────────────
async function registerServiceWorker() {
  // Skipped inside the Android app: its files ship in the APK, and this cache-first worker
  // would keep serving old lessons after an update. Plain-HTTP pages (the Jetson) have no
  // navigator.serviceWorker at all, so the guard below also covers them.
  if ('serviceWorker' in navigator && location.hostname !== 'appassets.androidplatform.net') {
    try {
      const reg = await navigator.serviceWorker.register('sw.js');
      console.log('[App] Service worker registered:', reg.scope);
    } catch (err) {
      console.warn('[App] SW registration failed:', err);
    }
  }
}

// ── Hash Router ───────────────────────────────────────────────────────────────
function handleHashChange() {
  const hash = window.location.hash.replace('#', '');
  if (hash && SCREENS.includes(hash) && hash !== 'loading') {
    navigate(hash);
  }
}

// ── App Initialization ─────────────────────────────────────────────────────────
async function init() {
  // Register audio listeners
  document.addEventListener('touchstart', initAudioOnGesture, { passive: true });
  document.addEventListener('mousedown', initAudioOnGesture);

  // Register service worker
  registerServiceWorker();

  // Hash routing
  window.addEventListener('hashchange', handleHashChange);

  // Check for existing user
  const user = getCurrentUser();
  state.currentUser = user;

  // Show loading screen briefly, then navigate
  const loadingEl = document.getElementById('loading-screen');
  if (loadingEl) loadingEl.classList.add('active');

  // Minimum loading time for UX
  await new Promise(resolve => setTimeout(resolve, 1500));

  // Hide loading
  if (loadingEl) {
    loadingEl.style.transition = 'opacity 0.5s ease';
    loadingEl.style.opacity = '0';
    setTimeout(() => loadingEl.classList.remove('active'), 500);
  }

  // Navigate to appropriate screen
  if (!user) {
    navigate('profile');
  } else {
    const hash = window.location.hash.replace('#', '');
    if (hash && SCREENS.includes(hash) && hash !== 'loading') {
      navigate(hash);
    } else {
      navigate('map');
    }
  }
}

// ── Start App ─────────────────────────────────────────────────────────────────
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// ── Expose globals for debugging ──────────────────────────────────────────────
window.__kukApp = { state, navigate, audio };
