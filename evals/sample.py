"""Step 10. Draw a stratified sample of posts to label.

    uv run evals/sample.py                 # 60 posts, seeded, reproducible
    uv run evals/sample.py -n 20 --report  # show the strata, write nothing

Not the first 60. A sample of whatever sits at the top of the current thread is a sample of
whatever people posted on the 1st, and it would systematically under-represent the shapes that
are rare and hard — which are exactly the ones worth measuring.

**The sampling rule lives in code, not in my head.** Seeded and deterministic, so the set can be
regenerated and anyone can check what went into it.

## Strata

Computed from the post text, not from the hand tally in docs/formats.md. That's a deliberate
narrowing: `format`, `salary` and `length` are mechanical properties I can derive for all 1,995
posts today, so the sample doesn't block on reading 30 posts by hand.

What the hand tally adds that this can't: agency spam, equity-only compensation, and genuinely
ambiguous posts. Those are judgment calls. If step 03 turns up a bucket that matters and isn't
represented here, this file is where it gets added — and the sample has to be redrawn before
labeling, not after.

Deliberately **not** a stratum: multi-role. Measured at 1.8% of the corpus, so 60 posts contains
about one, and one post cannot support a slice-level claim.
"""

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest.corpus import posts, to_text
from ingest.rules import find_salary

OUT = Path(__file__).resolve().parent / "sample.json"
SEED = 20260801  # recorded so the draw is reproducible


def strata(text: str) -> tuple[str, str, str]:
    """(format, salary, length) for one post. Mechanical — no judgment involved."""
    first = next((line for line in text.splitlines() if line.strip()), "")
    fmt = "pipe" if first.count("|") >= 2 else "prose"
    salary = "has_salary" if find_salary(text)[0] is not None else "no_salary"
    length = "long" if len(text) > 1200 else "short"
    return fmt, salary, length


