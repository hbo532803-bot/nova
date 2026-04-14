export function parseCurrencyToNumber(value, fallback = 0) {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value !== "string") return fallback;
  const normalized = value.replace(/[$,\s]/g, "").trim();
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function formatCurrencyDisplay(value, fallback = "$0") {
  if (typeof value === "string" && value.trim()) {
    const trimmed = value.trim();
    return /^\$/.test(trimmed) ? trimmed : `$${trimmed}`;
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return `$${value.toLocaleString()}`;
  }
  return fallback;
}

export function formatCurrency(value) {
  return formatCurrencyDisplay(value, "$0");
}

export function formatPercent(value) {
  return value + "%";
}

export function formatNumber(value) {
  return Number(value).toLocaleString();
}
