"""Public data API: stable re-exports for dataset + features.

Canonical implementations live in fightmatch.scrape.store and
fightmatch.match.features.  Import from here for convenience:

    from fightmatch.data import build_dataset, build_features
"""

from fightmatch.match.features import build_features
from fightmatch.scrape.store import build_dataset

__all__ = ["build_dataset", "build_features"]
