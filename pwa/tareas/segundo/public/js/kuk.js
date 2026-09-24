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

  _svgKuk() {
    // The one drawing of Q'uq' (icons/quq.svg), shared by every screen.
    return '<img src="icons/quq.svg" alt="" draggable="false" style="width:100%;height:100%;object-fit:contain" />';
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
