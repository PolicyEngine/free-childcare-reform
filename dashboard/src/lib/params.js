// Figures quoted in the copy that belong to the analysis, not the page. Each
// accessor reads the results JSON and falls back to the figure the copy used
// before it was wired up, so the page still renders if a key is missing.
// Point each one at its final key once the pipeline emits it.

function pick(value, fallback) {
  return value === null || value === undefined || Number.isNaN(Number(value))
    ? fallback
    : Number(value);
}

// Assumed share of new free hours that replaces care a family already buys.
// Reads assumptions.free_hours_displacement (0.9053 in the current run).
export function displacementShare(data) {
  return pick(data?.assumptions?.free_hours_displacement, 0.9);
}

// Share of childcare costs the UC childcare element covers, kept by the reform.
// Reads model_parameters.uc_childcare_coverage_rate.
export function ucCoverageRate(data) {
  return pick(data?.model_parameters?.uc_childcare_coverage_rate, 0.85);
}

// Tax-Free Childcare's statutory top-up on what a parent pays in (25%). The
// model parameter is the share of gross spend routed through the account
// (20%), so the top-up is r / (1 − r).
export function tfcTopUpRate(data) {
  const grossShare = data?.model_parameters?.baseline_tax_free_childcare_rate;
  if (grossShare === null || grossShare === undefined || Number(grossShare) >= 1) {
    return 0.25;
  }
  return Number(grossShare) / (1 - Number(grossShare));
}

// Tax-Free Childcare's annual cap per child, in pounds.
// Reads model_parameters.baseline_tax_free_childcare_cap_gbp.
export function tfcCapGbp(data) {
  return pick(data?.model_parameters?.baseline_tax_free_childcare_cap_gbp, 2000);
}

// Baseline take-up among English families with a child under 5, by scheme.
// No key carries these yet; they are the figures the Methodology tab quoted.
// Wire to the pipeline's key when it is added.
const TAKE_UP_FALLBACK = {
  tax_free_childcare: 0.97,
  extended: 0.86,
  universal: 0.86,
  targeted: 0.64,
};

// eslint-disable-next-line no-unused-vars
export function takeUpRatesUnder5(data, year) {
  const block = data?.by_year?.[String(year ?? data?.years?.[0])]?.take_up_rates_under_5;
  if (!block) return TAKE_UP_FALLBACK;
  return {
    tax_free_childcare: block.tax_free_childcare?.rate ?? TAKE_UP_FALLBACK.tax_free_childcare,
    extended: block.working_parent?.rate ?? TAKE_UP_FALLBACK.extended,
    universal: block.universal?.rate ?? TAKE_UP_FALLBACK.universal,
    targeted: block.targeted?.rate ?? TAKE_UP_FALLBACK.targeted,
  };
}
