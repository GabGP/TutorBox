// Q'uq' the Quetzal - Guide Character
// Drawn programmatically using SVG

class Kuk {
  constructor(container) {
    this.container = typeof container === 'string'
      ? document.querySelector(container)
      : container;
    this._el = null;
    this._bubble = null;
    this._bubbleTimer = null;
    this._animClass = '';
    this._visible = false;
    this._bouncing = false;
  }

  render() {
    if (this._el) return;

    // Main Kuk element
    this._el = document.createElement('div');
    this._el.className = 'kuk-guide';
    this._el.setAttribute('aria-label', "Q'uq' el quetzal");
    this._el.innerHTML = this._svgKuk();
    this._el.addEventListener('click', () => this._onClick());
    this._el.addEventListener('touchend', e => { e.preventDefault(); this._onClick(); });

    // Speech bubble
    this._bubble = document.createElement('div');
    this._bubble.className = 'kuk-speech-bubble';

    if (this.container) {
      this.container.appendChild(this._bubble);
      this.container.appendChild(this._el);
    } else {
      document.body.appendChild(this._bubble);
      document.body.appendChild(this._el);
    }

    this._visible = true;
    this._startBounce();
  }

  _svgKuk(size = 90) {
    return `<svg viewBox="0 0 100 130" xmlns="http://www.w3.org/2000/svg">
      <!-- Tail feathers -->
      <ellipse cx="50" cy="118" rx="4.5" ry="18" fill="#1B5E20" transform="rotate(-18,50,118)"/>
      <ellipse cx="50" cy="120" rx="4.5" ry="22" fill="#2E7D32"/>
      <ellipse cx="50" cy="118" rx="4.5" ry="18" fill="#1B5E20" transform="rotate(18,50,118)"/>
      <ellipse cx="48" cy="116" rx="3" ry="16" fill="#00E676" transform="rotate(-8,48,116)"/>
      <ellipse cx="52" cy="116" rx="3" ry="16" fill="#00E676" transform="rotate(8,52,116)"/>
      <!-- Body -->
      <ellipse cx="50" cy="78" rx="22" ry="28" fill="#2E7D32"/>
      <!-- Red chest -->
      <ellipse cx="50" cy="86" rx="15" ry="18" fill="#C62828"/>
      <ellipse cx="50" cy="90" rx="11" ry="12" fill="#EF5350"/>
      <!-- Left wing -->
      <ellipse cx="28" cy="75" rx="13" ry="20" fill="#1B5E20" transform="rotate(-22,28,75)"/>
      <ellipse cx="30" cy="77" rx="8" ry="14" fill="#4CAF50" transform="rotate(-22,30,77)"/>
      <!-- Right wing -->
      <ellipse cx="72" cy="75" rx="13" ry="20" fill="#1B5E20" transform="rotate(22,72,75)"/>
      <ellipse cx="70" cy="77" rx="8" ry="14" fill="#4CAF50" transform="rotate(22,70,77)"/>
      <!-- Head -->
      <circle cx="50" cy="44" r="22" fill="#2E7D32"/>
      <!-- Crest -->
      <ellipse cx="44" cy="26" rx="4" ry="10" fill="#4CAF50" transform="rotate(-18,44,26)"/>
      <ellipse cx="50" cy="23" rx="4" ry="12" fill="#69F0AE"/>
      <ellipse cx="56" cy="26" rx="4" ry="10" fill="#4CAF50" transform="rotate(18,56,26)"/>
      <!-- Eyes -->
      <circle cx="42" cy="42" r="8.5" fill="white"/>
      <circle cx="58" cy="42" r="8.5" fill="white"/>
      <circle cx="43.5" cy="43" r="5" fill="#1A237E"/>
      <circle cx="59.5" cy="43" r="5" fill="#1A237E"/>
      <circle cx="44" cy="42" r="2.5" fill="black"/>
      <circle cx="60" cy="42" r="2.5" fill="black"/>
      <circle cx="44.5" cy="41" r="1.2" fill="white"/>
      <circle cx="60.5" cy="41" r="1.2" fill="white"/>
      <!-- Beak -->
      <path d="M 44 53 Q 50 61 56 53 L 50 58 Z" fill="#FFA000"/>
      <!-- Cheek blush -->
      <ellipse cx="36" cy="48" rx="5" ry="3.5" fill="rgba(255,100,100,0.35)"/>
      <ellipse cx="64" cy="48" rx="5" ry="3.5" fill="rgba(255,100,100,0.35)"/>
    </svg>`;
  }

  _onClick() {
    this.celebrate();
    this.say('¡Hola! ¡Aprendamos matemáticas juntos!');
  }

  _startBounce() {
    if (!this._el) return;
    this._el.style.animation = 'kukBounce 2s ease-in-out infinite';
  }

  /**
   * Play celebration animation
   */
  celebrate() {
    if (!this._el) return;
    this._el.style.animation = 'none';
    void this._el.offsetWidth;
    this._el.style.animation = 'victoryBurst 0.5s cubic-bezier(0.34,1.56,0.64,1), kukBounce 2s ease-in-out 0.5s infinite';

    // Spin briefly
    const svg = this._el.querySelector('svg');
    if (svg) {
      svg.style.transition = 'transform 0.4s ease';
      svg.style.transform = 'rotate(360deg)';
      setTimeout(() => {
        svg.style.transform = '';
      }, 400);
    }
  }

  /**
   * Gentle nod/encourage animation
   */
  encourage() {
    if (!this._el) return;
    this._el.style.animation = 'none';
    void this._el.offsetWidth;
    this._el.style.animation = 'feedbackCorrect 0.4s ease, kukBounce 2s ease-in-out 0.4s infinite';
  }

  /**
   * Point Kuk toward a location on screen
   */
  point(x, y) {
    if (!this._el) return;
    const rect = this._el.getBoundingClientRect();
    const kukX = rect.left + rect.width / 2;
    const kukY = rect.top + rect.height / 2;
    const angle = Math.atan2(y - kukY, x - kukX) * (180 / Math.PI);

    const svg = this._el.querySelector('svg');
    if (svg) {
      const flipX = x < kukX ? -1 : 1;
      svg.style.transform = `scaleX(${flipX})`;
    }
  }

  /**
   * Show speech bubble with text, optionally speak it
   */
  say(text, audioKey) {
    if (!this._bubble) return;

    this._bubble.textContent = text;
    this._bubble.classList.add('visible');

    // Auto-hide after delay
    if (this._bubbleTimer) clearTimeout(this._bubbleTimer);
    this._bubbleTimer = setTimeout(() => {
      this._bubble.classList.remove('visible');
    }, Math.max(2500, text.length * 60));
  }

  hide() {
    if (this._el) {
      this._el.style.opacity = '0';
      this._el.style.pointerEvents = 'none';
    }
    if (this._bubble) this._bubble.classList.remove('visible');
    this._visible = false;
  }

  show() {
    if (this._el) {
      this._el.style.opacity = '1';
      this._el.style.pointerEvents = 'all';
    }
    this._visible = true;
  }

  destroy() {
    if (this._bubbleTimer) clearTimeout(this._bubbleTimer);
    if (this._el && this._el.parentNode) this._el.parentNode.removeChild(this._el);
    if (this._bubble && this._bubble.parentNode) this._bubble.parentNode.removeChild(this._bubble);
    this._el = null;
    this._bubble = null;
  }

  get element() { return this._el; }
  get isVisible() { return this._visible; }
}

// Create global Q'uq' instance
const kuk = new Kuk(document.body);
export default kuk;
