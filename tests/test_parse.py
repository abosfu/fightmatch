"""Test parse functions with fixture HTML."""

from pathlib import Path

import pytest

from fightmatch.scrape.parse import (
    parse_events_list,
    parse_event_page,
    parse_fight_details,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_events_list():
    html = (FIXTURES / "events_list.html").read_text()
    events = parse_events_list(html, "https://www.ufcstats.com")
    assert len(events) >= 2
    ids = {e["event_id"] for e in events}
    assert "abc123" in ids
    assert "def456" in ids
    one = next(e for e in events if e["event_id"] == "abc123")
    assert "Test" in one["name"]


def test_parse_event_page():
    html = (FIXTURES / "event_abc123.html").read_text()
    event_info, bouts, fight_links = parse_event_page(html, "abc123", "https://www.ufcstats.com")
    assert event_info["event_id"] == "abc123"
    assert "Test" in event_info["name"]
    assert len(bouts) >= 2
    b1 = next(b for b in bouts if b["bout_id"] == "bout1")
    assert b1["red_fighter_id"] == "fred1"
    assert b1["blue_fighter_id"] == "barney2"
    assert b1["weight_class"] == "Lightweight"
    assert b1["winner"] == "red"
    assert len(fight_links) >= 2


def test_parse_fight_details():
    html = (FIXTURES / "fight_bout1.html").read_text()
    red_s, blue_s, fighter_infos = parse_fight_details(html, "bout1")
    assert red_s is not None
    assert blue_s is not None
    assert red_s.get("sig_str_landed") == 45
    assert red_s.get("sig_str_att") == 80
    assert blue_s.get("sig_str_landed") == 30
    assert red_s.get("td_landed") == 2
    assert red_s.get("td_att") == 5
    assert len(fighter_infos) == 2
