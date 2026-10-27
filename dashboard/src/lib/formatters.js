// A null figure is withheld for disclosure control: it rests on too few survey
// households to publish. Shown as a dash, never as zero.
export const WITHHELD = "\u2013";

function getSignedPrefix(value) {
  const amount = Number(value);
  if (amount > 0) {
    return "+";
  }
  if (amount < 0) {
    return "\u2212";
  }
  return "";
}

export function formatCurrency(value) {
  if (value == null) return WITHHELD;
  return `\u00A3${Math.round(Number(value)).toLocaleString("en-GB")}`;
}

export function formatSignedCurrency(value) {
  if (value == null) return WITHHELD;
  const amount = Math.round(Number(value));
  return `${getSignedPrefix(amount)}\u00A3${Math.abs(amount).toLocaleString("en-GB")}`;
}

export function formatBn(value) {
  if (value == null) return WITHHELD;
  return `\u00A3${Number(value).toFixed(2)}bn`;
}

export function formatSignedBn(value) {
  if (value == null) return WITHHELD;
  const amount = Number(value);
  return `${getSignedPrefix(amount)}\u00A3${Math.abs(amount).toFixed(2)}bn`;
}

export function formatMn(value) {
  if (value == null) return WITHHELD;
  return `\u00A3${Math.round(Number(value)).toLocaleString("en-GB")}m`;
}

export function formatSignedMn(value) {
  if (value == null) return WITHHELD;
  const amount = Math.round(Number(value));
  return `${getSignedPrefix(amount)}\u00A3${Math.abs(amount).toLocaleString("en-GB")}m`;
}

export function formatPct(value, digits = 1) {
  if (value == null) return WITHHELD;
  return `${Number(value).toFixed(digits)}%`;
}

export function formatSignedPct(value, digits = 1) {
  if (value == null) return WITHHELD;
  return `${getSignedPrefix(value)}${formatPct(Math.abs(Number(value)), digits)}`;
}

export function formatCompactCurrency(value) {
  if (value == null) return WITHHELD;
  const formatter = new Intl.NumberFormat("en-GB", {
    notation: "compact",
    maximumFractionDigits: 1,
  });

  return `\u00A3${formatter.format(Number(value))}`;
}

// Signed figures use a true minus sign (U+2212) and an explicit "+", so a
// positive change never reads as an unsigned level.
export function formatCount(value) {
  if (value == null) return WITHHELD;
  const num = Number(value);
  const magnitude = Math.abs(num);
  // Counts of 100k+ are shown in millions with two decimals; smaller counts
  // (e.g. the poverty headcount) are shown in thousands.
  const text =
    magnitude >= 1e5 ? `${(magnitude / 1e6).toFixed(2)}m` : `${(magnitude / 1e3).toFixed(1)}k`;
  return num < 0 ? `\u2212${text}` : text;
}

// A change in a count (net entrants, FTEs), always with its sign.
export function formatSignedCount(value) {
  if (value == null) return WITHHELD;
  const num = Number(value);
  return `${getSignedPrefix(num)}${formatCount(Math.abs(num))}`;
}

// UK fiscal years run April to April, so the model's 2027 is 2027-28. Every
// year shown to a reader goes through this.
export function formatFiscalYear(year) {
  const start = Number(year);
  return `${start}-${String((start + 1) % 100).padStart(2, "0")}`;
}
