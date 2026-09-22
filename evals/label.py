"""Step 12. Hand-label the sampled posts, one field at a time.

    uv run evals/label.py              # start, or resume exactly where I stopped
    uv run evals/label.py --progress   # how far in, per stratum
    uv run evals/label.py --review     # re-open posts I flagged as uncertain
    uv run evals/label.py --verify     # check drafts.jsonl against each post, field by field

Writes `evals/labeled.jsonl` — one JSON object per post, matching the schema. Saves after every
post, so quitting mid-way loses nothing.

## The one rule this tool enforces

**It never shows me what the extractor produced.** The moment I see the regex output I'm no
longer writing ground truth, I'm agreeing with a machine — and a labeled set contaminated that
way scores its own extractor generously and nobody can tell from the outside.

That's why the blank-slate mode has no "accept suggestion" key. `--verify` does keep a value on
Enter, but what it shows is a draft written from the post text alone (see ANNOTATION.md), never
parser or model output, and every row it saves records who drafted it.

## Uncertainty is data

`?` flags a post as genuinely ambiguous rather than forcing a call. "11% of posts are ambiguous
on salary" is a real result about the ceiling on *any* extractor, mine included — it belongs in
the write-up, not buried in a coin-flip.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest.corpus import by_id, to_text

HERE = Path(__file__).resolve().parent
SAMPLE = HERE / "sample.json"
LABELS = HERE / "labeled.jsonl"
DRAFTS = HERE / "drafts.jsonl"

REMOTE = {"r": "remote", "h": "hybrid", "o": "onsite"}
SENIORITY = {"j": "junior", "m": "mid", "s": "senior", "t": "staff+"}
PERIOD = {"y": "year", "m": "month", "h": "hour"}


def load_done() -> dict:
    if not LABELS.exists():
        return {}
    return {
        r["comment_id"]: r
        for r in (json.loads(x) for x in LABELS.read_text().splitlines() if x.strip())
    }


def save(rows: dict) -> None:
    LABELS.write_text(
        "\n".join(json.dumps(rows[k]) for k in sorted(rows, key=int)) + "\n"
    )


def ask(prompt: str, *, allow=None, cast=None, optional=True):
    """Blank means 'the post does not state this' — which is a real answer, not a skip.

    Returns (value, quit, uncertain).
    """
    hint = f" [{'/'.join(allow)}]" if allow else ""
    while True:
        raw = input(f"  {prompt}{hint}: ").strip()
        if raw.lower() == "q":
            return None, True, False
        if raw == "?":
            return None, False, True
        if not raw:
            return None, False, False
        if allow:
            if raw.lower() in allow:
                return allow[raw.lower()], False, False
            print(f"    one of {'/'.join(allow)}, blank if not stated, ? if unclear")
            continue
        if cast:
            try:
                return cast(raw), False, False
            except ValueError:
                print("    couldn't read that as a number")
                continue
        return raw, False, False


def label_one(post: dict, meta: dict) -> dict | None:
    """Walk one post field by field. Returns None if the user quit."""
    text = to_text(post.get("comment_text"))
    print("\n" + "=" * 78)
    print(f"id={post['objectID']}   {meta['stratum']}   [{meta['split']}]")
    print("=" * 78)
    print(text)
    print("-" * 78)
    print("  blank = not stated in the post   ? = genuinely ambiguous   q = save and quit")

    row = {"comment_id": post["objectID"], "split": meta["split"],
           "stratum": meta["stratum"], "done": True, "uncertain": []}

    def field(name, prompt, **kw):
        value, quit_now, unsure = ask(prompt, **kw)
        if quit_now:
            return True
        if unsure:
            row["uncertain"].append(name)
        row[name] = value
        return False

    if field("company", "company"):
        return None
    if field("location", "location"):
        return None
    if field("remote", "remote", allow=REMOTE):
        return None
    if field("salary_min", "salary min (number only)", cast=int):
        return None
    if field("salary_max", "salary max", cast=int):
        return None
    if row.get("salary_min") is not None or row.get("salary_max") is not None:
        if field("salary_currency", "currency (USD/EUR/GBP)"):
            return None
        if field("salary_period", "period", allow=PERIOD):
            return None
    else:
        row["salary_currency"] = None
        row["salary_period"] = None
    if field("seniority", "seniority", allow=SENIORITY):
        return None

    skills, quit_now, unsure = ask("skills (comma separated)")
    if quit_now:
        return None
    if unsure:
        row["uncertain"].append("skills")
    row["skills"] = [s.strip() for s in (skills or "").split(",") if s.strip()]

    return row


FIELDS = [
    ("company", {}), ("location", {}), ("remote", {"allow": REMOTE}),
    ("salary_min", {"cast": int}), ("salary_max", {"cast": int}),
    ("salary_currency", {}), ("salary_period", {"allow": PERIOD}),
    ("seniority", {"allow": SENIORITY}), ("skills", {}),
]


def verify_one(post: dict, draft: dict) -> dict | None:
    """Check a drafted row against the post. Enter keeps the draft, anything typed replaces it,
    `-` clears it to null, `?` flags it. Returns None if the user quit."""
    text = to_text(post.get("comment_text"))
    print("\n" + "=" * 78)
    print(f"id={draft['comment_id']}   {draft['stratum']}   [{draft['split']}]")
    print("=" * 78)
    print(text)
    print("-" * 78)
    if draft.get("note"):
        print(f"  note: {draft['note']}")
    if draft.get("uncertain"):
        print(f"  drafter flagged: {', '.join(draft['uncertain'])}")
    print("  enter = keep   type = replace   - = null   ? = ambiguous   q = save and quit")

    row = {k: draft[k] for k in ("comment_id", "split", "stratum")}
    row.update(done=True, uncertain=[], drafted_by=draft.get("drafted_by"), verified=True)
    for name, kw in FIELDS:
        shown = ", ".join(draft[name]) if name == "skills" else draft[name]
        hint = f" [{'/'.join(kw['allow'])}]" if "allow" in kw else ""
        while True:
            raw = input(f"  {name}{hint} = {shown!r}: ").strip()
            if raw.lower() == "q":
                return None
            if raw == "":
                row[name] = draft[name]
            elif raw == "-":
                row[name] = [] if name == "skills" else None
            elif raw == "?":
                row["uncertain"].append(name)
                row[name] = draft[name]
            elif name == "skills":
                row[name] = [s.strip() for s in raw.split(",") if s.strip()]
            elif "allow" in kw:
                if raw.lower() not in kw["allow"]:
                    print(f"    one of {'/'.join(kw['allow'])}")
                    continue
                row[name] = kw["allow"][raw.lower()]
            elif "cast" in kw:
                try:
                    row[name] = kw["cast"](raw)
                except ValueError:
                    print("    couldn't read that as a number")
                    continue
            else:
                row[name] = raw
            break
    if draft.get("note"):
        row["note"] = draft["note"]
    return row


def verify(sample: dict, done: dict) -> None:
    drafts = {
        r["comment_id"]: r
        for r in (json.loads(x) for x in DRAFTS.read_text().splitlines() if x.strip())
    }
    todo = [p for p in sample["posts"] if p["comment_id"] not in done and p["comment_id"] in drafts]
    if not todo:
        print("nothing left to verify")
        return
    print(f"{len(done)} done, {len(todo)} drafts to check.")
    posts = {c["objectID"]: c for c in by_id([p["comment_id"] for p in todo])}
    for meta in todo:
        try:
            row = verify_one(posts[meta["comment_id"]], drafts[meta["comment_id"]])
        except (EOFError, KeyboardInterrupt):
            print("\nstopping.")
            break
        if row is None:
            print("saved, stopping.")
            break
        done[row["comment_id"]] = row
        save(done)
        print(f"  saved ({len(done)}/{len(sample['posts'])})")
    progress(sample, done)


def progress(sample: dict, done: dict) -> None:
    by_stratum = Counter()
    done_by_stratum = Counter()
    for p in sample["posts"]:
        by_stratum[p["stratum"]] += 1
        if p["comment_id"] in done:
            done_by_stratum[p["stratum"]] += 1

    print(f"{len(done)}/{len(sample['posts'])} labeled\n")
    print(f"{'stratum':<36}{'done':>6}{'of':>5}")
    print("-" * 48)
    for stratum in sorted(by_stratum):
        print(f"{stratum:<36}{done_by_stratum[stratum]:>6}{by_stratum[stratum]:>5}")

    flagged = [r for r in done.values() if r.get("uncertain")]
    if flagged:
        fields = Counter(f for r in flagged for f in r["uncertain"])
        print(f"\n{len(flagged)} posts flagged uncertain: {dict(fields)}")
        print("That count is a finding — it bounds what any extractor can score on this set.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--progress", action="store_true")
    ap.add_argument("--review", action="store_true", help="re-open posts flagged uncertain")
    ap.add_argument("--verify", action="store_true", help="check drafts.jsonl field by field")
    args = ap.parse_args()

    if not SAMPLE.exists():
        raise SystemExit("no sample yet. run: uv run evals/sample.py -n 80 --oversample prose=20")

    sample = json.loads(SAMPLE.read_text())
    done = load_done()

    if args.progress:
        progress(sample, done)
        return

    if args.verify:
        verify(sample, done)
        return

    if args.review:
        todo = [p for p in sample["posts"]
                if p["comment_id"] in done and done[p["comment_id"]].get("uncertain")]
        if not todo:
            print("nothing flagged uncertain")
            return
    else:
        todo = [p for p in sample["posts"] if p["comment_id"] not in done]

    if not todo:
        print(f"all {len(sample['posts'])} labeled.")
        progress(sample, done)
        print("\nnext: uv run evals/run.py --config rules --split dev")
        return

    print(f"{len(done)} done, {len(todo)} to go.")
    print("Read the post, then answer each field. Nothing here shows you what the parser said —")
    print("that's deliberate. Ctrl-C or q saves and exits.\n")

    posts = {c["objectID"]: c for c in by_id([p["comment_id"] for p in todo])}
    for meta in todo:
        try:
            row = label_one(posts[meta["comment_id"]], meta)
        except (EOFError, KeyboardInterrupt):
            print("\nstopping.")
            break
        if row is None:
            print("saved, stopping.")
            break
        done[row["comment_id"]] = row
        save(done)
        print(f"  saved ({len(done)}/{len(sample['posts'])})")

    save(done)
    print()
    progress(sample, done)


if __name__ == "__main__":
    main()
