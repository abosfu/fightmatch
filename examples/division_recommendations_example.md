# FightMatch Division Report: [division_name]

> This file illustrates the structure of FightMatch analytical outputs.
> Actual reports are generated via CLI commands.
>
> ```
> fightmatch recommend \
>   --division "[division_name]" \
>   --top 10 \
>   --features data/features/features.csv \
>   --processed data/processed \
>   --reports-dir data/reports
>
> # Or across all detected divisions:
> fightmatch recommend-all \
>   --top 5 \
>   --features data/features/features.csv \
>   --processed data/processed \
>   --reports-dir data/reports
> ```

---

**Division:** [division_name]
**Generated:** [timestamp]

### How to interpret this report

- Top contenders are ordered by the FightMatch fighter rating (0–10 scale). The rating combines
  activity, form, striking/grappling efficiency, opponent quality, and finish ability.
- Recommended matchups are ordered by promoter score — a weighted combination of competitive balance,
  divisional relevance, activity readiness, freshness, style interest, and fan engagement proxy.

---

## Top Contenders

| Rank | Fighter | Rating |
|------|---------|--------|
| 1 | [fighter_name_1] | [computed_rating_1] |
| 2 | [fighter_name_2] | [computed_rating_2] |
| 3 | [fighter_name_3] | [computed_rating_3] |
| 4 | [fighter_name_4] | [computed_rating_4] |
| 5 | [fighter_name_5] | [computed_rating_5] |
| … | … | … |

---

## Recommended Matchups

### 1. [fighter_name_1] vs [fighter_name_2]

Ratings: [computed_rating_1] vs [computed_rating_2]
Promoter score: [promoter_score] ([promoter_tier])
Win probability: [win_prob_a] / [win_prob_b] · Competitiveness: [competitiveness_score] ([competitiveness_label])
Style contrast: [style_contrast_score] ([style_contrast_label])

- [explanation_signal_1]
- [explanation_signal_2]
- [explanation_signal_3]

---

### 2. [fighter_name_3] vs [fighter_name_4]

Ratings: [computed_rating_3] vs [computed_rating_4]
Promoter score: [promoter_score] ([promoter_tier])
Win probability: [win_prob_a] / [win_prob_b] · Competitiveness: [competitiveness_score] ([competitiveness_label])
Style contrast: [style_contrast_score] ([style_contrast_label])

- [explanation_signal_1]
- [explanation_signal_2]
- [explanation_signal_3]

---

### 3. [fighter_name_5] vs [fighter_name_6]

Ratings: [computed_rating_5] vs [computed_rating_6]
Promoter score: [promoter_score] ([promoter_tier])
Win probability: [win_prob_a] / [win_prob_b] · Competitiveness: [competitiveness_score] ([competitiveness_label])
Style contrast: [style_contrast_score] ([style_contrast_label])

- [explanation_signal_1]
- [explanation_signal_2]
- [explanation_signal_3]

---

*Each fighter appears in at most one recommended matchup (no double-booking).
Matchups penalised by a freshness score of 0 when the pair fought recently.*
