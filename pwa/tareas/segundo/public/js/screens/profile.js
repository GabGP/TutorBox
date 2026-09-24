// Profile Screen - Create/View child profile
// Avatar selection with trajes típicos guatemaltecos

import { getCurrentUser, setCurrentUser, getTotalStars, getModuleCompletion } from '../data/progress.js';
import { MODULES } from '../data/modules.js';
import audio from '../engine/audio.js';

// 6 Avatar definitions - kids in different trajes típicos
const AVATARS = [
  { id: 1, name: 'Ixchel', colors: { skin: '#C68642', traje: '#E91E63', hair: '#2C1810' } },
  { id: 2, name: 'Ajpu', colors: { skin: '#A0522D', traje: '#2196F3', hair: '#1A0A00' } },
  { id: 3, name: 'Ix', colors: { skin: '#D2691E', traje: '#4CAF50', hair: '#2C1810' } },
  { id: 4, name: 'Balam', colors: { skin: '#CD853F', traje: '#FF5722', hair: '#1A0A00' } },
  { id: 5, name: 'Kej', colors: { skin: '#C68642', traje: '#9C27B0', hair: '#2C1810' } },
  { id: 6, name: 'Tzikin', colors: { skin: '#A0522D', traje: '#FF9800', hair: '#1A0A00' } }
];

function renderAvatarSVG(avatar, size = 80) {
  const c = avatar.colors;
  return `<svg viewBox="0 0 80 100" xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}">
    <!-- Hair back -->
    <ellipse cx="40" cy="28" rx="24" ry="26" fill="${c.hair}"/>
    <!-- Face -->
    <ellipse cx="40" cy="32" rx="20" ry="22" fill="${c.skin}"/>
    <!-- Eyes -->
    <ellipse cx="33" cy="30" rx="4" ry="4.5" fill="white"/>
    <ellipse cx="47" cy="30" rx="4" ry="4.5" fill="white"/>
    <circle cx="33.5" cy="31" r="2.5" fill="#1A237E"/>
    <circle cx="47.5" cy="31" r="2.5" fill="#1A237E"/>
    <circle cx="34" cy="30.5" r="1.2" fill="black"/>
    <circle cx="48" cy="30.5" r="1.2" fill="black"/>
    <circle cx="34.5" cy="30" r="0.6" fill="white"/>
    <circle cx="48.5" cy="30" r="0.6" fill="white"/>
    <!-- Nose -->
    <ellipse cx="40" cy="36" rx="2" ry="1.5" fill="rgba(0,0,0,0.15)"/>
    <!-- Smile -->
    <path d="M 34 40 Q 40 46 46 40" fill="none" stroke="${c.hair}" stroke-width="1.8" stroke-linecap="round"/>
    <!-- Cheeks -->
    <ellipse cx="29" cy="37" rx="5" ry="3.5" fill="rgba(255,150,100,0.3)"/>
    <ellipse cx="51" cy="37" rx="5" ry="3.5" fill="rgba(255,150,100,0.3)"/>
    <!-- Traje body -->
    <path d="M 20 54 Q 40 48 60 54 L 65 100 L 15 100 Z" fill="${c.traje}"/>
    <!-- Traje collar pattern -->
    <path d="M 30 54 L 40 60 L 50 54" fill="none" stroke="rgba(255,255,255,0.6)" stroke-width="1.5"/>
    <!-- Neck -->
    <rect x="36" y="50" width="8" height="8" fill="${c.skin}"/>
    <!-- Hair front strands -->
    <ellipse cx="20" cy="30" rx="8" ry="16" fill="${c.hair}" transform="rotate(-15,20,30)"/>
    <ellipse cx="60" cy="30" rx="8" ry="16" fill="${c.hair}" transform="rotate(15,60,30)"/>
    <!-- Pattern on traje -->
    <rect x="35" y="65" width="4" height="4" fill="rgba(255,255,255,0.5)" rx="1"/>
    <rect x="42" y="70" width="4" height="4" fill="rgba(255,255,255,0.5)" rx="1"/>
    <rect x="35" y="75" width="4" height="4" fill="rgba(255,255,255,0.5)" rx="1"/>
  </svg>`;
}

export function renderProfile(navigate) {
  const screen = document.getElementById('profile-screen');
  screen.innerHTML = '';

  const currentUser = getCurrentUser();

  if (!currentUser) {
    renderCreateProfile(screen, navigate);
  } else {
    renderViewProfile(screen, navigate, currentUser);
  }
}

