import argparse
import json

from .train import train_and_evaluate
from .matchmaking import recommend_cli_output, recommend


def train_cmd() -> None:
    p = argparse.ArgumentParser(description="Train win-probability models and write metrics + artifacts")
    p.add_argument("--db-url", default=None, help="DATABASE_URL (default: env)")
    args = p.parse_args()
    metrics = train_and_evaluate(db_url=args.db_url)
    print(json.dumps(metrics, indent=2))


def recommend_cmd() -> None:
    p = argparse.ArgumentParser(description="Run matchmaking: ranked candidates with p_win and explanations")
    p.add_argument("--fighter_id", required=True, help="Fighter UUID")
    p.add_argument("--weight_class", required=True, help="Weight class name")
    p.add_argument("--model", default="lightgbm", help="Model name (lightgbm or logistic_regression)")
    p.add_argument("--top_k", type=int, default=10)
    args = p.parse_args()
    print(recommend_cli_output(args.fighter_id, args.weight_class, model_name=args.model, top_k=args.top_k))
