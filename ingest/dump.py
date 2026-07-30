"""P2. Print postings as readable text so I can sit down and tally the formats.

    uv run ingest/dump.py -n 20
    uv run ingest/dump.py -n 30 > /tmp/posts.txt
    uv run ingest/dump.py --ids 48919859,48915735

Tally goes in docs/formats.md. Read them, don't skim them.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ingest.corpus import by_id, latest, to_text  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=20)
    ap.add_argument("--ids", help="comma-separated objectIDs, e.g. the ten POC posts")
    args = ap.parse_args()

    if args.ids:
        chosen = by_id(args.ids.split(","))
        header = f"{len(chosen)} posts by id"
    else:
        thread = latest()
        chosen = thread["comments"][: args.n]
        header = f"{thread.get('title') or thread['thread_id']}  ({len(thread['comments'])} postings)"

    print(f"{header}\n")
    for i, c in enumerate(chosen, 1):
        body = to_text(c.get("comment_text"))
        print("=" * 78)
        print(f"[{i}] id={c['objectID']}  by {c['author']}  {len(body)} chars")
        print("=" * 78)
        print(body)
        print()


if __name__ == "__main__":
    main()
