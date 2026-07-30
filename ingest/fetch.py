"""P1. Grab a Who-is-hiring thread and put the raw JSON on disk.

stdlib only so it runs before uv sync. The real ingest job in step 02 uses httpx.

    python3 ingest/fetch.py              # newest thread
    python3 ingest/fetch.py 41425910     # a specific one
"""

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://hn.algolia.com/api/v1"
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def get(path, **params):
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def latest_thread():
    """Newest 'Who is hiring?' story. whoishiring also posts freelancer and hiring threads."""
    hits = get("search_by_date", tags="story,author_whoishiring", hitsPerPage=20)["hits"]
    for h in hits:
        if "who is hiring" in h["title"].lower():
            return h["objectID"], h["title"], h["created_at"]
    sys.exit("no hiring thread in the last 20 stories from whoishiring")


def comments(thread_id):
    """Top-level comments only. Replies are discussion, not postings."""
    out, page, pages = [], 0, 1
    while page < pages:
        r = get("search", tags=f"comment,story_{thread_id}", hitsPerPage=100, page=page)
        pages = r["nbPages"]
        out += [h for h in r["hits"] if str(h["parent_id"]) == str(thread_id)]
        print(f"  page {page + 1}/{pages}, {len(out)} kept")
        page += 1
        time.sleep(0.3)
    return out


def main():
    if len(sys.argv) > 1:
        thread_id, title, created = sys.argv[1], None, None
    else:
        thread_id, title, created = latest_thread()
        print(f"{title} ({created})")

    RAW.mkdir(parents=True, exist_ok=True)
    dest = RAW / f"{thread_id}.json"
    if dest.exists():
        print(f"already have {dest.relative_to(RAW.parent.parent)}, not refetching")
        return

    hits = comments(thread_id)
    dest.write_text(
        json.dumps(
            {"thread_id": thread_id, "title": title, "created_at": created, "comments": hits},
            indent=2,
        )
    )
    print(f"{len(hits)} postings -> {dest.relative_to(RAW.parent.parent)}")


if __name__ == "__main__":
    main()
