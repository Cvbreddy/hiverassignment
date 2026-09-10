from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .agent import Example, SupportAgent
from .data import load_examples
from .evaluate import evaluate, judge_rubric, load_golden, write_json


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the auditable Hiver support agent")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo")
    demo.add_argument("--text", default="My order is late and I need tracking help")
    run = sub.add_parser("run")
    run.add_argument("--input", required=True)
    run.add_argument("--golden", required=True)
    run.add_argument("--brand", default="Acme")
    run.add_argument("--output", default="reports/metrics.json")
    run.add_argument("--brand-author-id")
    run.add_argument("--max-rows", type=int, help="Read only the first N source rows for a bounded Kaggle run")
    rubric = sub.add_parser("rubric")
    rubric.add_argument("--output", default="reports/judge_rubric.json")
    return parser.parse_args()


def main() -> None:
    args = _args()
    if args.command == "rubric":
        write_json(judge_rubric(), args.output)
        print(f"Wrote {args.output}")
        return
    if args.command == "demo":
        examples = [
            Example("Where is my order?", "delivery_tracking", "Look up the order status and share tracking privately.", "I’m sorry it’s taking longer than expected. Please DM your order number so we can check the tracking."),
            Example("I was charged twice", "billing_refund", "Verify the duplicate charge and refund the extra payment.", "I’m sorry about the duplicate charge. Please DM your order details so we can investigate securely."),
            Example("The app crashes on launch", "technical_problem", "Ask for device/app version, then provide troubleshooting or escalate.", "Sorry about that. Please DM your device and app version and we’ll help troubleshoot."),
        ]
        print(json.dumps(SupportAgent(examples).predict(args.text).to_dict(), indent=2))
        return
    examples = load_examples(args.input, brand=args.brand, brand_author_id=args.brand_author_id, max_rows=args.max_rows)
    if not examples:
        raise SystemExit("No usable conversation pairs found. Check the CSV columns and brand-author-id.")
    agent = SupportAgent(examples, brand=args.brand)
    metrics = evaluate(agent, load_golden(args.golden))
    write_json(metrics, args.output)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
