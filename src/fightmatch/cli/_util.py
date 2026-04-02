"""Shared CLI utilities: path helpers, division detection, report formatting."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from fightmatch.config import normalize_division
from fightmatch.match import load_features_csv


def parse_since(s: str) -> str:
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s
    raise ValueError("--since must be YYYY-MM-DD")


def division_slug(label: str) -> str:
    norm = normalize_division(label) or label.strip().lower()
    slug = norm.replace(" ", "-").replace("/", "-")
    return slug or "all"


def detect_divisions(
    processed_dir: Path, features_path: Path | None = None
) -> list[tuple[str, str]]:
    """Return list of (normalized_key, display_label) sorted by display label."""
    divisions: dict[str, str] = {}
    if features_path is not None and features_path.exists():
        try:
            rows = load_features_csv(features_path)
        except Exception:
            rows = []
        for r in rows:
            wc = r.get("weight_class")
            norm = normalize_division(wc)
            if norm and norm not in divisions:
                divisions[norm] = wc or norm.title()
    if not divisions:
        bouts_path = processed_dir / "bouts.json"
        if bouts_path.exists():
            try:
                bouts = json.loads(bouts_path.read_text(encoding="utf-8"))
            except Exception:
                bouts = []
            for b in bouts:
                wc = b.get("weight_class")
                norm = normalize_division(wc)
                if norm and norm not in divisions:
                    divisions[norm] = wc or norm.title()
    return sorted(divisions.items(), key=lambda kv: kv[1].lower())


def load_recent_pairs(processed_dir: Path) -> set[tuple[str, str]]:
    recent_pairs: set[tuple[str, str]] = set()
    bouts_path = processed_dir / "bouts.json"
    if processed_dir.exists() and bouts_path.exists():
        try:
            bouts = json.loads(bouts_path.read_text(encoding="utf-8"))
            for b in bouts:
                r = b.get("red_fighter_id")
                bl = b.get("blue_fighter_id")
                if r and bl:
                    recent_pairs.add((min(r, bl), max(r, bl)))
        except Exception:
            pass
    return recent_pairs


def find_fighter_rows(rows: list[dict], name: str) -> list[dict]:
    """Case-insensitive substring search for a fighter by name."""
    needle = name.strip().lower()
    return [r for r in rows if needle in (r.get("name") or "").lower()]


def validate_local_data(processed_dir: Path, features_path: Path) -> tuple[bool, str]:
    """Check that processed dir and features file exist and contain real data."""
    bouts_path = processed_dir / "bouts.json"

    if not processed_dir.exists():
        return False, (
            f"Processed data directory not found: {processed_dir}\n"
            "  Run: fightmatch scrape --since YYYY-MM-DD --out data/raw\n"
            "       fightmatch build-dataset --raw data/raw --out data/processed"
        )
    if not bouts_path.exists():
        return False, (
            f"bouts.json not found in {processed_dir}\n"
            "  Run: fightmatch build-dataset --raw data/raw --out data/processed"
        )
    try:
        bouts = json.loads(bouts_path.read_text(encoding="utf-8"))
    except Exception:
        bouts = []
    if not bouts:
        return False, (
            f"bouts.json in {processed_dir} is empty.\n"
            "  Run: fightmatch build-dataset --raw data/raw --out data/processed\n"
            "  If data/raw is also empty, a new scrape is needed:\n"
            "       fightmatch scrape --since YYYY-MM-DD --out data/raw"
        )
    if not features_path.exists():
        return False, (
            f"Features file not found: {features_path}\n"
            f"  Run: fightmatch features --in {processed_dir} --out {features_path}"
        )
    try:
        rows = load_features_csv(features_path)
    except Exception:
        rows = []
    if not rows:
        return False, (
            f"Features file {features_path} contains no rows.\n"
            f"  Run: fightmatch features --in {processed_dir} --out {features_path}"
        )
    return True, ""


def write_division_markdown(
    md_path: Path,
    division: str,
    top_contenders: list[dict],
    matchup_recommendations: list[dict],
) -> None:
    """Human-readable division report with promoter scoring when available."""
    ts = datetime.now().isoformat(timespec="seconds")
    with md_path.open("w", encoding="utf-8") as f:
        f.write("# FightMatch division report\n\n")
        f.write(f"**Division:** {division or 'All'}  \n")
        f.write(f"**Generated:** {ts}\n\n")
        f.write("### How to interpret this report\n")
        f.write(
            "- Top contenders are ordered by the FightMatch fighter rating (0\u201310 scale). "
            "The rating combines activity, form, striking/grappling efficiency, opponent quality, "
            "and finish ability.\n"
        )
        f.write(
            "- Recommended matchups are ordered by promoter score \u2014 a weighted combination of "
            "competitive balance, divisional relevance, activity readiness, freshness, style interest, "
            "and fan engagement proxy.\n\n"
        )

        f.write("### Top contenders\n\n")
        for c in top_contenders:
            name = c.get("name") or c.get("fighter_id") or ""
            score = float(c.get("score", 0.0))
            f.write(f"{c.get('rank')}. {name} ({score:.2f})\n")

        f.write("\n### Top 5 matchup recommendations\n")
        for i, rec in enumerate(matchup_recommendations[:5], start=1):
            f.write(f"\n#### {i}. {rec['matchup']}\n")
            score_a = float(rec.get("score_a", 0.0))
            score_b = float(rec.get("score_b", 0.0))
            f.write(f"Ratings: {score_a:.2f} vs {score_b:.2f}")
            if "promoter_score" in rec:
                f.write(
                    f"  |  Promoter score: {rec['promoter_score']:.3f} ({rec.get('promoter_tier', '')})"
                )
            f.write("\n")
            if "win_prob_a" in rec:
                f.write(
                    f"Win probability: {rec['win_prob_a']:.0%} / {rec['win_prob_b']:.0%}  "
                )
                f.write(f"  Competitiveness: {rec.get('competitiveness', 0):.2f}")
                f.write(f"  |  Style contrast: {rec.get('style_contrast', 0):.2f}\n")
            expl = rec.get("explanations") or []
            for reason in expl[:4]:
                f.write(f"- {reason}\n")
