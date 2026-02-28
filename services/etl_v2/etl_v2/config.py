import os
from pathlib import Path

def get_db_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        env_file = Path(__file__).resolve().parents[2] / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DATABASE_URL="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    if not url:
        raise ValueError("DATABASE_URL not set. Set env or create services/etl_v2/.env")
    return url
