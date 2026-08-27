function getSignedPrefix(value) {
  const amount = Number(value);
  if (amount > 0) {
    return "";
  }
  if (amount < 0) {
    return "\u2212";
  }
  return "";
}

export function formatCurrency(value) {
  return `\u00A3${Math.round(Number(value)).toLocaleString("en-GB")}`;
}

export function formatSignedCurrency(value) {
  const amount = Math.round(Number(value));
  return `${getSignedPrefix(amount)}\u00A3${Math.abs(amount).toLocaleString("en-GB")}`;
}

export function formatBn(value) {
  return `\u00A3${Number(value).toFixed(2)}bn`;
}

export function formatSignedBn(value) {
  const amount = Number(value);
  return `${getSignedPrefix(amount)}\u00A3${Math.abs(amount).toFixed(2)}bn`;
}

export function formatMn(value) {
  return `\u00A3${Math.round(Number(value)).toLocaleString("en-GB")}m`;
}

export function formatSignedMn(value) {
  const amount = Math.round(Number(value));
  return `${getSignedPrefix(amount)}\u00A3${Math.abs(amount).toLocaleString("en-GB")}m`;
}

export function formatPct(value, digits = 1) {
  return `${Number(value).toFixed(digits)}%`;
}

export function formatSignedPct(value, digits = 1) {
  return `${getSignedPrefix(value)}${formatPct(Math.abs(Number(value)), digits)}`;
}

export function formatCompactCurrency(value) {
  const formatter = new Intl.NumberFormat("en-GB", {
    notation: "compact",
    maximumFractionDigits: 1,
  });

  return `\u00A3${formatter.format(Number(value))}`;
}

export function formatCount(value) {
  const num = Number(value);
  // Counts of 100k+ are shown in millions with two decimals; smaller counts
  // (e.g. the poverty headcount) are shown in thousands.
  if (num >= 1e5) {
    return `${(num / 1e6).toFixed(2)}m`;
  }
  return `${(num / 1e3).toFixed(1)}k`;
}
