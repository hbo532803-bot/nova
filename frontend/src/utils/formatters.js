export function formatCurrency(value) {
  return "$" + Number(value).toLocaleString();
}

export function formatPercent(value) {
  return value + "%";
}

export function formatNumber(value) {
  return Number(value).toLocaleString();
}