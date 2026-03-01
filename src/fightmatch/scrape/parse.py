"""Parse UFCStats HTML into structured records. Robust: missing -> None, no crash."""

from __future__ import annotations

import re
from typing import Any, Optional

from bs4 import BeautifulSoup

from .schemas import Bout, Event, Fighter, FightStats


def _text(soup: Any) -> str:
    if soup is None:
        return ""
    return (soup.get_text() or "").strip()


def _int(s: str) -> Optional[int]:
    if not s:
        return None
    s = re.sub(r"[^\d-]", "", s)
    try:
        return int(s)
    except ValueError:
        return None


def _float(s: str) -> Optional[float]:
    if not s:
        return None
    s = s.strip().replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _slug_from_href(a: Any) -> Optional[str]:
    if a is None or not getattr(a, "get", None):
        return None
    href = a.get("href") or ""
    # e.g. /fighter-details/abc123 or /event-details/abc123
    parts = href.rstrip("/").split("/")
    return parts[-1] if parts else None


def parse_events_list(html: str, base_url: str = "https://www.ufcstats.com") -> list[dict[str, Any]]:
    """Parse events completed page. Returns list of {event_id, name, date, url}."""
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict[str, Any]] = []
    # UFCStats: table with links to event-details
    for link in soup.select("a[href*='event-details']"):
        href = link.get("href") or ""
        if "event-details" not in href:
            continue
        event_id = _slug_from_href(link)
        if not event_id:
            continue
        name = _text(link)
        if not name:
            continue
        # Date often in same row; try sibling or parent row
        row = link.find_parent("tr")
        date_val: Optional[str] = None
        if row:
            cells = row.find_all("td")
            for td in cells:
                t = _text(td)
                if re.match(r"\d{4}-\d{2}-\d{2}", t) or re.match(r"\w+\s+\d{1,2},\s*\d{4}", t):
                    date_val = t
                    break
        out.append({
            "event_id": event_id,
            "name": name,
            "date": date_val,
            "url": href if href.startswith("http") else f"{base_url.rstrip('/')}{href}",
        })
    return out


def parse_event_page(
    html: str,
    event_id: str,
    base_url: str = "https://www.ufcstats.com",
) -> tuple[Optional[dict], list[dict], list[dict]]:
    """
    Parse single event page. Returns (event_info, bouts[], fight_links_for_stats[]).
    event_info: {event_id, name, date, location}
    bouts: list of bout dicts (bout_id, event_id, red/blue fighter_id, weight_class, method, round, time, winner).
    fight_links_for_stats: [{bout_id, url}, ...] to fetch fight details for stats.
    """
    soup = BeautifulSoup(html, "html.parser")
    event_name = _text(soup.select_one("h2.b-content__title, .b-content__title a, span.b-content__title"))
    if not event_name:
        event_name = f"Event {event_id}"
    date_el = soup.select_one(".b-list__box-list-item span, .b-list__box-list .b-list__box-list-item")
    event_date = _text(date_el) if date_el else None
    location_el = soup.select_one(".b-list__box-list-item:nth-of-type(2)")
    location = _text(location_el) if location_el else None
    event_info: dict[str, Any] = {
        "event_id": event_id,
        "name": event_name,
        "date": event_date,
        "location": location,
    }
    bouts: list[dict[str, Any]] = []
    fight_links: list[dict[str, str]] = []
    # Fights: rows with links to fight-details and fighter-details
    rows = soup.select("tr.b-fight-details__table-row")
    if not rows:
        rows = soup.select("table tbody tr")
    for tr in rows:
        links = tr.find_all("a", href=re.compile(r"fight-details|fighter-details"))
        fight_link = next((a for a in links if "fight-details" in (a.get("href") or "")), None)
        fighter_links = [a for a in links if "fighter-details" in (a.get("href") or "")]
        if not fight_link and not fighter_links:
            continue
        bout_id = _slug_from_href(fight_link) if fight_link else None
        if not bout_id:
            continue
        red_id = _slug_from_href(fighter_links[0]) if len(fighter_links) > 0 else None
        blue_id = _slug_from_href(fighter_links[1]) if len(fighter_links) > 1 else None
        if not red_id or not blue_id:
            continue
        # Method, round, time from cells
        cells = tr.find_all("td")
        method = round_val = time_val = weight_class = winner = None
        for i, td in enumerate(cells):
            t = _text(td)
            if "Decision" in t or "KO" in t or "TKO" in t or "SUB" in t or "DQ" in t or "No Contest" in t or "Overturned" in t:
                method = t
            if re.match(r"^\d+$", t) and round_val is None and len(t) <= 2:
                round_val = _int(t)
            if re.match(r"\d+:\d+", t):
                time_val = t
            if any(w in t.lower() for w in ["heavyweight", "lightweight", "welterweight", "middleweight", "featherweight", "bantamweight", "flyweight", "light heavyweight", "women"]):
                weight_class = t
        # Winner: often first fighter in row is winner for W/L column
        wl_cell = tr.select_one("td .b-flag__text, td .b-flag")
        if wl_cell:
            wl = _text(wl_cell).upper()
            if "W" in wl or "WIN" in wl:
                winner = "red"  # UFCStats often lists winner first
            elif "L" in wl or "LOSS" in wl:
                winner = "blue"
            elif "D" in wl or "DRAW" in wl:
                winner = "draw"
            elif "NC" in wl or "NO CONTEST" in wl:
                winner = "nc"
        bouts.append({
            "bout_id": bout_id,
            "event_id": event_id,
            "red_fighter_id": red_id,
            "blue_fighter_id": blue_id,
            "weight_class": weight_class,
            "method": method,
            "round": round_val,
            "time": time_val,
            "winner": winner,
            "ref": None,
        })
        if fight_link:
            href = fight_link.get("href") or ""
            fight_links.append({
                "bout_id": bout_id,
                "url": href if href.startswith("http") else f"{base_url.rstrip('/')}{href}",
            })
    return event_info, bouts, fight_links


