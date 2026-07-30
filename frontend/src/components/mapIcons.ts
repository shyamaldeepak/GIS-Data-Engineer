/**
 * Draws a filled triangle onto an offscreen canvas and hands it to MapLibre
 * as an `sdf: true` icon. A plain filled shape isn't a real signed-distance
 * field (edges are hard, not anti-aliased), but MapLibre still renders it
 * fine and — critically — lets `icon-color` tint each feature individually,
 * which a normal RGBA icon can't do per-feature.
 */
export function createArrowIcon(size = 32): { width: number; height: number; data: Uint8Array } {
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d")!;
  ctx.clearRect(0, 0, size, size);
  ctx.fillStyle = "#ffffff";
  ctx.beginPath();
  ctx.moveTo(size / 2, size * 0.08);
  ctx.lineTo(size * 0.85, size * 0.9);
  ctx.lineTo(size / 2, size * 0.7);
  ctx.lineTo(size * 0.15, size * 0.9);
  ctx.closePath();
  ctx.fill();

  const imageData = ctx.getImageData(0, 0, size, size);
  return { width: size, height: size, data: new Uint8Array(imageData.data.buffer) };
}
