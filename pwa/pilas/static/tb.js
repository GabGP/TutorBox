/* TutorBox Pilas — shared client helpers. Pages are served by the FastAPI backend, so every call
   goes to the same origin (/api/v1) with the bearer token from POST /auth/login. */
const API = '/api/v1';
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const ERR = {
  0: 'Sin conexión con TutorBox', 401: 'Usuario o PIN incorrecto', 403: 'No tienes permiso para esto',
  404: 'No se encontró', 409: 'Ya existe', 422: 'Usuario de 3 a 32 letras o números y PIN de 4 a 8 números',
  429: 'Demasiados intentos, espera un momento', 502: 'El modelo no respondió',
};

async function api(method, path, body, auth = true) {
  const headers = { 'Content-Type': 'application/json' };
  const token = localStorage.getItem('tb_token');
  if (auth && token) headers.Authorization = 'Bearer ' + token;
  let r;
  try { r = await fetch(API + path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) }); }
  catch { throw Object.assign(new Error(ERR[0]), { status: 0 }); }
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw Object.assign(new Error(ERR[r.status] || data.detail || `Error ${r.status}`), { status: r.status, detail: data.detail });
  return data;
}

const auth = {
  async login(username, pin) {
    const r = await api('POST', '/auth/login', { username, pin }, false);
    localStorage.setItem('tb_token', r.session_id);
    return r; // r.must_change_pin -> askNewPin()
  },
  async logout() {
    try { await api('POST', '/auth/logout'); } catch {}
    localStorage.removeItem('tb_token');
  },
  async me() { // restores the session on reload; null when there is no valid token
    if (!localStorage.getItem('tb_token')) return null;
    try { return await api('GET', '/users/me'); }
    catch (e) { if (e.status === 401) localStorage.removeItem('tb_token'); return null; }
  },
  async changePin(username, current_pin, new_pin) { // the backend revokes the session: log in again
    await api('PATCH', '/users/me/pin', { current_pin, new_pin });
    return auth.login(username, new_pin);
  },
};

/* Login form with ids #user #pin #enter #lerr (+ #signup for students) and the forced PIN change
   form #npin #npin2 #setpin #perr. `show(step)` is the page's own section switcher. */
function bindLogin({ show, onDone, signup = false }) {
  const err = m => { $('lerr').textContent = m; $('lerr').hidden = !m; };
  let mode = 'login';
  if (signup) $('signup').onclick = () => {
    mode = mode === 'login' ? 'signup' : 'login';
    $('enter').textContent = mode === 'login' ? 'Entrar' : 'Crear cuenta y entrar';
    $('signup').textContent = mode === 'login' ? '¿Primera vez? Crear cuenta' : 'Ya tengo cuenta';
    err('');
  };
  $('enter').onclick = async () => {
    const username = $('user').value.trim(), pin = $('pin').value.trim();
    if (!username || !pin) return err('Escribe tu usuario y tu PIN');
    $('enter').disabled = true; err('');
    try {
      if (mode === 'signup') await api('POST', '/users/signup', { username, pin }, false);
      const r = await auth.login(username, pin);
      if (r.must_change_pin) return askNewPin(username, pin, show, onDone);
      onDone(await auth.me());
    } catch (e) { err(e.status === 409 ? 'Ese nombre ya está en uso, elige otro' : e.message); }
    finally { $('enter').disabled = false; }
  };
  $('pin').onkeydown = e => { if (e.key === 'Enter') $('enter').click(); };
}

function askNewPin(username, current, show, onDone) {
  show('pin');
  const err = m => { $('perr').textContent = m; $('perr').hidden = !m; };
  $('setpin').onclick = async () => {
    const a = $('npin').value.trim(), b = $('npin2').value.trim();
    if (a !== b) return err('Los dos PIN no coinciden');
    if (a === current) return err('El PIN nuevo debe ser diferente al temporal');
    $('setpin').disabled = true; err('');
    try { await auth.changePin(username, current, a); onDone(await auth.me()); }
    catch (e) { err(e.message); }
    finally { $('setpin').disabled = false; }
  };
}

/* Match to follow: ?s=<session id> pins one; otherwise the newest lobby/active session. */
const sessionPath = () => '/session/' + (new URLSearchParams(location.search).get('s') || 'current');

// ponytail: 1s polling; move to SSE/WebSocket if >30 clients lag
function poll(fn, ms = 1000) { (async function tick() { try { await fn(); } catch {} setTimeout(tick, ms); })(); }

/* Countdown ring: time_remaining is null after a backend restart (timers are in memory) -> hide. */
function ring(id, remaining, duration) {
  const el = $(id), none = remaining == null;
  el.hidden = none;
  if (none) return;
  const r = Math.ceil(remaining);
  el.firstElementChild.textContent = r;
  el.style.setProperty('--pct', 100 * remaining / duration);
  el.classList.toggle('low', r <= 5);
}

/* A–D option rows; counts optional (only known once the round is revealed). */
function bars(el, options, counts, total) {
  if (el.dataset.k !== JSON.stringify(options)) {
    el.dataset.k = JSON.stringify(options);
    el.innerHTML = ['A', 'B', 'C', 'D'].map(k => `<div class="bar"><span class="letter k-${k}">${k}</span><span class="txt">${esc(options[k])}</span><span class="track"><div class="k-${k}"></div></span><span class="n"></span></div>`).join('');
  }
  [...el.children].forEach((row, i) => {
    const v = counts ? counts['ABCD'[i]] : 0;
    row.children[2].firstChild.style.width = (total ? Math.round(100 * v / total) : 0) + '%';
    row.children[3].textContent = counts ? v : '';
  });
}
