"""Fighter analytics: rating engine, profile builder, consistency, and division landscape."""

from fightmatch.analytics.consistency import consistency_score, volatility_label
from fightmatch.analytics.landscape import (
    DivisionLandscape,
    build_landscape,
    format_landscape_terminal,
)
from fightmatch.analytics.profile import FighterProfile, build_profile
from fightmatch.analytics.rating import FighterRating, rate_fighter, rate_all

__all__ = [
    "FighterRating",
    "rate_fighter",
    "rate_all",
    "FighterProfile",
    "build_profile",
    "consistency_score",
    "volatility_label",
    "DivisionLandscape",
    "build_landscape",
    "format_landscape_terminal",
]
