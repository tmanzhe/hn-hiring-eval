"""Reading what's in data/raw/.

Everything that touches the corpus goes through here. The POC scripts used to pick the newest
file by mtime, which was fine with one thread on disk and quietly wrong with six — a re-fetch
reorders mtimes and the ten POC ids start getting looked up in the wrong thread.
"""

import html
import json
import re
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def to_text(s):
    """Algolia hands back HTML. Strip it, unescape entities, keep paragraph breaks."""
    s = re.sub(r"<p>", "\n\n", s or "")
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def threads():
    """Every thread on disk, oldest first. Ordered by thread_date, not mtime."""
    out = []
    for p in RAW.glob("*.json"):
        d = json.loads(p.read_text())
        out.append(d)
    if not out:
        raise SystemExit("data/raw is empty. run: uv run ingest/fetch.py --months 6")
    return sorted(out, key=lambda d: d.get("thread_date") or "")


def latest():
    """The current hiring thread. 'Currently hiring' means this one only."""
    return threads()[-1]


def posts(thread_date=None):
    """All postings across every thread, each tagged with its thread_date.

    Postings carry no date of their own, and the trends page needs one per row.
    """
    out = []
    for t in threads():
        if thread_date and t.get("thread_date") != thread_date:
            continue
        for c in t["comments"]:
            out.append({**c, "thread_date": t.get("thread_date")})
    return out


def by_id(ids):
    """Look ids up across the whole corpus, in the order given. Raises on a miss rather than
    silently scoring nine posts and calling it ten."""
    index = {c["objectID"]: c for c in posts()}
    missing = [i for i in ids if i not in index]
    if missing:
        raise SystemExit(f"not in data/raw: {', '.join(missing)}")
    return [index[i] for i in ids]
