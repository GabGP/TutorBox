// Canvas Helper Utilities
// Programmatic drawing tools for the Kuk Math App

/**
 * Draw a rounded rectangle
 */
export function drawRoundedRect(ctx, x, y, w, h, r, fill, stroke) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = 2; ctx.stroke(); }
}

/**
 * Draw a 5-pointed star
 */
export function drawStar(ctx, cx, cy, size, color) {
  ctx.save();
  ctx.fillStyle = color || '#FFD700';
  ctx.beginPath();
  for (let i = 0; i < 5; i++) {
    const outerAngle = (Math.PI * 2 * i) / 5 - Math.PI / 2;
    const innerAngle = outerAngle + Math.PI / 5;
    if (i === 0) ctx.moveTo(cx + size * Math.cos(outerAngle), cy + size * Math.sin(outerAngle));
    else ctx.lineTo(cx + size * Math.cos(outerAngle), cy + size * Math.sin(outerAngle));
    ctx.lineTo(cx + (size * 0.4) * Math.cos(innerAngle), cy + (size * 0.4) * Math.sin(innerAngle));
  }
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

/**
 * Draw a speech bubble
 */
export function drawBubble(ctx, x, y, w, h, text) {
  const r = 16;
  const tailH = 14;
  ctx.save();

  // Bubble body
  ctx.fillStyle = 'white';
  ctx.shadowColor = 'rgba(0,0,0,0.2)';
  ctx.shadowBlur = 8;
  drawRoundedRect(ctx, x, y, w, h, r, 'white', null);

  // Tail pointing down-left
  ctx.beginPath();
  ctx.moveTo(x + 20, y + h);
  ctx.lineTo(x + 10, y + h + tailH);
  ctx.lineTo(x + 40, y + h);
  ctx.closePath();
  ctx.fill();
  ctx.shadowBlur = 0;

  // Text
  if (text) {
    ctx.fillStyle = '#2C2C2C';
    ctx.font = 'bold 14px Nunito, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, x + w / 2, y + h / 2);
  }
  ctx.restore();
}

/**
 * Load an image as a Promise
 */
export function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}

/**
 * Draw image maintaining aspect ratio within bounds
 */
export function drawImageFit(ctx, img, x, y, w, h) {
  const imgRatio = img.width / img.height;
  const boxRatio = w / h;
  let dw, dh, dx, dy;
  if (imgRatio > boxRatio) {
    dw = w;
    dh = w / imgRatio;
    dx = x;
    dy = y + (h - dh) / 2;
  } else {
    dh = h;
    dw = h * imgRatio;
    dx = x + (w - dw) / 2;
    dy = y;
  }
  ctx.drawImage(img, dx, dy, dw, dh);
}

/**
 * Trigger CSS animation on element
 */
export function animateIn(element, animationClass) {
  element.classList.remove(animationClass);
  void element.offsetWidth; // reflow
  element.classList.add(animationClass);
}

/**
 * Clear entire canvas
 */
export function clearCanvas(ctx) {
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
}

/**
 * Scale canvas for HiDPI/Retina displays
 */
export function scaleCanvas(canvas, ctx) {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);
  return dpr;
}

/**
 * Draw a simple tree (brown trunk + green canopy)
 */
