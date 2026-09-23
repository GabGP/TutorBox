// Small drawing helpers shared by the choice lessons (see choice-lesson.js).
// Every helper draws inside a box { x, y, w, h } in canvas (CSS pixel) coordinates.

export function center(box) {
  return { cx: box.x + box.w / 2, cy: box.y + box.h / 2 };
}

export function inset(box, fx, fy = fx) {
  return { x: box.x + box.w * fx, y: box.y + box.h * fy, w: box.w * (1 - 2 * fx), h: box.h * (1 - 2 * fy) };
}

/** `emoji` may also be a drawing function from art.js (ctx, cx, cy, size). */
// The one drawing of Q'uq' (icons/quq.svg) for canvas scenes. Located relative to this module so
// it works in the app, the APK and tests/preview.html; draws nothing until the image has loaded.
const QUQ = typeof Image === 'undefined'
  ? null
  : Object.assign(new Image(), { src: new URL('../../../icons/quq.svg', import.meta.url).href });

export function drawQuq(ctx, cx, cy, height) {
  if (!QUQ || !QUQ.complete || !QUQ.naturalWidth) return;
  const width = (height * QUQ.naturalWidth) / QUQ.naturalHeight;
  ctx.drawImage(QUQ, cx - width / 2, cy - height / 2, width, height);
}

export function drawEmoji(ctx, emoji, cx, cy, size) {
  if (typeof emoji === 'function') {
    emoji(ctx, cx, cy, size);
    return;
  }
  ctx.save();
  ctx.font = `${Math.round(size)}px sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(emoji, cx, cy);
  ctx.restore();
}

/**
 * Lays `count` copies of an item out in a tidy grid inside `box`, so a child can count them.
 * `item` is an emoji or a function (ctx, cx, cy, size) for things with no emoji (jocote, tortilla),
 * or a list of those to draw a mixed group.
 * The last `crossed` items are drawn faded with a red cross (things taken away).
 * `slots` sizes the grid for at least that many items: groups that are compared must share it,
 * or 2 big mangos look like more than 5 small ones.
 */
export function drawItems(ctx, item, count, box, { crossed = 0, maxSize = Infinity, slots = count } = {}) {
  if (count <= 0) return;
  const grid = Math.max(count, slots);
  const cols = grid <= 3 ? grid : grid <= 4 ? 2 : grid <= 9 ? 3 : 4;
  const rows = Math.ceil(grid / cols);
  const cell = Math.min(box.w / cols, box.h / rows);
  const size = Math.min(cell * 0.8, maxSize);
  const startX = box.x + (box.w - cols * cell) / 2 + cell / 2;
  const startY = box.y + (box.h - rows * cell) / 2 + cell / 2;
  for (let i = 0; i < count; i++) {
    const x = startX + (i % cols) * cell;
    const y = startY + Math.floor(i / cols) * cell;
    const taken = i >= count - crossed;
    ctx.save();
    if (taken) ctx.globalAlpha = 0.35;
    const it = Array.isArray(item) ? item[i] : item;
    if (typeof it === 'function') it(ctx, x, y, size);
    else drawEmoji(ctx, it, x, y, size);
    ctx.restore();
    if (taken) drawCross(ctx, x, y, size * 0.45);
  }
}

export function drawCross(ctx, cx, cy, r) {
  ctx.save();
  ctx.strokeStyle = '#D32F2F';
  ctx.lineWidth = Math.max(3, r * 0.22);
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(cx - r, cy - r); ctx.lineTo(cx + r, cy + r);
  ctx.moveTo(cx + r, cy - r); ctx.lineTo(cx - r, cy + r);
  ctx.stroke();
  ctx.restore();
}

export function drawNumeral(ctx, n, box, color = '#1F2A1F') {
  const { cx, cy } = center(box);
  ctx.save();
  ctx.fillStyle = color;
  ctx.font = `900 ${Math.round(Math.min(box.w, box.h) * 0.62)}px Nunito, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(String(n), cx, cy + box.h * 0.04);
  ctx.restore();
}

/** kind: 'circle' | 'triangle' | 'square' | 'rectangle'. `r` is roughly the half-size. */
export function drawShape(ctx, kind, cx, cy, r, color) {
  ctx.save();
  ctx.fillStyle = color;
  ctx.strokeStyle = 'rgba(0,0,0,0.25)';
  ctx.lineWidth = 3;
  ctx.lineJoin = 'round';
  ctx.beginPath();
  if (kind === 'circle') {
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
  } else if (kind === 'triangle') {
    ctx.moveTo(cx, cy - r);
    ctx.lineTo(cx + r * 1.05, cy + r * 0.8);
    ctx.lineTo(cx - r * 1.05, cy + r * 0.8);
    ctx.closePath();
  } else if (kind === 'square') {
    ctx.rect(cx - r * 0.85, cy - r * 0.85, r * 1.7, r * 1.7);
  } else {
    ctx.rect(cx - r * 1.2, cy - r * 0.65, r * 2.4, r * 1.3);
  }
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}

/** A stylised one-quetzal coin. */
export function drawCoin(ctx, cx, cy, r) {
  ctx.save();
  ctx.fillStyle = '#E0B84A';
  ctx.strokeStyle = '#9C7A1F';
  ctx.lineWidth = Math.max(2, r * 0.12);
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = '#7A5C12';
  ctx.font = `900 ${Math.round(r * 0.8)}px Nunito, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('Q1', cx, cy + r * 0.05);
  ctx.restore();
}

/** `slots` works as in drawItems: coin groups shown side by side must share it. */
export function drawCoins(ctx, count, box, slots = count) {
  const grid = Math.max(count, slots);
  const cols = Math.min(grid, 3);
  const rows = Math.ceil(grid / cols);
  const cell = Math.min(box.w / cols, box.h / rows);
  const startX = box.x + (box.w - cols * cell) / 2 + cell / 2;
  const startY = box.y + (box.h - rows * cell) / 2 + cell / 2;
  for (let i = 0; i < count; i++) {
    drawCoin(ctx, startX + (i % cols) * cell, startY + Math.floor(i / cols) * cell, cell * 0.38);
  }
}

/** `count` wooden sticks side by side (for "how many sides" questions). */
export function drawSticks(ctx, count, box) {
  const gap = box.w / (count + 1);
  ctx.save();
  ctx.strokeStyle = '#8D5524';
  ctx.lineCap = 'round';
  ctx.lineWidth = Math.max(4, box.w * 0.05);
  for (let i = 1; i <= count; i++) {
    const x = box.x + gap * i;
    ctx.beginPath();
    ctx.moveTo(x, box.y + box.h * 0.2);
    ctx.lineTo(x, box.y + box.h * 0.8);
    ctx.stroke();
  }
  ctx.restore();
}

/** A woven basket (canasta); draw the items over its upper part. */
export function drawBasket(ctx, box, color = '#C68642') {
  ctx.save();
  ctx.fillStyle = color;
  ctx.strokeStyle = '#8D5524';
  ctx.lineWidth = 3;
  const top = box.y + box.h * 0.45;
  ctx.beginPath();
  ctx.moveTo(box.x, top);
  ctx.lineTo(box.x + box.w, top);
  ctx.lineTo(box.x + box.w * 0.88, box.y + box.h);
  ctx.lineTo(box.x + box.w * 0.12, box.y + box.h);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}
