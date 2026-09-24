// Hand-drawn fruit, maize and farm animals for the lessons. They look the same on every phone,
// unlike emoji (the mango emoji does not even exist before Android 9, and the APK supports 8).
// Each function draws centred on (cx, cy) inside a square of side `size`, like an emoji would,
// so it can be passed to drawItems / drawEmoji in place of an emoji string.

function oval(ctx, x, y, rx, ry, rot, fill) {
  ctx.fillStyle = fill;
  ctx.beginPath();
  ctx.ellipse(x, y, rx, ry, rot, 0, Math.PI * 2);
  ctx.fill();
}

const dot = (ctx, x, y, r, fill) => oval(ctx, x, y, r, r, 0, fill);

export function mango(ctx, cx, cy, size) {
  const s = size / 2;
  ctx.save();
  oval(ctx, cx, cy + s * 0.08, s * 0.62, s * 0.8, -0.5, '#FFB300');
  ctx.clip();
  oval(ctx, cx - s * 0.4, cy + s * 0.45, s * 0.36, s * 0.4, -0.5, 'rgba(255,112,67,0.55)');
  ctx.restore();
  oval(ctx, cx - s * 0.18, cy - s * 0.25, s * 0.12, s * 0.28, -0.5, 'rgba(255,255,255,0.35)');
  oval(ctx, cx + s * 0.32, cy - s * 0.72, s * 0.3, s * 0.12, -0.6, '#43A047');
}

export function banano(ctx, cx, cy, size) {
  const s = size / 2;
  const oy = cy - s * 0.45;
  ctx.save();
  ctx.lineCap = 'round';
  ctx.strokeStyle = '#FDD835';
  ctx.lineWidth = s * 0.42;
  ctx.beginPath(); ctx.arc(cx, oy, s * 0.85, Math.PI * 0.18, Math.PI * 0.82); ctx.stroke();
  ctx.strokeStyle = 'rgba(0,0,0,0.12)';
  ctx.lineWidth = s * 0.1;
  ctx.beginPath(); ctx.arc(cx, oy, s * 0.72, Math.PI * 0.25, Math.PI * 0.75); ctx.stroke();
  ctx.restore();
  [Math.PI * 0.14, Math.PI * 0.86].forEach((a) => dot(ctx, cx + Math.cos(a) * s * 0.85, oy + Math.sin(a) * s * 0.85, s * 0.1, '#6D4C41'));
}

export function naranja(ctx, cx, cy, size) {
  const s = size / 2;
  dot(ctx, cx, cy + s * 0.08, s * 0.78, '#FB8C00');
  dot(ctx, cx - s * 0.3, cy - s * 0.2, s * 0.18, '#FFB74D');
  [[0.3, 0.3], [-0.2, 0.45], [0.45, -0.1], [0.05, 0.1]].forEach(([dx, dy]) => dot(ctx, cx + dx * s, cy + dy * s, s * 0.04, '#E65100'));
  oval(ctx, cx + s * 0.25, cy - s * 0.72, s * 0.28, s * 0.11, -0.4, '#43A047');
  dot(ctx, cx, cy - s * 0.68, s * 0.07, '#6D4C41');
}

export function tomate(ctx, cx, cy, size) {
  const s = size / 2;
  oval(ctx, cx, cy + s * 0.1, s * 0.8, s * 0.68, 0, '#E53935');
  oval(ctx, cx - s * 0.32, cy - s * 0.12, s * 0.16, s * 0.1, -0.5, 'rgba(255,255,255,0.4)');
  for (let i = 0; i < 5; i++) {
    const a = (Math.PI * 2 * i) / 5 - Math.PI / 2;
    oval(ctx, cx + Math.cos(a) * s * 0.18, cy - s * 0.52 + Math.sin(a) * s * 0.1, s * 0.2, s * 0.07, a, '#388E3C');
  }
}

export function aguacate(ctx, cx, cy, size) {
  const s = size / 2;
  // Cut in half: dark skin, pale flesh, brown seed.
  dot(ctx, cx, cy + s * 0.25, s * 0.6, '#33691E');
  dot(ctx, cx, cy - s * 0.3, s * 0.4, '#33691E');
  dot(ctx, cx, cy + s * 0.25, s * 0.5, '#C5E1A5');
  dot(ctx, cx, cy - s * 0.3, s * 0.31, '#C5E1A5');
  oval(ctx, cx, cy - s * 0.08, s * 0.3, s * 0.3, 0, '#C5E1A5');
  dot(ctx, cx, cy + s * 0.25, s * 0.26, '#8D6E63');
}

export function elote(ctx, cx, cy, size) {
  const s = size / 2;
  oval(ctx, cx - s * 0.22, cy + s * 0.25, s * 0.2, s * 0.62, 0.35, '#7CB342');
  oval(ctx, cx + s * 0.22, cy + s * 0.25, s * 0.2, s * 0.62, -0.35, '#8BC34A');
  oval(ctx, cx, cy - s * 0.05, s * 0.3, s * 0.78, 0, '#FBC02D');
  for (let r = -3; r <= 3; r++) {
    for (const c of [-1, 0, 1]) dot(ctx, cx + c * s * 0.14, cy - s * 0.05 + r * s * 0.18, s * 0.055, '#F9A825');
  }
}

