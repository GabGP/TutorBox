// Parent Dashboard Screen
// PIN-protected analytics and progress view

import { getCurrentUser } from '../data/progress.js';
import { MODULES } from '../data/modules.js';

const CNB_DESCRIPTIONS = {
  m1: 'Ubicación espacial: arriba, abajo, adentro, afuera, cerca, lejos',
  m2: 'Patrones y secuencias con elementos del entorno cultural maya',
  m3: 'Conjuntos, clasificación y comparación de cantidades',
  m4: 'Números del 1 al 9, suma y resta con objetos concretos',
  m5: 'Resolución de problemas del contexto cotidiano guatemalteco',
  m6: 'Identificación de figuras geométricas planas en el entorno',
  m7: 'Medición del tiempo: horas, días y calendario'
};

export function renderParent(navigate) {
  const screen = document.getElementById('parent-screen');
  screen.innerHTML = '';

  const user = getCurrentUser();

  // Build PIN entry screen first
  renderPinEntry(screen, navigate, user);
}

function renderPinEntry(screen, navigate, user) {
  // Header
  const header = document.createElement('div');
  header.className = 'parent-header';

  const backBtn = document.createElement('button');
  backBtn.className = 'parent-back-btn';
  backBtn.textContent = '←';
  backBtn.addEventListener('click', () => navigate('map'));
  backBtn.addEventListener('touchend', e => { e.preventDefault(); navigate('map'); });
  header.appendChild(backBtn);

  const title = document.createElement('div');
  title.className = 'parent-title';
  title.textContent = '👨‍👩‍👧 Panel de Padres';
  header.appendChild(title);
  screen.appendChild(header);

  // PIN entry
  const pinScreen = document.createElement('div');
  pinScreen.className = 'pin-screen';
  pinScreen.style.flex = '1';

  const pinTitle = document.createElement('div');
  pinTitle.style.cssText = 'color:white; font-size:1.2rem; font-weight:800; text-align:center;';
  pinTitle.textContent = '🔒 Ingresa tu PIN de 4 dígitos';
  pinScreen.appendChild(pinTitle);

  const pinSubtitle = document.createElement('div');
  pinSubtitle.style.cssText = 'color:rgba(255,255,255,0.6); font-size:0.85rem; font-weight:600; text-align:center;';
  pinSubtitle.textContent = 'O presiona "Sin PIN" si no configuraste uno';
  pinScreen.appendChild(pinSubtitle);

  // PIN dots
  const dotsEl = document.createElement('div');
  dotsEl.className = 'pin-dots';
  const dots = [1,2,3,4].map(() => {
    const d = document.createElement('div');
    d.className = 'pin-dot';
    dotsEl.appendChild(d);
    return d;
  });
  pinScreen.appendChild(dotsEl);

  // PIN keypad
  let pinValue = '';

  const keypad = document.createElement('div');
  keypad.className = 'pin-keypad';

  const keys = [1,2,3,4,5,6,7,8,9,'⌫',0,'✓'];
  keys.forEach(k => {
    const btn = document.createElement('div');
    btn.className = 'pin-key' + (k === '⌫' || k === '✓' ? ' delete' : '');
    btn.textContent = k;
    if (k === '') { keypad.appendChild(btn); return; }

    const onPress = () => {
      if (k === '⌫') {
        pinValue = pinValue.slice(0,-1);
      } else if (k === '✓') {
        doVerify(pinValue);
      } else if (pinValue.length < 4) {
        pinValue += String(k);
      }
      // Update dots
      dots.forEach((d, i) => {
        d.classList.toggle('filled', i < pinValue.length);
      });
    };

    btn.addEventListener('click', onPress);
    btn.addEventListener('touchend', e => { e.preventDefault(); onPress(); });
    keypad.appendChild(btn);
  });

  pinScreen.appendChild(keypad);

  // No PIN button
  const noPinBtn = document.createElement('button');
  noPinBtn.className = 'btn-large';
  noPinBtn.style.cssText = 'background:rgba(255,255,255,0.15); border:1px solid rgba(255,255,255,0.3); color:white; max-width:260px;';
  noPinBtn.textContent = 'Sin PIN - Solo ver';
  noPinBtn.addEventListener('click', () => doVerify(''));
  noPinBtn.addEventListener('touchend', e => { e.preventDefault(); doVerify(''); });
  pinScreen.appendChild(noPinBtn);

  // Error message
  const errorEl = document.createElement('div');
  errorEl.style.cssText = 'color:#EF9A9A; font-size:0.9rem; font-weight:700; min-height:24px;';
  pinScreen.appendChild(errorEl);

  screen.appendChild(pinScreen);

  function doVerify(pin) {
    if (!user) {
      showDashboard(screen, navigate, null, {});
      return;
    }

    if (!pin) {
      showDashboard(screen, navigate, user, {});
      return;
    }

    if (!user.parentPin || user.parentPin === pin) {
      screen.innerHTML = '';
      showDashboard(screen, navigate, user, {});
    } else {
      errorEl.textContent = '❌ PIN incorrecto. Intenta de nuevo.';
      pinValue = '';
      dots.forEach(d => d.classList.remove('filled'));
      setTimeout(() => errorEl.textContent = '', 2000);
    }
  }
}

