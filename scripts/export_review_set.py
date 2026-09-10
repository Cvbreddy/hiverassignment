from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export real inbound messages for blind human labeling")
    parser.add_argument("--input", required=True)
    parser.add_argument("--brand-author-id", required=True)
    parser.add_argument("--output", default="data/review_candidates.csv")
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()

    replies: dict[str, str] = {}
    with Path(args.input).open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row.get("author_id") == args.brand_author_id:
                replies[row.get("tweet_id", "")] = row.get("text", "")

    candidates = []
    with Path(args.input).open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row.get("inbound", "").lower() not in {"true", "1", "yes"}:
                continue
            reply = replies.get(row.get("response_tweet_id", ""))
            if reply is None:
                continue
            candidates.append({
                "id": row.get("tweet_id", ""),
                "text": row.get("text", ""),
                "historical_reply": reply,
                "intent": "",
                "expected_action": "",
                "review_notes": "",
            })
            if len(candidates) >= args.limit:
                break

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(candidates[0]) if candidates else ["id", "text", "historical_reply", "intent", "expected_action", "review_notes"])
        writer.writeheader()
        writer.writerows(candidates)
    print(f"wrote {len(candidates)} real review candidates to {output}")


if __name__ == "__main__":
    main()
