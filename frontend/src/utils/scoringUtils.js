export function calculateOpportunityScore(data) {
  let score = 0;

  if (data.market_size > 1000000) score += 30;
  if (data.competition < 5) score += 20;
  if (data.growth_rate > 20) score += 30;
  if (data.execution_complexity < 5) score += 20;

  return score;
}