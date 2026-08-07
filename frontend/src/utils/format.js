export function fmtNum(value, digits = 0, fallback = '—') {
  const n = Number(value);
  if (!Number.isFinite(n)) return fallback;
  return n.toFixed(digits);
}