function renderCreateProfile(screen, navigate) {
  let selectedAvatar = AVATARS[0];
  let nameValue = '';

  // Back button
  const backBtn = document.createElement('button');
  backBtn.className = 'profile-back-btn';
  backBtn.textContent = '←';
  backBtn.style.display = 'none'; // Hide on first launch
  screen.appendChild(backBtn);

  // Title
  const title = document.createElement('div');
  title.className = 'profile-create-title';
  title.innerHTML = '👋 ¡Hola! ¿Cómo te llamas?';
  title.style.cssText = 'font-size:1.6rem; font-weight:900; color:white; text-align:center; text-shadow:1px 2px 4px rgba(0,0,0,0.3); margin-top:20px;';
  screen.appendChild(title);

  // Avatar grid
  const form = document.createElement('div');
  form.className = 'profile-create-form';

  const avatarTitle = document.createElement('div');
  avatarTitle.style.cssText = 'color:rgba(255,255,255,0.9); font-size:1rem; font-weight:700;';
  avatarTitle.textContent = '¡Elige tu personaje!';
  form.appendChild(avatarTitle);

  const grid = document.createElement('div');
  grid.className = 'profile-avatar-grid';

  const avatarOptions = [];
  AVATARS.forEach((av, i) => {
    const opt = document.createElement('div');
    opt.className = 'profile-avatar-option' + (i === 0 ? ' selected' : '');
    opt.innerHTML = renderAvatarSVG(av, 70);
    opt.addEventListener('click', () => {
      avatarOptions.forEach(o => o.classList.remove('selected'));
      opt.classList.add('selected');
      selectedAvatar = av;
      previewEl.innerHTML = renderAvatarSVG(av, 100);
      audio.playTap && audio.playTap();
    });
    opt.addEventListener('touchend', e => {
      e.preventDefault();
      avatarOptions.forEach(o => o.classList.remove('selected'));
      opt.classList.add('selected');
      selectedAvatar = av;
      previewEl.innerHTML = renderAvatarSVG(av, 100);
    });
    grid.appendChild(opt);
    avatarOptions.push(opt);
  });
  form.appendChild(grid);

  // Preview
  const previewEl = document.createElement('div');
  previewEl.style.cssText = 'width:100px; height:100px; margin:0 auto;';
  previewEl.innerHTML = renderAvatarSVG(AVATARS[0], 100);
  form.appendChild(previewEl);

  // Name input
  const nameLabel = document.createElement('div');
  nameLabel.style.cssText = 'color:rgba(255,255,255,0.9); font-size:1rem; font-weight:700;';
  nameLabel.textContent = '¿Cuál es tu nombre?';
  form.appendChild(nameLabel);

  const nameInput = document.createElement('input');
  nameInput.type = 'text';
  nameInput.className = 'input-field';
  nameInput.placeholder = 'Mi nombre...';
  nameInput.maxLength = 20;
  nameInput.autocomplete = 'off';
  nameInput.addEventListener('input', () => { nameValue = nameInput.value; });
  form.appendChild(nameInput);

  // PIN for parents
  const pinLabel = document.createElement('div');
  pinLabel.style.cssText = 'color:rgba(255,255,255,0.7); font-size:0.85rem; font-weight:600;';
  pinLabel.textContent = '🔒 PIN para padres (opcional)';
  form.appendChild(pinLabel);

  const pinInput = document.createElement('input');
  pinInput.type = 'password';
  pinInput.className = 'input-field';
  pinInput.placeholder = '4 dígitos...';
  pinInput.maxLength = 4;
  pinInput.inputMode = 'numeric';
  pinInput.style.cssText += 'font-size:1.6rem; letter-spacing:8px;';
  form.appendChild(pinInput);

  // Create button
  const createBtn = document.createElement('button');
  createBtn.className = 'btn-large btn-gold';
  createBtn.innerHTML = '✨ ¡Empezar la aventura!';
  createBtn.addEventListener('click', () => doCreate());
  createBtn.addEventListener('touchend', e => { e.preventDefault(); doCreate(); });
  form.appendChild(createBtn);

  screen.appendChild(form);

  function doCreate() {
    const name = nameInput.value.trim() || 'Estudiante';
    const pin = pinInput.value.trim();

    const user = { id: Date.now(), name, avatar: selectedAvatar.id, parentPin: pin || null };
    setCurrentUser(user);
    audio.playSuccess();
    navigate('map');
  }
}