export function drawTree(ctx, x, y, height, color) {
  const trunkW = height * 0.12;
  const trunkH = height * 0.45;
  const canopyR = height * 0.32;

  // Trunk
  ctx.fillStyle = '#8B4513';
  ctx.fillRect(x - trunkW / 2, y - trunkH, trunkW, trunkH);

  // Canopy
  ctx.fillStyle = color || '#2E7D32';
  ctx.beginPath();
  ctx.arc(x, y - trunkH - canopyR * 0.6, canopyR, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = color ? lightenColor(color, 20) : '#4CAF50';
  ctx.beginPath();
  ctx.arc(x - canopyR * 0.3, y - trunkH - canopyR * 0.9, canopyR * 0.75, 0, Math.PI * 2);
  ctx.fill();

  ctx.beginPath();
  ctx.arc(x + canopyR * 0.3, y - trunkH - canopyR * 0.85, canopyR * 0.7, 0, Math.PI * 2);
  ctx.fill();
}

/**
 * Draw a simple volcano shape
 */
export function drawVolcano(ctx, x, y, size) {
  ctx.save();
  // Mountain body
  ctx.fillStyle = '#5D4037';
  ctx.beginPath();
  ctx.moveTo(x - size, y);
  ctx.lineTo(x - size * 0.15, y - size * 0.85);
  ctx.lineTo(x + size * 0.15, y - size * 0.85);
  ctx.lineTo(x + size, y);
  ctx.closePath();
  ctx.fill();

  // Snow cap / lava top
  ctx.fillStyle = '#EF5350';
  ctx.beginPath();
  ctx.moveTo(x - size * 0.12, y - size * 0.85);
  ctx.lineTo(x - size * 0.06, y - size);
  ctx.lineTo(x + size * 0.06, y - size);
  ctx.lineTo(x + size * 0.12, y - size * 0.85);
  ctx.closePath();
  ctx.fill();

  ctx.restore();
}

/**
 * Helper: lighten a hex color
 */
function lightenColor(hex, amount) {
  let num = parseInt(hex.replace('#', ''), 16);
  let r = Math.min(255, (num >> 16) + amount);
  let g = Math.min(255, ((num >> 8) & 0xff) + amount);
  let b = Math.min(255, (num & 0xff) + amount);
  return `rgb(${r},${g},${b})`;
}

/**
 * Draw a simple house / building
 */
export function drawBuilding(ctx, x, y, w, h, wallColor, roofColor) {
  // Wall
  ctx.fillStyle = wallColor || '#FFF9C4';
  ctx.fillRect(x, y, w, h);
  ctx.strokeStyle = 'rgba(0,0,0,0.2)';
  ctx.lineWidth = 1;
  ctx.strokeRect(x, y, w, h);

  // Roof (triangle)
  ctx.fillStyle = roofColor || '#C62828';
  ctx.beginPath();
  ctx.moveTo(x - 6, y);
  ctx.lineTo(x + w / 2, y - h * 0.5);
  ctx.lineTo(x + w + 6, y);
  ctx.closePath();
  ctx.fill();
}

/**
 * Draw a simple chicken
 */
export function drawChicken(ctx, x, y, size, color) {
  ctx.save();
  color = color || '#FFA000';
  // Body
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.ellipse(x, y, size * 0.7, size * 0.55, 0, 0, Math.PI * 2);
  ctx.fill();
  // Head
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x + size * 0.65, y - size * 0.4, size * 0.35, 0, Math.PI * 2);
  ctx.fill();
  // Beak
  ctx.fillStyle = '#FF6F00';
  ctx.beginPath();
  ctx.moveTo(x + size * 0.98, y - size * 0.38);
  ctx.lineTo(x + size * 1.2, y - size * 0.28);
  ctx.lineTo(x + size * 0.98, y - size * 0.2);
  ctx.closePath();
  ctx.fill();
  // Eye
  ctx.fillStyle = 'white';
  ctx.beginPath();
  ctx.arc(x + size * 0.73, y - size * 0.44, size * 0.1, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = 'black';
  ctx.beginPath();
  ctx.arc(x + size * 0.74, y - size * 0.44, size * 0.055, 0, Math.PI * 2);
  ctx.fill();
  // Comb
  ctx.fillStyle = '#E53935';
  ctx.beginPath();
  ctx.arc(x + size * 0.65, y - size * 0.78, size * 0.12, 0, Math.PI * 2);
  ctx.fill();
  // Legs
  ctx.strokeStyle = '#FF8F00';
  ctx.lineWidth = size * 0.08;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(x - size * 0.1, y + size * 0.5);
  ctx.lineTo(x - size * 0.1, y + size * 0.85);
  ctx.moveTo(x + size * 0.2, y + size * 0.5);
  ctx.lineTo(x + size * 0.2, y + size * 0.85);
  ctx.stroke();
  ctx.restore();
}

/**
 * Draw a simple quetzal bird
 */
export function drawQuetzal(ctx, cx, cy, size) {
  ctx.save();
  const s = size;
  // Tail
  ctx.fillStyle = '#1B5E20';
  for (let i = -1; i <= 1; i++) {
    ctx.beginPath();
    ctx.ellipse(cx + i * s * 0.1, cy + s * 0.8, s * 0.06, s * 0.4, i * 0.2, 0, Math.PI * 2);
    ctx.fill();
  }
  // Body
  ctx.fillStyle = '#2E7D32';
  ctx.beginPath();
  ctx.ellipse(cx, cy + s * 0.2, s * 0.3, s * 0.4, 0, 0, Math.PI * 2);
  ctx.fill();
  // Red chest
  ctx.fillStyle = '#C62828';
  ctx.beginPath();
  ctx.ellipse(cx, cy + s * 0.35, s * 0.2, s * 0.25, 0, 0, Math.PI * 2);
  ctx.fill();
  // Head
  ctx.fillStyle = '#2E7D32';
  ctx.beginPath();
  ctx.arc(cx, cy - s * 0.15, s * 0.22, 0, Math.PI * 2);
  ctx.fill();
  // Crest
  ctx.fillStyle = '#4CAF50';
  ctx.beginPath();
  ctx.ellipse(cx, cy - s * 0.42, s * 0.06, s * 0.14, 0, 0, Math.PI * 2);
  ctx.fill();
  // Eye
  ctx.fillStyle = 'white';
  ctx.beginPath();
  ctx.arc(cx + s * 0.1, cy - s * 0.17, s * 0.08, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#1A237E';
  ctx.beginPath();
  ctx.arc(cx + s * 0.11, cy - s * 0.17, s * 0.05, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}
