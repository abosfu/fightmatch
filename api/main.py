"""FightMatch REST API.

Run with:
    uvicorn api.main:app --reload
"""

from __future__ import annotations

import json
import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from fightmatch.db.models import Fighter, SessionLocal

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

_ENV_PATH = Path(__file__).resolve().parent.parent / "tests" / ".env"
load_dotenv(_ENV_PATH)

_GEMINI_KEY = os.getenv("GEMINI_API_KEY")
_gemini_client: genai.Client | None = None
if _GEMINI_KEY:
    _gemini_client = genai.Client(api_key=_GEMINI_KEY)

_MODEL_NAME = "gemini-2.5-flash"

# ---------------------------------------------------------------------------
# Database schema description fed to the LLM so it can write accurate SQL.
# ---------------------------------------------------------------------------

DB_SCHEMA = """\
SQLite database with the following tables:

CREATE TABLE fighters (
    fighter_id TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    height     TEXT,   -- e.g. "6' 0\\""
    reach      TEXT,   -- e.g. "72\\""
    stance     TEXT,   -- Orthodox | Southpaw | Switch
    dob        TEXT    -- YYYY-MM-DD
);

CREATE TABLE events (
    event_id TEXT PRIMARY KEY,
    name     TEXT NOT NULL,
    date     TEXT,      -- YYYY-MM-DD
    location TEXT
);

CREATE TABLE bouts (
    bout_id         TEXT PRIMARY KEY,
    event_id        TEXT NOT NULL REFERENCES events(event_id),
    red_fighter_id  TEXT NOT NULL REFERENCES fighters(fighter_id),
    blue_fighter_id TEXT NOT NULL REFERENCES fighters(fighter_id),
    weight_class    TEXT,   -- e.g. Welterweight, Lightweight, Middleweight
    method          TEXT,   -- KO/TKO, SUB, DEC, UDEC, SDEC, MDEC, DQ, NC
    round           INTEGER,
    time            TEXT,   -- MM:SS
    winner          TEXT,   -- "red" | "blue" | "draw" | "nc"
    ref             TEXT
);

CREATE TABLE fight_stats (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    bout_id          TEXT NOT NULL REFERENCES bouts(bout_id),
    fighter_id       TEXT NOT NULL REFERENCES fighters(fighter_id),
    corner           TEXT NOT NULL,  -- "red" | "blue"
    sig_str_landed   INTEGER,
    sig_str_att      INTEGER,
    total_str_landed INTEGER,
    total_str_att    INTEGER,
    td_landed        INTEGER,
    td_att           INTEGER,
    sub_att          INTEGER,
    rev              INTEGER,
    ctrl_time_seconds REAL
);
"""

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="FightMatch API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class QueryRequest(BaseModel):
    question: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/fighters")
def list_fighters(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    fighters = db.query(Fighter).limit(50).all()
    return [
        {
            "fighter_id": f.fighter_id,
            "name": f.name,
            "height": f.height,
            "reach": f.reach,
            "stance": f.stance,
            "dob": f.dob,
        }
        for f in fighters
    ]


@app.post("/api/query")
def query_database(body: QueryRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    if not _gemini_client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured.")

    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    # -- Step 1: Generate SQL from the question --------------------------------
    sql_prompt = (
        f"You are a SQLite expert. Given the following database schema:\n\n"
        f"{DB_SCHEMA}\n"
        f"Write a single valid SQLite SELECT query that answers this question:\n"
        f'"{question}"\n\n'
        f"Rules:\n"
        f"- Return ONLY the raw SQL. No markdown, no backticks, no explanation.\n"
        f"- The query must be read-only (SELECT only).\n"
        f"- Limit results to 50 rows unless the question asks for a specific count.\n"
        f"- Use LIKE with % wildcards for name searches (names are mixed case).\n"
    )

    try:
        sql_response = _gemini_client.models.generate_content(
            model=_MODEL_NAME,
            contents=sql_prompt,
        )
        generated_sql = sql_response.text.strip()
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Gemini SQL generation failed: {exc}"
        )

    generated_sql = (
        generated_sql.removeprefix("```sql")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )

    upper = generated_sql.upper()
    if any(
        kw in upper
        for kw in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "ATTACH")
    ):
        raise HTTPException(
            status_code=400, detail="Generated query is not read-only. Aborting."
        )

    # -- Step 2: Execute the SQL -----------------------------------------------
    try:
        result = db.execute(text(generated_sql))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"SQL execution failed: {exc}",
        )

    # -- Step 3: Explain the results -------------------------------------------
    explain_prompt = (
        f"You are a UFC strategic analyst. A user asked:\n"
        f'"{question}"\n\n'
        f"The database returned this data:\n"
        f"{json.dumps(rows[:30], default=str)}\n\n"
        f"Write a 2-3 sentence strategic analyst explanation of what the data shows. "
        f"Be concise, insightful, and speak like a combat-sports analyst."
    )

    try:
        explain_response = _gemini_client.models.generate_content(
            model=_MODEL_NAME,
            contents=explain_prompt,
        )
        explanation = explain_response.text.strip()
    except Exception as exc:
        explanation = f"Explanation unavailable: {exc}"

    return {
        "sql": generated_sql,
        "data": rows,
        "explanation": explanation,
    }
