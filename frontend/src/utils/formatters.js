export function formatNumber(n, decimals = 0) {
  if (n === null || n === undefined) return '--';
  return Number(n).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatPct(n, decimals = 2) {
  if (n === null || n === undefined) return '--';
  return `${Number(n).toFixed(decimals)}%`;
}

export function formatMs(n) {
  if (n === null || n === undefined) return '--';
  return `${Number(n).toFixed(2)}ms`;
}

export function formatTime(ts) {
  if (!ts) return '--';
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString();
}

export function truncateHex(hex, len = 8) {
  if (!hex) return '--';
  return hex.length > len ? hex.slice(0, len) + '...' : hex;
}
