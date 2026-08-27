/**
 * Accessors for the free_school_meals_results.json payload.
 *
 * Deliberately no fallbacks: if a field is missing the consumer throws
 * visibly rather than rendering placeholders.
 */

export function getReform(data) {
  return data.reform;
}

export function getBaseline(data) {
  return data.baseline;
}

export function getOfficialStats(data) {
  return data.official_stats;
}

export function getAssumptions(data) {
  return data.assumptions;
}

export function getPolicyUnmodelled(data) {
  return data.policy_unmodelled;
}

export function getMethods(data) {
  return data.methods;
}
