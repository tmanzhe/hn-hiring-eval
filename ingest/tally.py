"""Step 03. Read posts one at a time and record which format buckets each one falls into.

    uv run ingest/tally.py              # start, or resume where I left off
    uv run ingest/tally.py --report     # rewrite the counts table, don't read anything
    uv run ingest/tally.py --reset      # throw the tally away and start over

I still make every call. This just stops me keeping tally on paper and re-finding posts later.

Two outputs:
  docs/format_tally.json   id -> buckets. Feeds step 10's stratified sample directly.
  docs/formats.md          the counts table, regenerated from the tally.

Quit any time with q. Progress saves after every post.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ingest.corpus import latest, to_text

DOCS = Path(__file__).resolve().parent.parent / "docs"
TALLY = DOCS / "format_tally.json"
FORMATS = DOCS / "formats.md"

# The buckets from the plan. Add rows here as I find shapes nobody predicted — that's the whole
# reason for reading rather than regexing.
BUCKETS = {
    "p": "pipe-delimited header line",
    "r": "prose paragraphs",
    "b": "bulleted requirements",
    "m": "multi-role post",
    "n": "no salary stated",
    "f": "non-USD salary",
    "e": "equity only / \"competitive\"",
    "a": "agency or recruiter spam",
    "?": "genuinely ambiguous",
}

MENU = "  ".join(f"[{k}] {v}" for k, v in BUCKETS.items())


def load():
    return json.loads(TALLY.read_text()) if TALLY.exists() else {}


def save(tally):
    DOCS.mkdir(exist_ok=True)
    TALLY.write_text(json.dumps(tally, indent=2, sort_keys=True))


def report(tally):
    """Regenerate the counts table in formats.md between the markers, leaving my prose alone."""
    n = len(tally)
    counts = {k: 0 for k in BUCKETS}
    for buckets in tally.values():
        for k in buckets:
            if k in counts:
                counts[k] += 1

    rows = [f"| Shape | Count / {n or 30} | Notes |", "| --- | --- | --- |"]
    for k, label in BUCKETS.items():
        c = counts[k]
        pct = f" ({c / n:.0%})" if n else ""
        rows.append(f"| {label} | {c or ''}{pct if c else ''} |  |")
    table = "\n".join(rows)

    body = FORMATS.read_text() if FORMATS.exists() else ""
    start, end = "<!-- tally:start -->", "<!-- tally:end -->"
    block = f"{start}\n{table}\n{end}"
    if start in body and end in body:
        head, rest = body.split(start, 1)
        body = head + block + rest.split(end, 1)[1]
    else:
        body = body.rstrip() + "\n\n" + block + "\n"
    FORMATS.write_text(body)
    print(f"\n{n} posts tallied. counts written to docs/formats.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true", help="rewrite counts, read nothing")
    ap.add_argument("--reset", action="store_true", help="discard the tally")
    ap.add_argument("-n", type=int, default=30, help="how many posts to work through")
    args = ap.parse_args()

    if args.reset:
        TALLY.unlink(missing_ok=True)
        print("tally cleared")
        return

    tally = load()
    if args.report:
        report(tally)
        return

    posts = latest()["comments"][: args.n]
    todo = [c for c in posts if c["objectID"] not in tally]
    if not todo:
        print(f"all {len(posts)} already tallied. --report to rewrite counts, --reset to redo.")
        report(tally)
        return

    print(f"{len(tally)} done, {len(todo)} to go. Type the letters that apply, then Enter.")
    print("Multiple is fine (e.g. 'pn' = pipe header, no salary). Blank = skip. q = quit.\n")

    for i, c in enumerate(todo, 1):
        body = to_text(c.get("comment_text"))
        print("=" * 78)
        print(f"({i}/{len(todo)})  id={c['objectID']}  {len(body)} chars")
        print("=" * 78)
        print(body)
        print("-" * 78)
        print(MENU)

        try:
            raw = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nstopping.")
            break

        if raw == "q":
            print("stopping.")
            break
        if not raw:
            print("skipped\n")
            continue

        picked = [ch for ch in raw if ch in BUCKETS]
        unknown = [ch for ch in raw if ch not in BUCKETS]
        if unknown:
            print(f"ignored unknown: {''.join(unknown)}")
        if not picked:
            print("nothing recognised, skipped\n")
            continue

        tally[c["objectID"]] = picked
        save(tally)
        print(f"saved: {', '.join(BUCKETS[k] for k in picked)}\n")

    report(tally)
    print("\nnow write the interesting cases into docs/formats.md by hand — the counts are only")
    print("half of it. The examples are what step 19's few-shots and step 10's hard cases come from.")


if __name__ == "__main__":
    main()
