"""Data schemas for fighters, events, bouts, fight stats."""

from __future__ import annotations

from typing import Optional

# Use optional pydantic; fallback to dataclasses if we want zero deps for core
try:
    from pydantic import BaseModel
except ImportError:
    BaseModel = None  # type: ignore

if BaseModel is not None:

    class Fighter(BaseModel):
        fighter_id: str
        name: str
        height: Optional[str] = None
        reach: Optional[str] = None
        stance: Optional[str] = None
        dob: Optional[str] = None

    class Event(BaseModel):
        event_id: str
        name: str
        date: Optional[str] = None
        location: Optional[str] = None

    class Bout(BaseModel):
        bout_id: str
        event_id: str
        red_fighter_id: str
        blue_fighter_id: str
        weight_class: Optional[str] = None
        method: Optional[str] = None
        round: Optional[int] = None
        time: Optional[str] = None
        winner: Optional[str] = None  # "red" | "blue" | "draw" | "nc"
        ref: Optional[str] = None

    class FightStats(BaseModel):
        """Per fighter per bout."""
        bout_id: str
        fighter_id: str
        corner: str  # "red" | "blue"
        sig_str_landed: Optional[int] = None
        sig_str_att: Optional[int] = None
        total_str_landed: Optional[int] = None
        total_str_att: Optional[int] = None
        td_landed: Optional[int] = None
        td_att: Optional[int] = None
        sub_att: Optional[int] = None
        rev: Optional[int] = None
        ctrl_time_seconds: Optional[float] = None

else:
    from dataclasses import dataclass

    @dataclass
    class Fighter:
        fighter_id: str
        name: str
        height: Optional[str] = None
        reach: Optional[str] = None
        stance: Optional[str] = None
        dob: Optional[str] = None

    @dataclass
    class Event:
        event_id: str
        name: str
        date: Optional[str] = None
        location: Optional[str] = None

    @dataclass
    class Bout:
        bout_id: str
        event_id: str
        red_fighter_id: str
        blue_fighter_id: str
        weight_class: Optional[str] = None
        method: Optional[str] = None
        round: Optional[int] = None
        time: Optional[str] = None
        winner: Optional[str] = None
        ref: Optional[str] = None

    @dataclass
    class FightStats:
        bout_id: str
        fighter_id: str
        corner: str
        sig_str_landed: Optional[int] = None
        sig_str_att: Optional[int] = None
        total_str_landed: Optional[int] = None
        total_str_att: Optional[int] = None
        td_landed: Optional[int] = None
        td_att: Optional[int] = None
        sub_att: Optional[int] = None
        rev: Optional[int] = None
        ctrl_time_seconds: Optional[float] = None
