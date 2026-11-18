/**
 * Defensive numeric and text formatting utilities.
 * Guarantees zero runtime TypeError exceptions on undefined/null values.
 */

export function safeNumber(val: any, fallback = 0): number {
  if (val === null || val === undefined) return fallback;
  const num = Number(val);
  return isNaN(num) ? fallback : num;
}

export function formatNum(val: any, decimals = 2, fallback = '—'): string {
  if (val === null || val === undefined) return fallback;
  const num = Number(val);
  if (isNaN(num)) return fallback;
  return num.toFixed(decimals);
}

export function formatInt(val: any, fallback = '0'): string {
  if (val === null || val === undefined) return fallback;
  const num = Number(val);
  if (isNaN(num)) return fallback;
  return Math.round(num).toLocaleString();
}

export function formatDelta(val: any, decimals = 3, suffix = ''): string {
  if (val === null || val === undefined) return '0.000';
  const num = Number(val);
  if (isNaN(num)) return '0.000';
  const formatted = num.toFixed(decimals);
  return (num > 0 ? `+${formatted}` : formatted) + suffix;
}

export function formatPercent(val: any, decimals = 1): string {
  if (val === null || val === undefined) return '0.0%';
  const num = Number(val);
  if (isNaN(num)) return '0.0%';
  return `${(num * 100).toFixed(decimals)}%`;
}