export function gallina(ctx, cx, cy, size) {
  const s = size / 2;
  oval(ctx, cx - s * 0.5, cy - s * 0.05, s * 0.22, s * 0.4, -0.5, '#5D3A1A');
  oval(ctx, cx - s * 0.05, cy + s * 0.2, s * 0.6, s * 0.45, 0, '#A1662F');
  oval(ctx, cx - s * 0.1, cy + s * 0.18, s * 0.3, s * 0.2, 0.2, '#8B5425');
  dot(ctx, cx + s * 0.4, cy - s * 0.3, s * 0.25, '#A1662F');
  [[0.3, -0.58], [0.42, -0.62], [0.54, -0.56]].forEach(([dx, dy]) => dot(ctx, cx + dx * s, cy + dy * s, s * 0.08, '#E53935'));
  ctx.fillStyle = '#FFA000';
  ctx.beginPath(); ctx.moveTo(cx + s * 0.62, cy - s * 0.35); ctx.lineTo(cx + s * 0.82, cy - s * 0.28); ctx.lineTo(cx + s * 0.62, cy - s * 0.22); ctx.fill();
  oval(ctx, cx + s * 0.6, cy - s * 0.13, s * 0.05, s * 0.09, 0, '#E53935');
  dot(ctx, cx + s * 0.46, cy - s * 0.34, s * 0.05, '#1A1A1A');
  ctx.strokeStyle = '#FFA000';
  ctx.lineWidth = Math.max(1.5, s * 0.06);
  ctx.beginPath(); ctx.moveTo(cx - s * 0.1, cy + s * 0.6); ctx.lineTo(cx - s * 0.1, cy + s * 0.8);
  ctx.moveTo(cx + s * 0.12, cy + s * 0.6); ctx.lineTo(cx + s * 0.12, cy + s * 0.8); ctx.stroke();
}

export function pollito(ctx, cx, cy, size) {
  const s = size / 2;
  dot(ctx, cx - s * 0.05, cy + s * 0.22, s * 0.5, '#FDD835');
  oval(ctx, cx - s * 0.12, cy + s * 0.25, s * 0.25, s * 0.16, 0.3, '#FBC02D');
  dot(ctx, cx + s * 0.25, cy - s * 0.32, s * 0.32, '#FDD835');
  ctx.fillStyle = '#FB8C00';
  ctx.beginPath(); ctx.moveTo(cx + s * 0.52, cy - s * 0.36); ctx.lineTo(cx + s * 0.74, cy - s * 0.28); ctx.lineTo(cx + s * 0.52, cy - s * 0.2); ctx.fill();
  dot(ctx, cx + s * 0.34, cy - s * 0.38, s * 0.06, '#1A1A1A');
  ctx.strokeStyle = '#FB8C00';
  ctx.lineWidth = Math.max(1.5, s * 0.06);
  ctx.beginPath(); ctx.moveTo(cx - s * 0.15, cy + s * 0.7); ctx.lineTo(cx - s * 0.15, cy + s * 0.86);
  ctx.moveTo(cx + s * 0.08, cy + s * 0.7); ctx.lineTo(cx + s * 0.08, cy + s * 0.86); ctx.stroke();
}

export function vaca(ctx, cx, cy, size) {
  const s = size / 2;
  oval(ctx, cx - s * 0.62, cy - s * 0.35, s * 0.25, s * 0.12, -0.4, '#E0E0E0');
  oval(ctx, cx + s * 0.62, cy - s * 0.35, s * 0.25, s * 0.12, 0.4, '#E0E0E0');
  oval(ctx, cx - s * 0.32, cy - s * 0.66, s * 0.08, s * 0.18, -0.4, '#BCAAA4');
  oval(ctx, cx + s * 0.32, cy - s * 0.66, s * 0.08, s * 0.18, 0.4, '#BCAAA4');
  ctx.save();
  oval(ctx, cx, cy, s * 0.52, s * 0.68, 0, '#FFFFFF');
  ctx.strokeStyle = '#9E9E9E';
  ctx.lineWidth = Math.max(1.5, s * 0.05);
  ctx.stroke();
  ctx.clip();
  oval(ctx, cx - s * 0.35, cy - s * 0.35, s * 0.3, s * 0.25, 0.3, '#212121');
  oval(ctx, cx + s * 0.45, cy + s * 0.05, s * 0.2, s * 0.3, -0.3, '#212121');
  ctx.restore();
  oval(ctx, cx, cy + s * 0.42, s * 0.42, s * 0.28, 0, '#F8BBD0');
  dot(ctx, cx - s * 0.15, cy + s * 0.44, s * 0.06, '#AD1457');
  dot(ctx, cx + s * 0.15, cy + s * 0.44, s * 0.06, '#AD1457');
  dot(ctx, cx - s * 0.2, cy - s * 0.08, s * 0.07, '#1A1A1A');
  dot(ctx, cx + s * 0.2, cy - s * 0.08, s * 0.07, '#1A1A1A');
}

export function cerdo(ctx, cx, cy, size) {
  const s = size / 2;
  ctx.fillStyle = '#F06292';
  ctx.beginPath(); ctx.moveTo(cx - s * 0.55, cy - s * 0.35); ctx.lineTo(cx - s * 0.38, cy - s * 0.82); ctx.lineTo(cx - s * 0.15, cy - s * 0.5); ctx.fill();
  ctx.beginPath(); ctx.moveTo(cx + s * 0.55, cy - s * 0.35); ctx.lineTo(cx + s * 0.38, cy - s * 0.82); ctx.lineTo(cx + s * 0.15, cy - s * 0.5); ctx.fill();
  dot(ctx, cx, cy, s * 0.68, '#F48FB1');
  oval(ctx, cx, cy + s * 0.2, s * 0.3, s * 0.22, 0, '#F06292');
  dot(ctx, cx - s * 0.1, cy + s * 0.2, s * 0.06, '#AD1457');
  dot(ctx, cx + s * 0.1, cy + s * 0.2, s * 0.06, '#AD1457');
  dot(ctx, cx - s * 0.25, cy - s * 0.18, s * 0.07, '#1A1A1A');
  dot(ctx, cx + s * 0.25, cy - s * 0.18, s * 0.07, '#1A1A1A');
}
