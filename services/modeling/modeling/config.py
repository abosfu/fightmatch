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
        raise ValueError("DATABASE_URL not set. Set env or create services/modeling/.env")
    return url


def get_reports_dir() -> Path:
    base = Path(__file__).resolve().parents[3]
    reports = base / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    return reports


def get_models_dir() -> Path:
    base = Path(__file__).resolve().parents[3]
    models = base / "models"
    models.mkdir(parents=True, exist_ok=True)
    return models
