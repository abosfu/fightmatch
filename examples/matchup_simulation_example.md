# Matchup Simulation: [fighter_a] vs [fighter_b]

> This file illustrates the structure of FightMatch analytical outputs.
> Actual reports are generated via CLI commands.
>
> ```
> fightmatch simulate \
>   --fighter-a "[fighter_a]" \
>   --fighter-b "[fighter_b]" \
>   --features data/features/features.csv \
>   --processed data/processed \
>   --reports-dir data/reports
> ```

---

**Generated:** [timestamp]

## Ratings & Win Probability

| Fighter | Rating | Win Probability |
|---------|--------|-----------------|
| [fighter_a] | [rating_a] / 10 | [win_prob_a] |
| [fighter_b] | [rating_b] / 10 | [win_prob_b] |

Win probability is computed via a logistic function on the rating delta.
A one-point rating gap corresponds to approximately 62% probability for the higher-rated fighter.

## Matchup Metrics

| Metric | Score | Label |
|--------|-------|-------|
| Competitiveness | [competitiveness_score] | [competitiveness_label] |
| Style Contrast | [style_contrast_score] | [style_contrast_label] |
| Rank Impact | [rank_impact_score] | [rank_impact_label] |

## Promoter Decision Score

| Component | Weight | Score |
|-----------|--------|-------|
| Competitiveness | 30% | [competitiveness_score] |
| Divisional Relevance | 20% | [divisional_relevance_score] |
| Activity Readiness | 20% | [activity_readiness_score] |
| Freshness | 15% | [freshness_score] |
| Style Interest | 10% | [style_interest_score] |
| Fan Interest (proxy) | 5% | [fan_interest_score] |
| **Total** | | **[promoter_score_total]** |

**Matchmaking tier:** [promoter_tier]
*(Priority ≥ 0.75 · Strong ≥ 0.60 · Consider ≥ 0.45 · Pass)*

## Key Factors

- [explanation_signal_1]
- [explanation_signal_2]
- [explanation_signal_3]

## Recommendation

**[recommendation_summary]**

---

*Style contrast measures divergence across four normalised dimensions: striking output, takedown volume,
control time, and finish rate. Rank impact reflects the average divisional rank position of both fighters.
Freshness drops to 0 when the pair fought recently.*
