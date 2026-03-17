# Fighter Profile: [fighter_name]

> This file illustrates the structure of FightMatch analytical outputs.
> Actual reports are generated via CLI commands.
>
> ```
> fightmatch fighter-profile --fighter "[fighter_name]" \
>   --features data/features/features.csv \
>   --processed data/processed \
>   --reports-dir data/reports
> ```

---

**Division:** [weight_class]
**Generated:** [timestamp]

## Summary

| Field | Value |
|-------|-------|
| Rating | [computed_rating] / 10 (Top [rating_percentile]%) |
| Archetype | [style_archetype] |
| Activity | [activity_status] ([days_since_last_fight] days since last fight) |
| Momentum | [momentum] (streak: [win_streak] \| last 5: [last_5_win_pct]) |
| Striking | [striking_label] ([sig_str_per_min] sig/min) |
| Grappling | [grappling_label] (TD rate: [td_rate] \| control: [control_per_15]s/15min) |
| Finishing | [finish_label] ([finish_rate]) |
| Competition | [sos_label] (avg opp win %: [opp_win_pct_avg]) |

## Rating Components

| Component | Score |
|-----------|-------|
| Activity (25%) | [activity_score] |
| Form (25%) | [form_score] |
| Efficiency (20%) | [efficiency_score] |
| Opponent Quality (15%) | [opponent_quality_score] |
| Finish Ability (15%) | [finish_ability_score] |
| **Composite (0–10)** | **[computed_rating]** |

---

*The composite rating is a weighted sum of all five components, each normalized to [0, 1].
Activity decays exponentially by days since last fight. Form combines win streak and recent win rate.
Efficiency reflects striking output and grappling volume. Opponent quality proxies strength of schedule.*
