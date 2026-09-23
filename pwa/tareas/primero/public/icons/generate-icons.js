// Icon generator script - run once with Node.js to generate PWA icons
// node public/icons/generate-icons.js
// This creates simple canvas-based icons without external dependencies

const { createCanvas } = require('canvas');
const fs = require('fs');
const path = require('path');

function generateIcon(size) {
  const canvas = createCanvas(size, size);
  const ctx = canvas.getContext('2d');

  // Background - sky to ground gradient
  const grad = ctx.createLinearGradient(0, 0, 0, size);
  grad.addColorStop(0, '#87CEEB');
  grad.addColorStop(0.6, '#4CAF50');
  grad.addColorStop(1, '#2E7D32');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, size, size);

  // Circle background
  ctx.fillStyle = '#2E7D32';
  ctx.beginPath();
  ctx.arc(size/2, size/2, size*0.45, 0, Math.PI*2);
  ctx.fill();

  // Simple quetzal body
  const s = size * 0.3;
  const cx = size/2, cy = size/2;

  // Body
  ctx.fillStyle = '#4CAF50';
  ctx.beginPath();
  ctx.ellipse(cx, cy, s*0.5, s*0.7, 0, 0, Math.PI*2);
  ctx.fill();

  // Red chest
  ctx.fillStyle = '#C62828';
  ctx.beginPath();
  ctx.ellipse(cx, cy+s*0.2, s*0.32, s*0.45, 0, 0, Math.PI*2);
  ctx.fill();

  // Head
  ctx.fillStyle = '#4CAF50';
  ctx.beginPath();
  ctx.arc(cx, cy-s*0.5, s*0.35, 0, Math.PI*2);
  ctx.fill();

  // Eye
  ctx.fillStyle = 'white';
  ctx.beginPath();
  ctx.arc(cx+s*0.12, cy-s*0.52, s*0.1, 0, Math.PI*2);
  ctx.fill();
  ctx.fillStyle = 'black';
  ctx.beginPath();
  ctx.arc(cx+s*0.13, cy-s*0.52, s*0.06, 0, Math.PI*2);
  ctx.fill();

  // Tail
  ctx.fillStyle = '#1B5E20';
  ctx.beginPath();
  ctx.ellipse(cx, cy+s*0.9, s*0.1, s*0.4, 0, 0, Math.PI*2);
  ctx.fill();

  const buffer = canvas.toBuffer('image/png');
  fs.writeFileSync(path.join(__dirname, `icon-${size}.png`), buffer);
  console.log(`Generated icon-${size}.png`);
}

try {
  generateIcon(192);
  generateIcon(512);
} catch(e) {
  console.log('Note: canvas package not installed. Using fallback icons.');
  // Maskable-safe Q'uq' the Quetzal, full-bleed background, centered art.
  // viewBox stays 192x192 for both sizes (SVG scales cleanly to 512).
  const art = `
<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#9BE3F7"/><stop offset=".55" stop-color="#7CC6E8"/><stop offset="1" stop-color="#2E7D32"/>
</linearGradient></defs>
<rect width="192" height="192" fill="url(#g)"/>
<ellipse cx="96" cy="205" rx="150" ry="62" fill="#43A047"/>
<ellipse cx="96" cy="144" rx="6" ry="20" fill="#1B5E20" transform="rotate(-13 96 144)"/>
<ellipse cx="96" cy="146" rx="6" ry="24" fill="#2E7D32"/>
<ellipse cx="96" cy="144" rx="6" ry="20" fill="#1B5E20" transform="rotate(13 96 144)"/>
<ellipse cx="96" cy="142" rx="3.6" ry="18" fill="#69F0AE" transform="rotate(-7 96 142)"/>
<ellipse cx="96" cy="142" rx="3.6" ry="18" fill="#69F0AE" transform="rotate(7 96 142)"/>
<ellipse cx="96" cy="108" rx="28" ry="34" fill="#2E7D32"/>
<ellipse cx="70" cy="106" rx="15" ry="23" fill="#1B5E20" transform="rotate(-20 70 106)"/>
<ellipse cx="71" cy="108" rx="9" ry="16" fill="#4CAF50" transform="rotate(-20 71 108)"/>
<ellipse cx="122" cy="106" rx="15" ry="23" fill="#1B5E20" transform="rotate(20 122 106)"/>
<ellipse cx="121" cy="108" rx="9" ry="16" fill="#4CAF50" transform="rotate(20 121 108)"/>
<ellipse cx="96" cy="116" rx="19" ry="21" fill="#C62828"/>
<ellipse cx="96" cy="121" rx="14" ry="14" fill="#EF5350"/>
<circle cx="96" cy="64" r="26" fill="#2E7D32"/>
<ellipse cx="89" cy="40" rx="5" ry="12" fill="#4CAF50" transform="rotate(-20 89 40)"/>
<ellipse cx="96" cy="37" rx="5" ry="14" fill="#69F0AE"/>
<ellipse cx="103" cy="40" rx="5" ry="12" fill="#4CAF50" transform="rotate(20 103 40)"/>
<circle cx="86" cy="62" r="10" fill="#fff"/><circle cx="106" cy="62" r="10" fill="#fff"/>
<circle cx="88" cy="63" r="6" fill="#1A237E"/><circle cx="108" cy="63" r="6" fill="#1A237E"/>
<circle cx="89" cy="62" r="2.8" fill="#000"/><circle cx="109" cy="62" r="2.8" fill="#000"/>
<circle cx="90" cy="60.5" r="1.4" fill="#fff"/><circle cx="110" cy="60.5" r="1.4" fill="#fff"/>
<path d="M88 74 Q96 83 104 74 L96 80 Z" fill="#FFA000"/>
<ellipse cx="78" cy="71" rx="5" ry="3.4" fill="#FF8A80" opacity=".5"/>
<ellipse cx="114" cy="71" rx="5" ry="3.4" fill="#FF8A80" opacity=".5"/>`;
  const svg = size => `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 192 192">${art}</svg>\n`;
  fs.writeFileSync(path.join(__dirname, 'icon-192.svg'), svg(192));
  fs.writeFileSync(path.join(__dirname, 'icon-512.svg'), svg(512));
  console.log('Created SVG fallback icons');
}
