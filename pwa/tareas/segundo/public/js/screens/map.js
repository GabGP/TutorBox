// Adventure Map Screen
// Shows 7 world nodes on a winding path

import { MODULES } from '../data/modules.js';
import { getProgress, getModuleStars, isModuleUnlocked, isLessonUnlockedById, getTotalStars } from '../data/progress.js';
import audio from '../engine/audio.js';

export function renderMap(navigate, currentProgress) {
  const screen = document.getElementById('map-screen');
  screen.innerHTML = '';

  const totalStars = getTotalStars();
  const progress = getProgress();

  // ── Header ──────────────────────────────────────────────────────────────
  const header = document.createElement('div');
  header.className = 'map-header';
  header.innerHTML = `
    <div class="map-stars-display">
      <span class="map-stars-icon">⭐</span>
      <span class="map-stars-count">${totalStars}</span>
    </div>
    <div class="map-title">¡Aventura con Q'uq'!</div>
    <div class="map-profile-btn" id="map-profile-btn" role="button" aria-label="Mi perfil">👤</div>
  `;
  screen.appendChild(header);

  // ── Scrollable world container ───────────────────────────────────────────
  const worldWrap = document.createElement('div');
  worldWrap.className = 'map-world';
  screen.appendChild(worldWrap);

  // ── SVG Path ────────────────────────────────────────────────────────────
  const nodesContainer = document.createElement('div');
  nodesContainer.className = 'world-nodes-container';
  nodesContainer.style.minHeight = '760px';
  worldWrap.appendChild(nodesContainer);

  // Node positions for a winding S-curve path (% of container width)
  const nodePositions = [
    { x: 50, y: 92 },  // M1 - bottom center
    { x: 78, y: 80 },  // M2 - right
    { x: 55, y: 67 },  // M3 - center
    { x: 22, y: 54 },  // M4 - left
    { x: 50, y: 40 },  // M5 - center
    { x: 76, y: 26 },  // M6 - right
    { x: 50, y: 12 },  // M7 - top center
  ];

  // Draw SVG path connecting nodes
  const svgNS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(svgNS, 'svg');
  svg.classList.add('map-path-svg');
  svg.setAttribute('viewBox', '0 0 100 100');
  svg.setAttribute('preserveAspectRatio', 'none');
  nodesContainer.appendChild(svg);

  // Draw winding dotted path
  const pathEl = document.createElementNS(svgNS, 'path');
  const d = nodePositions.map((p, i) => {
    if (i === 0) return `M ${p.x} ${p.y}`;
    const prev = nodePositions[i - 1];
    const cpx = (prev.x + p.x) / 2 + (i % 2 === 0 ? 15 : -15);
    const cpy = (prev.y + p.y) / 2;
    return `Q ${cpx} ${cpy} ${p.x} ${p.y}`;
  }).join(' ');

  pathEl.setAttribute('d', d);
  pathEl.setAttribute('fill', 'none');
  pathEl.setAttribute('stroke', 'rgba(255,255,255,0.6)');
  pathEl.setAttribute('stroke-width', '1.5');
  pathEl.setAttribute('stroke-dasharray', '3 3');
  svg.appendChild(pathEl);

  // ── World Nodes ──────────────────────────────────────────────────────────
  MODULES.forEach((mod, i) => {
    const pos = nodePositions[i];
    const modProgress = progress[mod.id] || {};
    const modStars = getModuleStars(mod.id);
    const maxStars = mod.totalLessons * 3;
    const unlocked = i === 0 || isModuleUnlocked(i);
    const completed = modStars >= maxStars * 0.5;

    const node = document.createElement('div');
    node.className = 'world-node' + (unlocked ? ' unlocked' : ' locked') + (completed ? ' completed' : '');
    node.style.left = `calc(${pos.x}% - 44px)`;
    node.style.top = `calc(${pos.y}% - 44px)`;
    node.style.backgroundColor = mod.color;
    node.style.animationDelay = `${i * 0.3}s`;
    node.setAttribute('role', 'button');
    node.setAttribute('aria-label', mod.world);

    // Stars earned display
    const starsEarned = Math.min(modStars, maxStars);
    const starsFrac = maxStars > 0 ? starsEarned / maxStars : 0;
    const starDisplay = '⭐'.repeat(Math.min(3, Math.floor(starsFrac * 3)));

    node.innerHTML = `
      <img class="world-node-icon" src="icons/worlds/${mod.id}.svg" alt="" draggable="false" />
      <div class="world-node-stars">
        ${[0,1,2].map(j => `<span class="world-node-star ${j < Math.floor(starsFrac * 3) ? 'earned' : ''}">★</span>`).join('')}
      </div>
      ${!unlocked ? '<span class="world-node-lock">🔒</span>' : ''}
    `;

    // World label
    const label = document.createElement('div');
    label.className = 'world-label';
    label.textContent = mod.name;
    node.appendChild(label);

    if (unlocked) {
      node.addEventListener('click', () => onWorldTap(mod, i, navigate));
      node.addEventListener('touchend', e => { e.preventDefault(); onWorldTap(mod, i, navigate); });
    }

    nodesContainer.appendChild(node);
  });

  // ── Kuk flying character on map ──────────────────────────────────────────
  const kukEl = document.createElement('div');
  kukEl.style.cssText = `
    position: absolute;
    width: 64px;
    height: 64px;
    left: calc(50% + 40px); /* beside world 1, so its picture stays visible */
    bottom: 70px;
    z-index: 15;
    animation: kukBounce 2s ease-in-out infinite;
    filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.3));
    pointer-events: none;
  `;
  kukEl.innerHTML = '<img src="icons/quq.svg" alt="" draggable="false" style="width:100%;height:100%;object-fit:contain" />';
  nodesContainer.appendChild(kukEl);

  // Parent dashboard button (bottom of screen)
  const parentBtn = document.createElement('div');
  parentBtn.style.cssText = `
    position: fixed;
    bottom: 20px;
    left: 16px;
    background: rgba(255,255,255,0.9);
    border-radius: 50%;
    width: 52px;
    height: 52px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    box-shadow: 0 4px 16px rgba(0,0,0,0.2);
    cursor: pointer;
    z-index: 30;
  `;
  parentBtn.textContent = '👨‍👩‍👧';
  parentBtn.setAttribute('aria-label', 'Panel de padres');
  parentBtn.addEventListener('click', () => navigate('parent'));
  parentBtn.addEventListener('touchend', e => { e.preventDefault(); navigate('parent'); });
  screen.appendChild(parentBtn);

  // Profile button handler
  document.getElementById('map-profile-btn')?.addEventListener('click', () => navigate('profile'));
}

function onWorldTap(mod, moduleIndex, navigate) {
  audio.playTap && audio.playTap();
  // Navigate to first unlocked lesson in this module
  const progress = getProgress();
  const modData = progress[mod.id] || {};

  let targetLesson = mod.lessons[0];
  for (const lesson of mod.lessons) {
    const lessonDone = (modData[lesson.id]?.stars || 0) > 0;
    if (!lessonDone) {
      targetLesson = lesson;
      break;
    }
  }

  navigate('lesson', { moduleId: mod.id, lessonId: targetLesson.id, module: mod, lesson: targetLesson });
}
