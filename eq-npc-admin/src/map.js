// EQ client map coordinates are -world X, -world Y. /loc is Y, X, Z.
export const worldToMap = (p) => [-Number(p.x), -Number(p.y), Number(p.z)];
export const project = (p, v, w, h) => [
  (p[0] - v.x) * v.scale + w / 2,
  (p[1] - v.y) * v.scale + h / 2,
];
export function fitView(points, w, h) {
  if (!points.length) return { x: 0, y: 0, scale: 1 };
  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity;
  for (const p of points) {
    minX = Math.min(minX, p[0]);
    minY = Math.min(minY, p[1]);
    maxX = Math.max(maxX, p[0]);
    maxY = Math.max(maxY, p[1]);
  }
  return {
    x: (minX + maxX) / 2,
    y: (minY + maxY) / 2,
    scale: Math.min(
      Math.max(40, w - 80) / Math.max(100, maxX - minX),
      Math.max(40, h - 80) / Math.max(100, maxY - minY),
    ),
  };
}
export function zoomView(v, factor, x, y, w, h) {
  const scale = Math.max(0.002, Math.min(12, v.scale * factor));
  return {
    x: v.x + (x - w / 2) / v.scale - (x - w / 2) / scale,
    y: v.y + (y - h / 2) / v.scale - (y - h / 2) / scale,
    scale,
  };
}
export function clipHeight(line, min, max) {
  const [x1, y1, z1, x2, y2, z2, layer] = line;
  if (min > max || Math.max(z1, z2) < min || Math.min(z1, z2) > max)
    return null;
  if (z1 === z2) return line;
  const a = (min - z1) / (z2 - z1),
    b = (max - z1) / (z2 - z1),
    lo = Math.max(0, Math.min(a, b)),
    hi = Math.min(1, Math.max(a, b));
  if (lo > hi) return null;
  return [
    x1 + (x2 - x1) * lo,
    y1 + (y2 - y1) * lo,
    z1 + (z2 - z1) * lo,
    x1 + (x2 - x1) * hi,
    y1 + (y2 - y1) * hi,
    z1 + (z2 - z1) * hi,
    layer,
  ];
}
export function spawnPairs(spawns, changes, zone) {
  return spawns
    .filter((s) => `${s.zone}:${s.version}` === zone)
    .map((before) => ({
      before,
      after:
        changes.find(
          (c) => c.table === "spawn2" && String(c.key.id) === String(before.id),
        )?.after ?? before,
    }));
}
