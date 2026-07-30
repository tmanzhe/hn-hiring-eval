"""Step 02. Fetch Who-is-hiring threads from Algolia and write the raw JSON to disk.

    uv run ingest/fetch.py                # newest thread only
    uv run ingest/fetch.py --months 12    # the last 12 monthly threads
    uv run ingest/fetch.py --thread 48747976

Raw in, nothing parsed. Parsing happens in rules.py and the LLM fallback, both of which run
offline against these files. I rewrite the parser many times; I don't want to re-hit the API
many times, and I don't want a different snapshot landing mid-project and invalidating labels
I already made.
"""

import argparse
import json
import re
import time
from datetime import date
from pathlib import Path

import httpx

API = "https://hn.algolia.com/api/v1"
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

# "Ask HN: Who is hiring? (July 2026)"
TITLE = re.compile(r"who is hiring", re.IGNORECASE)
MONTH_YEAR = re.compile(r"\(([A-Za-z]+)\s+(\d{4})\)")
MONTHS = {
    m: i
    for i, m in enumerate(
        [
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december",
        ],
        1,
    )
}


def client():
    return httpx.Client(
        base_url=API,
        timeout=httpx.Timeout(30.0, connect=10.0),
        transport=httpx.HTTPTransport(retries=3),
        headers={"user-agent": "hn-hiring-eval (github.com/tmanzhe/hn-hiring-eval)"},
    )


def thread_date(title):
    """Month the thread was posted for. Step 09 partitions on this, and it's what separates
    'currently hiring' from the historical trends set. Conflating those two is a correctness
    bug, not a UI detail."""
    m = MONTH_YEAR.search(title or "")
    if not m or m[1].lower() not in MONTHS:
        return None
    return date(int(m[2]), MONTHS[m[1].lower()], 1).isoformat()


def hiring_threads(c, limit):
    """whoishiring also posts freelancer and who-wants-to-be-hired threads. Filter on title."""
    r = c.get(
        "/search_by_date",
        params={"tags": "story,author_whoishiring", "hitsPerPage": limit * 3},
    )
    r.raise_for_status()
    out = [h for h in r.json()["hits"] if TITLE.search(h["title"] or "")]
    return out[:limit]


def comments(c, thread_id):
    """Top-level comments only. Replies are people asking about visa sponsorship."""
    out, page, pages = [], 0, 1
    while page < pages:
        r = c.get(
            "/search",
            params={"tags": f"comment,story_{thread_id}", "hitsPerPage": 100, "page": page},
        )
        r.raise_for_status()
        body = r.json()
        pages = body["nbPages"]
        out += [h for h in body["hits"] if str(h["parent_id"]) == str(thread_id)]
        page += 1
        time.sleep(0.3)
    return out


def save(c, thread_id, title=None, created=None):
    dest = RAW / f"{thread_id}.json"
    if dest.exists():
        print(f"  have {thread_id} already, skipping")
        return 0

    hits = comments(c, thread_id)
    dest.write_text(
        json.dumps(
            {
                "thread_id": str(thread_id),
                "title": title,
                "created_at": created,
                "thread_date": thread_date(title),
                "comments": hits,
            },
            indent=2,
        )
    )
    print(f"  {thread_id}  {title or '-'}  {len(hits)} postings")
    return len(hits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=1, help="how many recent threads to pull")
    ap.add_argument("--thread", help="a specific thread id, skips the search")
    args = ap.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    total = 0
    with client() as c:
        if args.thread:
            total += save(c, args.thread)
        else:
            threads = hiring_threads(c, args.months)
            if not threads:
                raise SystemExit("no hiring threads found in whoishiring's recent stories")
            for h in threads:
                total += save(c, h["objectID"], h["title"], h["created_at"])

    print(f"\n{total} new postings in data/raw/")


if __name__ == "__main__":
    main()