async function showDashboard(screen, navigate, user, opts) {
  const { getProgress, getTotalStars } = await import('../data/progress.js');
  const localProgress = getProgress();
  const localStars = getTotalStars();
  const summary = null;
  const recent = null;

  // ── Header ──────────────────────────────────────────────────────────────
  const header = document.createElement('div');
  header.className = 'parent-header';

  const backBtn = document.createElement('button');
  backBtn.className = 'parent-back-btn';
  backBtn.textContent = '←';
  backBtn.addEventListener('click', () => navigate('map'));
  backBtn.addEventListener('touchend', e => { e.preventDefault(); navigate('map'); });
  header.appendChild(backBtn);

  const titleEl = document.createElement('div');
  titleEl.className = 'parent-title';
  titleEl.textContent = `📊 Progreso de ${user?.name || 'tu hijo/a'}`;
  header.appendChild(titleEl);

  screen.appendChild(header);

  const content = document.createElement('div');
  content.className = 'parent-content';
  screen.appendChild(content);

  // ── Summary Card ─────────────────────────────────────────────────────────
  const summaryCard = document.createElement('div');
  summaryCard.className = 'parent-card';

  const totalStars = summary?.totalStars ?? localStars;
  const totalTime = summary?.totalTimeSeconds ?? 0;
  const lessonsCompleted = summary?.lessonsCompleted ?? Object.values(localProgress).reduce((sum, mod) => sum + Object.keys(mod).length, 0);
  const modulesCompleted = summary?.modulesCompleted ?? Object.keys(localProgress).length;

  summaryCard.innerHTML = `
    <div class="parent-card-title">📈 Resumen General</div>
    <div class="parent-stat">
      <span class="parent-stat-label">⭐ Estrellas ganadas</span>
      <span class="parent-stat-value">${totalStars}</span>
    </div>
    <div class="parent-stat">
      <span class="parent-stat-label">📚 Lecciones completadas</span>
      <span class="parent-stat-value">${lessonsCompleted}</span>
    </div>
    <div class="parent-stat">
      <span class="parent-stat-label">🌍 Mundos explorados</span>
      <span class="parent-stat-value">${modulesCompleted} / 7</span>
    </div>
    <div class="parent-stat">
      <span class="parent-stat-label">⏱️ Tiempo total</span>
      <span class="parent-stat-value">${formatTime(totalTime)}</span>
    </div>
  `;
  content.appendChild(summaryCard);

  // ── Activity Chart (last 7 days) ──────────────────────────────────────────
  const chartCard = document.createElement('div');
  chartCard.className = 'parent-card';

  const chartTitle = document.createElement('div');
  chartTitle.className = 'parent-card-title';
  chartTitle.textContent = '📅 Actividad (últimos 7 días)';
  chartCard.appendChild(chartTitle);

  const barChart = document.createElement('div');
  barChart.className = 'bar-chart';

  // Generate last 7 days
  const days = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    days.push({
      date: d.toISOString().split('T')[0],
      label: ['D','L','M','M','J','V','S'][d.getDay()]
    });
  }

  const dailyMap = {};
  if (recent?.dailySessions) {
    recent.dailySessions.forEach(s => { dailyMap[s.date] = s.duration; });
  }
  const starMap = {};
  if (recent?.dailyStars) {
    recent.dailyStars.forEach(s => { starMap[s.date] = s.stars; });
  }

  const maxDuration = Math.max(1, ...days.map(d => dailyMap[d.date] || 0));

  days.forEach(day => {
    const wrap = document.createElement('div');
    wrap.className = 'bar-chart-wrap';

    const bar = document.createElement('div');
    bar.className = 'bar-chart-bar';
    const duration = dailyMap[day.date] || 0;
    const heightPct = Math.max(5, (duration / maxDuration) * 100);
    bar.style.height = `${heightPct}%`;

    // Show stars on bar
    const stars = starMap[day.date] || 0;
    if (stars > 0) {
      bar.title = `${stars} estrellas`;
      bar.style.background = 'linear-gradient(180deg, #FFD700, #FFA000)';
    }

    const label = document.createElement('div');
    label.className = 'bar-chart-label';
    label.textContent = day.label;

    wrap.appendChild(bar);
    wrap.appendChild(label);
    barChart.appendChild(wrap);
  });
  chartCard.appendChild(barChart);
  content.appendChild(chartCard);

  // ── Module Completion ──────────────────────────────────────────────────────
  const moduleCard = document.createElement('div');
  moduleCard.className = 'parent-card';
  moduleCard.innerHTML = '<div class="parent-card-title">🌍 Progreso por Módulo CNB</div>';

  MODULES.forEach(mod => {
    const modData = localProgress[mod.id] || {};
    const completed = Object.values(modData).filter(l => l.stars > 0).length;
    const pct = mod.totalLessons > 0 ? Math.round((completed / mod.totalLessons) * 100) : 0;

    const row = document.createElement('div');
    row.className = 'module-completion-row';
    row.innerHTML = `
      <span class="module-completion-emoji">${mod.emoji}</span>
      <div class="module-completion-bar-track">
        <div class="module-completion-fill" style="width:${pct}%; background:${mod.color}"></div>
      </div>
      <span class="module-completion-pct">${pct}%</span>
    `;
    moduleCard.appendChild(row);
  });
  content.appendChild(moduleCard);

  // ── CNB Competencias ───────────────────────────────────────────────────────
  const cnbCard = document.createElement('div');
  cnbCard.className = 'parent-card';
  cnbCard.innerHTML = '<div class="parent-card-title">📖 Competencias CNB (1° Primaria)</div>';

  MODULES.forEach(mod => {
    const desc = document.createElement('div');
    desc.style.cssText = 'padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.08); font-size:0.82rem;';
    desc.innerHTML = `
      <span style="color:var(--color-gold); font-weight:700;">${mod.emoji} ${mod.name}: </span>
      <span style="color:rgba(255,255,255,0.75);">${CNB_DESCRIPTIONS[mod.id]}</span>
    `;
    cnbCard.appendChild(desc);
  });
  content.appendChild(cnbCard);

  // ── Export Button ──────────────────────────────────────────────────────────
  const exportCard = document.createElement('div');
  exportCard.className = 'parent-card';
  exportCard.innerHTML = '<div class="parent-card-title">📤 Compartir Progreso</div>';

  const exportBtn = document.createElement('button');
  exportBtn.className = 'btn-large btn-primary';
  exportBtn.style.cssText = 'margin:0; font-size:0.95rem;';
  exportBtn.innerHTML = '📋 Copiar reporte';
  exportBtn.addEventListener('click', () => exportProgress(user, localProgress, localStars, lessonsCompleted));
  exportCard.appendChild(exportBtn);
  content.appendChild(exportCard);

  // Add bottom padding
  const pad = document.createElement('div');
  pad.style.height = '40px';
  content.appendChild(pad);
}

function formatTime(seconds) {
  if (!seconds) return '0 min';
  const mins = Math.floor(seconds / 60);
  const hrs = Math.floor(mins / 60);
  if (hrs > 0) return `${hrs}h ${mins % 60}min`;
  return `${mins} min`;
}

function exportProgress(user, progress, stars, lessons) {
  const report = [
    `=== Reporte de ${user?.name || 'Estudiante'} ===`,
    `Fecha: ${new Date().toLocaleDateString('es-GT')}`,
    `Estrellas totales: ${stars}`,
    `Lecciones completadas: ${lessons}`,
    '',
    'Progreso por módulo:',
    ...MODULES.map(mod => {
      const modData = progress[mod.id] || {};
      const done = Object.keys(modData).length;
      return `  ${mod.emoji} ${mod.name}: ${done}/${mod.totalLessons} lecciones`;
    }),
    '',
    "App: Matemáticas 2º con Q'uq' - Guatemala"
  ].join('\n');

  if (navigator.share) {
    navigator.share({ title: "Mi progreso en Q'uq' 2º", text: report }).catch(() => {});
  } else {
    navigator.clipboard?.writeText(report).then(() => alert('¡Reporte copiado!')).catch(() => {
      alert(report);
    });
  }
}
