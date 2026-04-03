"""Pydantic V2 data schemas for fighters, events, bouts, fight stats."""

from __future__ import annotations

from pydantic import BaseModel


class Fighter(BaseModel):
    fighter_id: str
    name: str
    height: str | None = None
    reach: str | None = None
    stance: str | None = None
    dob: str | None = None


class Event(BaseModel):
    event_id: str
    name: str
    date: str | None = None
    location: str | None = None


class Bout(BaseModel):
    bout_id: str
    event_id: str
    red_fighter_id: str
    blue_fighter_id: str
    weight_class: str | None = None
    method: str | None = None
    round: int | None = None
    time: str | None = None
    winner: str | None = None  # "red" | "blue" | "draw" | "nc"
    ref: str | None = None


class FightStats(BaseModel):
    """Per-fighter, per-bout striking/grappling stats."""

    bout_id: str
    fighter_id: str
    corner: str  # "red" | "blue"
    sig_str_landed: int | None = None
    sig_str_att: int | None = None
    total_str_landed: int | None = None
    total_str_att: int | None = None
    td_landed: int | None = None
    td_att: int | None = None
    sub_att: int | None = None
    rev: int | None = None
    ctrl_time_seconds: float | None = None
