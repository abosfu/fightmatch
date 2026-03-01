"""Build normalized dataset from raw UFCStats HTML (no fightmatch.data package)."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from .parse import parse_event_page, parse_fight_details


def _normalize_date(s: str | None) -> str | None:
    if not s:
        return None
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s


def build_dataset(raw_dir: Path, out_dir: Path) -> None:
    """Read raw_dir/ufcstats (events/*.html, fights/*.html), write fighters.json, events.json, bouts.json, stats.jsonl."""
    raw_base = Path(raw_dir) / "ufcstats"
    events_dir = raw_base / "events"
    fights_dir = raw_base / "fights"
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    fighters_by_id: dict[str, dict] = {}
    events_list: list[dict] = []
    bouts_list: list[dict] = []
    stats_list: list[dict] = []

    if events_dir.exists():
        for p in sorted(events_dir.glob("*.html")):
            event_id = p.stem
            html = p.read_text(encoding="utf-8", errors="replace")
            event_info, bouts, fight_links = parse_event_page(html, event_id)
            events_list.append(event_info)
            for b in bouts:
                bouts_list.append(b)
                for fid in (b.get("red_fighter_id"), b.get("blue_fighter_id")):
                    if fid and fid not in fighters_by_id:
                        fighters_by_id[fid] = {"fighter_id": fid, "name": fid, "height": None, "reach": None, "stance": None, "dob": None}

            for fl in fight_links:
                bout_id = fl.get("bout_id")
                fight_path = fights_dir / f"{bout_id}.html"
                if not fight_path.exists():
                    continue
                try:
                    fight_html = fight_path.read_text(encoding="utf-8", errors="replace")
                    red_s, blue_s, fighter_infos = parse_fight_details(fight_html, bout_id)
                    for info in fighter_infos:
                        fid = info.get("fighter_id")
                        if fid:
                            fighters_by_id.setdefault(fid, {"fighter_id": fid, "name": fid, "height": None, "reach": None, "stance": None, "dob": None})["name"] = info.get("name", fid)
                    if red_s and red_s.get("fighter_id"):
                        stats_list.append(red_s)
                    if blue_s and blue_s.get("fighter_id"):
                        stats_list.append(blue_s)
                except Exception:
                    continue

    seen_events: set[str] = set()
    unique_events: list[dict] = []
    for e in events_list:
        eid = e.get("event_id")
        if eid and eid not in seen_events:
            seen_events.add(eid)
            if e.get("date"):
                e = {**e, "date": _normalize_date(e["date"])}
            unique_events.append(e)

    (out_dir / "fighters.json").write_text(json.dumps(list(fighters_by_id.values()), indent=2), encoding="utf-8")
    (out_dir / "events.json").write_text(json.dumps(unique_events, indent=2), encoding="utf-8")
    (out_dir / "bouts.json").write_text(json.dumps(bouts_list, indent=2), encoding="utf-8")
    with open(out_dir / "stats.jsonl", "w", encoding="utf-8") as f:
        for s in stats_list:
            f.write(json.dumps(s) + "\n")