function renderViewProfile(screen, navigate, user) {
  const avatar = AVATARS.find(a => a.id === user.avatar) || AVATARS[0];
  const totalStars = getTotalStars();

  // Back button
  const backBtn = document.createElement('button');
  backBtn.className = 'profile-back-btn';
  backBtn.textContent = '←';
  backBtn.addEventListener('click', () => navigate('map'));
  backBtn.addEventListener('touchend', e => { e.preventDefault(); navigate('map'); });
  screen.appendChild(backBtn);

  // Avatar large display
  const avatarBig = document.createElement('div');
  avatarBig.style.cssText = `
    width: 120px; height: 120px;
    border-radius: 50%;
    background: rgba(255,255,255,0.2);
    border: 4px solid rgba(255,255,255,0.5);
    display: flex; align-items: center; justify-content: center;
    overflow: hidden;
  `;
  avatarBig.innerHTML = renderAvatarSVG(avatar, 110);
  screen.appendChild(avatarBig);

  // Name
  const nameEl = document.createElement('div');
  nameEl.className = 'profile-name-display';
  nameEl.textContent = user.name || 'Estudiante';
  screen.appendChild(nameEl);

  // Stars field
  const starsTitle = document.createElement('div');
  starsTitle.style.cssText = 'color:rgba(255,255,255,0.9); font-weight:800; font-size:1rem;';
  starsTitle.textContent = `⭐ ${totalStars} estrellas ganadas`;
  screen.appendChild(starsTitle);

  const starsField = document.createElement('div');
  starsField.className = 'profile-stars-field';
  const starCount = Math.min(totalStars, 50);
  for (let i = 0; i < starCount; i++) {
    const s = document.createElement('span');
    s.className = 'profile-star-item';
    s.textContent = '⭐';
    s.style.animationDelay = `${i * 0.04}s`;
    starsField.appendChild(s);
  }
  if (starCount === 0) {
    starsField.innerHTML = '<span style="color:rgba(255,255,255,0.5); font-size:0.9rem;">¡Juega y gana estrellas!</span>';
  }
  screen.appendChild(starsField);

  // Module progress bars
  const progressTitle = document.createElement('div');
  progressTitle.style.cssText = 'color:rgba(255,255,255,0.9); font-weight:800; font-size:1rem; align-self:flex-start;';
  progressTitle.textContent = '📊 Mi progreso';
  screen.appendChild(progressTitle);

  const progressBars = document.createElement('div');
  progressBars.className = 'profile-module-progress';
  progressBars.style.width = '100%';

  MODULES.forEach(mod => {
    const pct = getModuleCompletion(mod.id, mod.totalLessons);
    const row = document.createElement('div');
    row.className = 'module-progress-bar';
    row.innerHTML = `
      <span class="module-progress-emoji">${mod.emoji}</span>
      <div class="module-progress-track">
        <div class="module-progress-fill" style="width:${pct}%"></div>
      </div>
    `;
    progressBars.appendChild(row);
  });
  screen.appendChild(progressBars);

  // Switch user / change avatar button
  const switchBtn = document.createElement('button');
  switchBtn.className = 'btn-large btn-secondary';
  switchBtn.style.cssText = 'margin-top:8px; background:rgba(255,255,255,0.2); border:2px solid rgba(255,255,255,0.4);';
  switchBtn.innerHTML = '🔄 Cambiar usuario';
  switchBtn.addEventListener('click', () => {
    setCurrentUser(null);
    renderProfile(navigate);
  });
  switchBtn.addEventListener('touchend', e => { e.preventDefault(); setCurrentUser(null); renderProfile(navigate); });
  screen.appendChild(switchBtn);

  // Parent access button
  const parentBtn = document.createElement('button');
  parentBtn.className = 'btn-large';
  parentBtn.style.cssText = 'background:rgba(255,255,255,0.15); border:2px solid rgba(255,255,255,0.3); color:white; margin-top:4px;';
  parentBtn.innerHTML = '👨‍👩‍👧 Ver panel de padres';
  parentBtn.addEventListener('click', () => navigate('parent'));
  parentBtn.addEventListener('touchend', e => { e.preventDefault(); navigate('parent'); });
  screen.appendChild(parentBtn);
}
