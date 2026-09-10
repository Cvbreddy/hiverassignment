from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from itertools import islice

from .agent import Example


TEXT_COLUMNS = ("text", "tweet_text", "message", "body")


def _value(row: dict[str, str], names: tuple[str, ...], default: str = "") -> str:
    for name in names:
        if row.get(name):
            return row[name].strip()
    return default


def load_examples(
    path: str | Path,
    brand: str | None = None,
    brand_author_id: str | None = None,
    max_rows: int | None = None,
) -> list[Example]:
    """Load either the included review CSV or Kaggle's tweet export.

    Kaggle's export has inbound, author_id, text, response_tweet_id and
    in_response_to_tweet_id. Brand replies are used as historical evidence;
    rows with an explicit intent/resolution/public_reply are accepted directly.
    """
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader) if max_rows is None else list(islice(reader, max_rows))
    if not rows:
        return []
    output: list[Example] = []
    direct = all(field in rows[0] for field in ("intent", "resolution", "public_reply"))
    if direct:
        for row in rows:
            if row.get("text") and row.get("intent"):
                output.append(Example(row["text"], row["intent"], row["resolution"], row["public_reply"]))
        return output

    # Keep inbound messages as prompts and pair them with the next brand reply
    # using the dataset's reply id relationship when available.
    by_id = {_value(row, ("tweet_id", "id")): row for row in rows if _value(row, ("tweet_id", "id"))}
    outbound_author_counts = Counter(
        _value(row, ("author_id", "user_id"))
        for row in rows
        if _value(row, ("inbound",)).lower() in {"false", "0", "no"}
    )
    selected_author = brand_author_id or (outbound_author_counts.most_common(1)[0][0] if outbound_author_counts else None)
    for row in rows:
        inbound = _value(row, ("inbound",)).lower() in {"true", "1", "yes"}
        author = _value(row, ("author_id", "user_id"))
        if not inbound or (selected_author and author == selected_author):
            continue
        text = _value(row, TEXT_COLUMNS)
        reply_id = _value(row, ("response_tweet_id",))
        reply_row = by_id.get(reply_id)
        if not text or not reply_row:
            continue
        reply = _value(reply_row, TEXT_COLUMNS)
        output.append(Example(text, "other", reply, reply))
    return output


def group_by_intent(examples: list[Example]) -> dict[str, list[Example]]:
    groups: dict[str, list[Example]] = defaultdict(list)
    for example in examples:
        groups[example.intent].append(example)
    return groups
