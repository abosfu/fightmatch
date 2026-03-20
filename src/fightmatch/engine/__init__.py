"""Decision engine: matchup simulation, promoter scoring, explainability, and what-if."""

from fightmatch.engine.explain import explain_matchup_narrative
from fightmatch.engine.promoter import PromoterScore, score_matchup, select_matchups_ranked
from fightmatch.engine.simulate import MatchupSimulation, simulate
from fightmatch.engine.whatif import SCENARIOS, WhatIfResult, format_whatif_terminal, run_whatif

__all__ = [
    "MatchupSimulation",
    "simulate",
    "PromoterScore",
    "score_matchup",
    "select_matchups_ranked",
    "explain_matchup_narrative",
    "SCENARIOS",
    "WhatIfResult",
    "run_whatif",
    "format_whatif_terminal",
]