def draw(n: int, seed: int = SEED, oversample: dict[str, int] | None = None):
    """Proportional allocation with a floor.

    Pure proportional allocation would give a rare stratum zero or one post, which cannot
    support a claim about it. Every non-empty stratum gets at least `floor` posts, taken from
    the largest strata — trading a little representativeness for the ability to say anything
    about the small groups. That trade is the whole point of stratifying.
    """
    all_posts = posts()
    grouped: dict[tuple, list] = {}
    for c in all_posts:
        key = strata(to_text(c.get("comment_text")))
        grouped.setdefault(key, []).append(c)

    total = len(all_posts)
    floor = max(2, n // (len(grouped) * 3))

    allocation = {k: max(floor, round(n * len(v) / total)) for k, v in grouped.items()}
    allocation = {k: min(v, len(grouped[k])) for k, v in allocation.items()}

    # Oversampling: guarantee a slice enough rows to say something about it. The cost is that
    # the sample stops being proportional to the corpus, so the OVERALL number becomes a
    # weighted estimate rather than a plain mean — see the note printed by --report.
    for value, target in (oversample or {}).items():
        cells = [k for k in grouped if value in k]
        if not cells:
            continue
        have = sum(allocation[k] for k in cells)
        deficit = target - have
        while deficit > 0:
            # Grow the largest cell that still has spare posts, so the boost lands where the
            # corpus actually has material rather than exhausting a rare cell.
            cell = max(
                (k for k in cells if allocation[k] < len(grouped[k])),
                key=lambda k: len(grouped[k]),
                default=None,
            )
            if cell is None:
                break
            allocation[cell] += 1
            deficit -= 1

    # Reconcile to exactly n by adjusting the largest strata, never below the floor.
    protected = {k for v in (oversample or {}) for k in grouped if v in k}
    order = sorted(grouped, key=lambda k: -len(grouped[k]))
    while sum(allocation.values()) != n:
        delta = 1 if sum(allocation.values()) < n else -1
        moved = False
        for key in order if delta > 0 else reversed(order):
            if delta < 0 and key in protected:
                continue  # never shrink a slice that was deliberately boosted
            nxt = allocation[key] + delta
            if floor <= nxt <= len(grouped[key]):
                allocation[key] = nxt
                moved = True
                break
        if not moved:
            break  # cannot hit n exactly with these strata; report what we got

    rng = random.Random(seed)
    chosen = []
    for key in sorted(grouped, key=str):
        chosen += rng.sample(grouped[key], allocation[key])
    rng.shuffle(chosen)  # so labeling order doesn't track stratum
    return chosen, allocation, grouped


def split(chosen: list, dev_frac: float = 2 / 3, seed: int = SEED):
    """40 dev / 20 held-out at n=60.

    I iterate against dev and will overfit to it. Held-out gets touched exactly twice: once at
    baseline, once at the end. If dev improves and held-out doesn't, I tuned to noise — and
    knowing that is the entire reason for the split.
    """
    rng = random.Random(seed + 1)
    order = list(chosen)
    rng.shuffle(order)
    cut = round(len(order) * dev_frac)
    return {c["objectID"]: ("dev" if i < cut else "held-out") for i, c in enumerate(order)}


def slice_power(chosen: list) -> list[tuple[str, str, int, float]]:
    """What each reportable slice will actually support, before any labeling happens.

    A slice with 8 posts carries a ±30-point interval, which cannot distinguish 60% from 90%.
    Better to find that out now than after six hours of labeling — the fix (oversample, or drop
    the slice) is free before and expensive after.
    """
    from evals.scorers import margin

    dims = {"format": 0, "salary": 1, "length": 2}
    out = []
    for dim, idx in dims.items():
        counts = Counter(strata(to_text(c.get("comment_text")))[idx] for c in chosen)
        for value, n in sorted(counts.items()):
            # Margin at an assumed 80% — the regime these metrics actually live in.
            out.append((dim, value, n, margin(round(n * 0.8), n)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-n", type=int, default=60)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--report", action="store_true", help="show strata, write nothing")
    ap.add_argument(
        "--oversample",
        action="append",
        default=[],
        metavar="VALUE=N",
        help="guarantee a slice N posts, e.g. --oversample prose=20",
    )
    args = ap.parse_args()

    over = {}
    for spec in args.oversample:
        value, _, target = spec.partition("=")
        if not target.isdigit():
            raise SystemExit(f"--oversample wants VALUE=N, got {spec!r}")
        over[value] = int(target)

    chosen, allocation, grouped = draw(args.n, args.seed, over)
    splits = split(chosen, seed=args.seed)

    total = sum(len(v) for v in grouped.values())
    print(f"corpus {total} posts, {len(grouped)} strata, drawing {len(chosen)}\n")
    print(f"{'stratum':<34}{'corpus':>8}{'share':>8}{'drawn':>7}")
    print("-" * 57)
    for key in sorted(grouped, key=str):
        label = " / ".join(key)
        share = len(grouped[key]) / total
        print(f"{label:<34}{len(grouped[key]):>8}{share:>7.1%}{allocation[key]:>7}")

    counts = Counter(splits.values())
    print(f"\nsplit: {counts['dev']} dev / {counts['held-out']} held-out")

    print(f"\n{'slice':<24}{'n':>5}{'± at 80%':>11}   claim it can support")
    print("-" * 72)
    for dim, value, n, m in slice_power(chosen):
        if m <= 0.15:
            verdict = "usable"
        elif m <= 0.25:
            verdict = "weak — only large gaps"
        else:
            verdict = "TOO SMALL — do not report this slice"
        print(f"{dim + ': ' + value:<24}{n:>5}{m:>10.0%}   {verdict}")
    if over:
        print(
            f"\nOversampled {', '.join(f'{k}->{v}' for k, v in over.items())}. The sample is no "
            "longer proportional to the corpus, so the OVERALL number is a weighted estimate, "
            "not a plain mean. Per-slice numbers are unaffected."
        )
    else:
        print("\nDecide this before labeling, not after. Oversampling a thin slice is free now.")

    if args.report:
        print("\nreport only, nothing written")
        return

    OUT.write_text(
        json.dumps(
            {
                "seed": args.seed,
                "n": len(chosen),
                "rule": "proportional allocation with a per-stratum floor; strata are "
                        "(format, salary, length) computed from post text",
                "strata": {" / ".join(k): allocation[k] for k in sorted(grouped, key=str)},
                "posts": [
                    {
                        "comment_id": c["objectID"],
                        "split": splits[c["objectID"]],
                        "stratum": " / ".join(strata(to_text(c.get("comment_text")))),
                    }
                    for c in chosen
                ],
            },
            indent=2,
        )
    )
    print(f"\nwrote {OUT.relative_to(OUT.parent.parent)}")
    print("next: uv run evals/label.py")


if __name__ == "__main__":
    main()
