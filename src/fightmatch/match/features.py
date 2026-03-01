"""Build per-fighter features CSV from processed JSON/JSONL (no fightmatch.data package)."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path


def _parse_date(s: str | None) -> datetime | None:
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"):
        try:
            if fmt == "%Y-%m-%d" and len(s) >= 10:
                return datetime.strptime(s[:10], fmt)
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def load_processed(processed_dir: Path) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Load fighters, events, bouts, stats from processed dir."""
    p = Path(processed_dir)
    fighters = json.loads((p / "fighters.json").read_text(encoding="utf-8")) if (p / "fighters.json").exists() else []
    events = json.loads((p / "events.json").read_text(encoding="utf-8")) if (p / "events.json").exists() else []
    bouts = json.loads((p / "bouts.json").read_text(encoding="utf-8")) if (p / "bouts.json").exists() else []
    stats_list: list[dict] = []
    if (p / "stats.jsonl").exists():
        with open(p / "stats.jsonl", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    stats_list.append(json.loads(line))
    return fighters, events, bouts, stats_list


def build_features(processed_dir: Path, out_path: Path) -> None:
    """Build per-fighter features CSV. Writes fighter_id, name, weight_class, and rolling feature columns."""
    fighters, events, bouts, stats_list = load_processed(processed_dir)
    event_dates = {e["event_id"]: _parse_date(e.get("date")) for e in events if e.get("event_id")}
    event_dates = {k: v for k, v in event_dates.items() if v is not None}
    stats_by_bout: dict[str, list[dict]] = {}
    for s in stats_list:
        bid = s.get("bout_id")
        if bid:
            stats_by_bout.setdefault(bid, []).append(s)

    fighter_bouts: dict[str, list[dict]] = {}
    for b in bouts:
        eid = b.get("event_id")
        if not eid or eid not in event_dates:
            continue
        dt = event_dates[eid]
        bid = b.get("bout_id")
        red_id = b.get("red_fighter_id")
        blue_id = b.get("blue_fighter_id")
        winner = b.get("winner")
        wc = b.get("weight_class")
        stat_rows = stats_by_bout.get(bid, [])
        red_s = next((r for r in stat_rows if r.get("corner") == "red"), {})
        blue_s = next((r for r in stat_rows if r.get("corner") == "blue"), {})
        for fid, opp, corner, st in [(red_id, blue_id, "red", red_s), (blue_id, red_id, "blue", blue_s)]:
            if not fid:
                continue
            won = (winner == "red" and corner == "red") or (winner == "blue" and corner == "blue")
            fighter_bouts.setdefault(fid, []).append({
                "date": dt, "opponent_id": opp, "won": won, "weight_class": wc,
                "stat": st, "round_minutes": 5.0,
            })

    fighter_weight_class: dict[str, str] = {}
    for fid, h in fighter_bouts.items():
        if h:
            wc = max(h, key=lambda x: x["date"]).get("weight_class")
            if wc:
                fighter_weight_class[fid] = wc

    fieldnames = [
        "fighter_id", "name", "weight_class",
        "activity_recency_days", "win_streak", "last_5_win_pct",
        "sig_str_diff_per_min", "td_rate", "td_attempts_per_15", "control_per_15",
        "finish_rate", "opponent_recent_win_pct_avg",
    ]
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ref = datetime.now()
    rows: list[dict] = []
    for f in fighters:
        fid = f.get("fighter_id")
        if not fid:
            continue
        history = sorted(fighter_bouts.get(fid, []), key=lambda x: x["date"], reverse=True)
        wc = fighter_weight_class.get(fid)
        if not history:
            rows.append({k: None for k in fieldnames})
            rows[-1]["fighter_id"] = fid
            rows[-1]["name"] = f.get("name", fid)
            rows[-1]["weight_class"] = wc
            rows[-1]["win_streak"] = 0
            continue
        recency = (ref - history[0]["date"]).days
        win_streak = 0
        for h in history:
            if h["won"]:
                win_streak += 1
            else:
                break
        last_5 = history[:5]
        last_5_win_pct = sum(1 for h in last_5 if h["won"]) / len(last_5) if last_5 else None
        finishes = sum(1 for h in history if (h.get("round_minutes") or 5) < 4)
        finish_rate = finishes / len(history) if history else None
        sig_per_min = 0.0
        td_landed = td_att = ctrl = 0
        total_mins = 0.1
        for h in history:
            st = h.get("stat") or {}
            m = h.get("round_minutes") or 5.0
            total_mins += m
            sig_per_min += (st.get("sig_str_landed") or 0) / m
            td_landed += st.get("td_landed") or 0
            td_att += st.get("td_att") or 1
            ctrl += st.get("ctrl_time_seconds") or 0
        td_rate = td_landed / max(1, td_att)
        td_per_15 = (td_landed + td_att) / max(0.01, total_mins) * 15
        ctrl_per_15 = ctrl / max(0.01, total_mins) * 15 * 60
        opp_avg = None
        rows.append({
            "fighter_id": fid, "name": f.get("name", fid), "weight_class": wc,
            "activity_recency_days": recency, "win_streak": win_streak,
            "last_5_win_pct": round(last_5_win_pct, 4) if last_5_win_pct is not None else None,
            "sig_str_diff_per_min": round(sig_per_min / max(1, len(history)), 4),
            "td_rate": round(td_rate, 4), "td_attempts_per_15": round(td_per_15, 4),
            "control_per_15": round(ctrl_per_15, 4),
            "finish_rate": round(finish_rate, 4) if finish_rate is not None else None,
            "opponent_recent_win_pct_avg": opp_avg,
        })

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
