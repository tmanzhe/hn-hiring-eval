"""P2. Print postings as readable text so I can sit down and tally the formats.

    python3 ingest/dump.py -n 20
    python3 ingest/dump.py -n 30 > /tmp/posts.txt

Tally goes in docs/formats.md. Read them, don't skim them.
"""

import argparse
import html
import json
import re
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def to_text(s):
    s = re.sub(r"<p>", "\n\n", s or "")
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=20)
    ap.add_argument("--file", type=Path)
    args = ap.parse_args()

    path = args.file or max(RAW.glob("*.json"), key=lambda p: p.stat().st_mtime, default=None)
    if not path:
        raise SystemExit("nothing in data/raw. run ingest/fetch.py first")

    data = json.loads(path.read_text())
    posts = data["comments"][: args.n]
    print(f"{data.get('title') or data['thread_id']}  ({len(data['comments'])} postings)\n")

    for i, c in enumerate(posts, 1):
        body = to_text(c.get("comment_text"))
        print("=" * 78)
        print(f"[{i}] id={c['objectID']}  by {c['author']}  {len(body)} chars")
        print("=" * 78)
        print(body)
        print()


if __name__ == "__main__":
    main()