def parse_fight_details(
    html: str,
    bout_id: str,
) -> tuple[Optional[dict], Optional[dict], list[dict]]:
    """
    Parse fight details page for stats. Returns (red_stats, blue_stats, fighter_infos).
    Each stats dict: FightStats fields. fighter_infos: list of {fighter_id, name, ...} from page.
    """
    soup = BeautifulSoup(html, "html.parser")
    fighter_infos: list[dict[str, Any]] = []
    # Two sides: red and blue. UFCStats uses .b-fight-details__person or similar.
    persons = soup.select(".b-fight-details__person, .b-fight-details__persons")
    if not persons:
        persons = soup.select("[class*='fight-details'] [class*='person']")
    links = soup.find_all("a", href=re.compile(r"fighter-details"))
    for a in links[:2]:
        fid = _slug_from_href(a)
        if fid:
            fighter_infos.append({"fighter_id": fid, "name": _text(a)})
    # Stats table: Sig str, TD, etc. Often two columns (red | blue) or two rows.
    def _parse_stats_table() -> tuple[Optional[dict], Optional[dict]]:
        red_s: dict[str, Any] = {"bout_id": bout_id, "fighter_id": "", "corner": "red"}
        blue_s: dict[str, Any] = {"bout_id": bout_id, "fighter_id": "", "corner": "blue"}
        tables = soup.select("table.b-fight-details__table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue
                label = _text(cells[0]).lower()
                v1 = _text(cells[1]) if len(cells) > 1 else ""
                v2 = _text(cells[2]) if len(cells) > 2 else ""
                if "sig. str" in label or "significant" in label:
                    parts1 = re.split(r"\s+of\s+", v1)
                    parts2 = re.split(r"\s+of\s+", v2)
                    red_s["sig_str_landed"] = _int(parts1[0]) if parts1 else _int(v1)
                    red_s["sig_str_att"] = _int(parts1[1]) if len(parts1) > 1 else None
                    blue_s["sig_str_landed"] = _int(parts2[0]) if parts2 else _int(v2)
                    blue_s["sig_str_att"] = _int(parts2[1]) if len(parts2) > 1 else None
                elif "total str" in label or "total strike" in label:
                    parts1 = re.split(r"\s+of\s+", v1)
                    parts2 = re.split(r"\s+of\s+", v2)
                    red_s["total_str_landed"] = _int(parts1[0]) if parts1 else _int(v1)
                    red_s["total_str_att"] = _int(parts1[1]) if len(parts1) > 1 else None
                    blue_s["total_str_landed"] = _int(parts2[0]) if parts2 else _int(v2)
                    blue_s["total_str_att"] = _int(parts2[1]) if len(parts2) > 1 else None
                elif "takedown" in label or (label and "td" in label and "sub" not in label):
                    parts1 = re.split(r"\s+of\s+", v1)
                    parts2 = re.split(r"\s+of\s+", v2)
                    red_s["td_landed"] = _int(parts1[0]) if parts1 else _int(v1)
                    red_s["td_att"] = _int(parts1[1]) if len(parts1) > 1 else None
                    blue_s["td_landed"] = _int(parts2[0]) if parts2 else _int(v2)
                    blue_s["td_att"] = _int(parts2[1]) if len(parts2) > 1 else None
                elif "sub" in label:
                    red_s["sub_att"] = _int(v1)
                    blue_s["sub_att"] = _int(v2)
                elif "reversal" in label or "rev" in label:
                    red_s["rev"] = _int(v1)
                    blue_s["rev"] = _int(v2)
                elif "control" in label or "ctrl" in label:
                    def to_seconds(s: str) -> Optional[float]:
                        if not s:
                            return None
                        if ":" in s:
                            parts = s.strip().split(":")
                            if len(parts) == 2:
                                try:
                                    return int(parts[0]) * 60 + float(parts[1])
                                except ValueError:
                                    return None
                        return _float(s)
                    red_s["ctrl_time_seconds"] = to_seconds(v1)
                    blue_s["ctrl_time_seconds"] = to_seconds(v2)
        if fighter_infos:
            red_s["fighter_id"] = fighter_infos[0].get("fighter_id", "")
            blue_s["fighter_id"] = fighter_infos[1].get("fighter_id", "") if len(fighter_infos) > 1 else ""
        return red_s, blue_s

    red_stats, blue_stats = _parse_stats_table()
    if fighter_infos and red_stats and blue_stats:
        red_stats["fighter_id"] = fighter_infos[0].get("fighter_id", "")
        blue_stats["fighter_id"] = fighter_infos[1].get("fighter_id", "") if len(fighter_infos) > 1 else ""
    return red_stats, blue_stats, fighter_infos


def schema_to_dict(obj: Any) -> dict[str, Any]:
    """Convert schema instance to dict for JSON."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return dict(obj)
