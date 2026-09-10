from __future__ import annotations

import argparse
import csv
from pathlib import Path

from hiver_agent.agent import HIGH_RISK, SENSITIVE, classify


def main() -> None:
    parser = argparse.ArgumentParser(description="Fill preliminary AI-assisted labels for review")
    parser.add_argument("--input", default="data/apple_support_review.csv")
    parser.add_argument("--output", default="data/apple_support_review_labeled.csv")
    args = parser.parse_args()

    with Path(args.input).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        intent, confidence = classify(row["text"])
        lower = row["text"].lower()
        reasons = confidence < 0.66 or intent in {"complaint", "other"}
        reasons = reasons or any(term in lower for term in SENSITIVE + HIGH_RISK)
        row["intent"] = intent
        row["expected_action"] = "escalate" if reasons else "auto-handle"
        row["review_notes"] = "AI-assisted preliminary label; requires human review"

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} preliminary labels to {output}")


if __name__ == "__main__":
    main()
