// Touch/Mouse Event Normalizer
// Handles both touch and mouse events for cross-device compatibility

export class TouchHandler {
  constructor(element) {
    this.el = element;
    this._tapCb = null;
    this._dragStartCb = null;
    this._dragMoveCb = null;
    this._dragEndCb = null;
    this._traceCb = null;

    this._isDragging = false;
    this._startPos = null;
    this._tracing = false;

    this._bound = {};
    this._init();
  }

  _init() {
    this._bound.touchstart = this._onTouchStart.bind(this);
    this._bound.touchmove = this._onTouchMove.bind(this);
    this._bound.touchend = this._onTouchEnd.bind(this);
    this._bound.mousedown = this._onMouseDown.bind(this);
    this._bound.mousemove = this._onMouseMove.bind(this);
    this._bound.mouseup = this._onMouseUp.bind(this);

    this.el.addEventListener('touchstart', this._bound.touchstart, { passive: false });
    this.el.addEventListener('touchmove', this._bound.touchmove, { passive: false });
    this.el.addEventListener('touchend', this._bound.touchend, { passive: false });
    this.el.addEventListener('mousedown', this._bound.mousedown);
    this.el.addEventListener('mousemove', this._bound.mousemove);
    this.el.addEventListener('mouseup', this._bound.mouseup);
  }

  _getPos(event, touch) {
    const rect = this.el.getBoundingClientRect();
    const src = touch || event;

    // Coordenadas relativas al contenedor visual (CSS pixels)
    const cssX = src.clientX - rect.left;
    const cssY = src.clientY - rect.top;

    // Factor de escala: resolución interna real / tamaño mostrado en pantalla
    // Compensa el estiramiento causado por max-height: 80vh o flexbox
    const scaleX = this.el.width / rect.width;
    const scaleY = this.el.height / rect.height;

    // DPR usado en canvas.js para pantallas retina
    const dpr = window.devicePixelRatio || 1;

    return {
      x: (cssX * scaleX) / dpr,
      y: (cssY * scaleY) / dpr
    };
  }

  _onTouchStart(e) {
    e.preventDefault();
    const pos = this._getPos(e, e.touches[0]);
    this._isDragging = true;
    this._startPos = pos;
    if (this._dragStartCb) this._dragStartCb(pos);
    if (this._traceCb) { this._tracing = true; this._traceCb({ type: 'start', ...pos }); }
  }

  _onTouchMove(e) {
    e.preventDefault();
    if (!this._isDragging) return;
    const pos = this._getPos(e, e.touches[0]);
    if (this._dragMoveCb) this._dragMoveCb(pos);
    if (this._tracing && this._traceCb) this._traceCb({ type: 'move', ...pos });
  }

  _onTouchEnd(e) {
    e.preventDefault();
    const changedTouch = e.changedTouches[0];
    const pos = this._getPos(e, changedTouch);
    const wasDragging = this._isDragging;
    this._isDragging = false;

    if (this._dragEndCb && wasDragging) this._dragEndCb(pos);
    if (this._tracing && this._traceCb) { this._traceCb({ type: 'end', ...pos }); this._tracing = false; }

    // Detect tap (short press, no significant move)
    if (this._tapCb && this._startPos) {
      const dx = Math.abs(pos.x - this._startPos.x);
      const dy = Math.abs(pos.y - this._startPos.y);
      if (dx < 15 && dy < 15) this._tapCb(pos);
    }
    this._startPos = null;
  }

  _onMouseDown(e) {
    const pos = this._getPos(e);
    this._isDragging = true;
    this._startPos = pos;
    if (this._dragStartCb) this._dragStartCb(pos);
    if (this._traceCb) { this._tracing = true; this._traceCb({ type: 'start', ...pos }); }
  }

  _onMouseMove(e) {
    if (!this._isDragging) return;
    const pos = this._getPos(e);
    if (this._dragMoveCb) this._dragMoveCb(pos);
    if (this._tracing && this._traceCb) this._traceCb({ type: 'move', ...pos });
  }

  _onMouseUp(e) {
    const pos = this._getPos(e);
    const wasDragging = this._isDragging;
    this._isDragging = false;

    if (this._dragEndCb && wasDragging) this._dragEndCb(pos);
    if (this._tracing && this._traceCb) { this._traceCb({ type: 'end', ...pos }); this._tracing = false; }

    if (this._tapCb && this._startPos) {
      const dx = Math.abs(pos.x - this._startPos.x);
      const dy = Math.abs(pos.y - this._startPos.y);
      if (dx < 15 && dy < 15) this._tapCb(pos);
    }
    this._startPos = null;
  }

  onTap(callback) { this._tapCb = callback; return this; }
  onDragStart(callback) { this._dragStartCb = callback; return this; }
  onDragMove(callback) { this._dragMoveCb = callback; return this; }
  onDragEnd(callback) { this._dragEndCb = callback; return this; }
  onTrace(callback) { this._traceCb = callback; return this; }

  destroy() {
    this.el.removeEventListener('touchstart', this._bound.touchstart);
    this.el.removeEventListener('touchmove', this._bound.touchmove);
    this.el.removeEventListener('touchend', this._bound.touchend);
    this.el.removeEventListener('mousedown', this._bound.mousedown);
    this.el.removeEventListener('mousemove', this._bound.mousemove);
    this.el.removeEventListener('mouseup', this._bound.mouseup);
    this._tapCb = null;
    this._dragStartCb = null;
    this._dragMoveCb = null;
    this._dragEndCb = null;
    this._traceCb = null;
  }
}
