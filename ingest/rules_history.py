"""Track rules-only non-null extraction counts by America/Toronto run date and HN thread ID."""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest import fetch, rules
from ingest.corpus import to_text
from ingest.schema import Extraction

TORONTO = ZoneInfo("America/Toronto")


def run_date(now=None):
    """Return the America/Toronto local date for a run (default: now)."""
    now = now or datetime.now(UTC)
    return now.astimezone(TORONTO).date().isoformat()

FIELDS = tuple(Extraction.model_fields)
DEFAULT_HISTORY = Path(__file__).resolve().parent.parent / "data" / "rules_history.jsonl"


def count_extractions(comments):
    """Count non-null values, including False and empty lists, once per post/field."""
    counts = dict.fromkeys(FIELDS, 0)
    total = 0
    for comment in comments:
        extraction, _ = rules.parse(to_text(comment.get("comment_text")))
        total += 1
        for field in FIELDS:
            counts[field] += int(getattr(extraction, field) is not None)
    return {"total_posts": total, **counts}


def update_history(path, row):
    """Preserve other runs and replace all rows matching this date/thread key."""
    path = Path(path)
    rows = []
    if path.exists():
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    key = (row["date"], str(row["thread_id"]))
    rows = [r for r in rows if (r["date"], str(r["thread_id"])) != key]
    rows.append(row)
    rows.sort(key=lambda r: (r["date"], str(r["thread_id"])))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return rows


def trend_table(rows):
    """Render one row per recorded run, in date/thread order."""
    columns = ("date", "thread_id", "total_posts", *FIELDS)
    values = [list(columns)]
    for row in sorted(rows, key=lambda r: (r["date"], str(r["thread_id"]))):
        values.append([str(row[column]) for column in columns])
    widths = [max(len(row[i]) for row in values) for i in range(len(columns))]
    return "\n".join(
        "  ".join(value.ljust(width) for value, width in zip(row, widths)).rstrip()
        for row in values
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--thread", required=True, type=int, help="HN hiring thread ID")
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY, help="JSONL history path")
    args = parser.parse_args(argv)
    date = run_date()
    with fetch.client() as client:
        counts = count_extractions(fetch.comments(client, args.thread))
    row = {"date": date, "thread_id": str(args.thread), **counts}
    print(trend_table(update_history(args.history, row)))


if __name__ == "__main__":
    main()
