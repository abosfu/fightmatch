import sys
import argparse
import json

from .train import train_and_evaluate
from .matchmaking import recommend, recommend_cli_output


def main():
    p = argparse.ArgumentParser(description="FightMatch modeling CLI")
    sub = p.add_subparsers(dest="cmd", required=True)
    train_p = sub.add_parser("train")
    train_p.add_argument("--db-url", default=None)
    rec_p = sub.add_parser("recommend")
    rec_p.add_argument("--fighter_id", required=True)
    rec_p.add_argument("--weight_class", required=True)
    rec_p.add_argument("--model", default="lightgbm")
    rec_p.add_argument("--top_k", type=int, default=10)
    args = p.parse_args()

    if args.cmd == "train":
        metrics = train_and_evaluate(db_url=args.db_url)
        print(json.dumps(metrics, indent=2))
    elif args.cmd == "recommend":
        print(recommend_cli_output(args.fighter_id, args.weight_class, model_name=args.model, top_k=args.top_k))


if __name__ == "__main__":
    main()
