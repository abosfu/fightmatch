"""SQLAlchemy ORM models for FightMatch.

Tables
------
fighters    — one row per UFC fighter (master list)
events      — one row per UFC event
bouts       — one row per fight (two fighters per bout)
fight_stats — per-fighter, per-bout striking/grappling statistics
"""

from pathlib import Path

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

# ---------------------------------------------------------------------------
# Database location — project root / fightmatch.db
# ---------------------------------------------------------------------------
_DB_PATH = Path(__file__).resolve().parents[3] / "fightmatch.db"
DATABASE_URL = f"sqlite:///{_DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Fighter(Base):
    """Master fighter record sourced from processed/fighters.json."""

    __tablename__ = "fighters"

    fighter_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    height = Column(String)  # e.g. "6' 0\""
    reach = Column(String)  # e.g. "72\""
    stance = Column(String)  # Orthodox | Southpaw | Switch
    dob = Column(String)  # ISO date string YYYY-MM-DD

    # Relationships
    red_bouts = relationship(
        "Bout", foreign_keys="Bout.red_fighter_id", back_populates="red_fighter"
    )
    blue_bouts = relationship(
        "Bout", foreign_keys="Bout.blue_fighter_id", back_populates="blue_fighter"
    )
    stats = relationship("FightStats", back_populates="fighter")

    def __repr__(self) -> str:
        return f"<Fighter {self.fighter_id} {self.name!r}>"


class Event(Base):
    """UFC event record sourced from processed/events.json."""

    __tablename__ = "events"

    event_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    date = Column(String)  # ISO date string YYYY-MM-DD
    location = Column(String)

    bouts = relationship("Bout", back_populates="event")

    def __repr__(self) -> str:
        return f"<Event {self.event_id} {self.name!r} {self.date}>"


class Bout(Base):
    """Single fight record sourced from processed/bouts.json.

    winner values: "red" | "blue" | "draw" | "nc"
    """

    __tablename__ = "bouts"

    bout_id = Column(String, primary_key=True)
    event_id = Column(String, ForeignKey("events.event_id"), nullable=False)
    red_fighter_id = Column(String, ForeignKey("fighters.fighter_id"), nullable=False)
    blue_fighter_id = Column(String, ForeignKey("fighters.fighter_id"), nullable=False)
    weight_class = Column(String)
    method = Column(String)  # KO | TKO | SUB | DEC | UDEC | SDEC | MDEC | DQ | NC
    round = Column(Integer)
    time = Column(String)  # MM:SS
    winner = Column(String)  # "red" | "blue" | "draw" | "nc"
    ref = Column(String)

    event = relationship("Event", back_populates="bouts")
    red_fighter = relationship(
        "Fighter", foreign_keys=[red_fighter_id], back_populates="red_bouts"
    )
    blue_fighter = relationship(
        "Fighter", foreign_keys=[blue_fighter_id], back_populates="blue_bouts"
    )
    stats = relationship("FightStats", back_populates="bout")

    def __repr__(self) -> str:
        return f"<Bout {self.bout_id} {self.red_fighter_id} vs {self.blue_fighter_id}>"


class FightStats(Base):
    """Per-fighter, per-bout striking/grappling stats from processed/stats.jsonl.

    corner values: "red" | "blue"
    """

    __tablename__ = "fight_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bout_id = Column(String, ForeignKey("bouts.bout_id"), nullable=False)
    fighter_id = Column(String, ForeignKey("fighters.fighter_id"), nullable=False)
    corner = Column(String, nullable=False)

    sig_str_landed = Column(Integer)
    sig_str_att = Column(Integer)
    total_str_landed = Column(Integer)
    total_str_att = Column(Integer)
    td_landed = Column(Integer)
    td_att = Column(Integer)
    sub_att = Column(Integer)
    rev = Column(Integer)
    ctrl_time_seconds = Column(Float)

    bout = relationship("Bout", back_populates="stats")
    fighter = relationship("Fighter", back_populates="stats")

    def __repr__(self) -> str:
        return f"<FightStats bout={self.bout_id} fighter={self.fighter_id} corner={self.corner}>"
