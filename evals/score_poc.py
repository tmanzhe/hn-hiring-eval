"""P5. Score the crude rules against my ten hand labels. One honest number per field.

    python3 evals/score_poc.py

n=10, so none of these numbers mean anything on their own. The point is that the loop exists
and runs end to end. This file grows into the real scorers at step 14.

Order matters: label first (P4), then run this. Reading the rules output before labeling is how
I'd talk myself into agreeing with the regex.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ingest.corpus import by_id, to_text  # noqa: E402
from ingest.rules_poc import find_salary, find_skills  # noqa: E402

LABELS = Path(__file__).resolve().parent / "poc_labels.jsonl"

# applied to labels AND predictions, identically. do it one-sided and the F1 measures this dict
# instead of the extractor. the real version of this is step 08.
SYNONYMS = {"k8s": "kubernetes", "postgres": "postgresql", "js": "javascript"}


def norm(skills):
    return {SYNONYMS.get(s.lower().strip(), s.lower().strip()) for s in skills}


def main():
    labels = [json.loads(l) for l in LABELS.read_text().splitlines() if l.strip()]
    done = [r for r in labels if r.get("done")]
    if not done:
        raise SystemExit(
            f"0 of {len(labels)} rows labeled. that's P4.\n"
            "  uv run ingest/dump.py --ids "
            + ",".join(r["comment_id"] for r in labels)
            + "\nthen fill in evals/poc_labels.jsonl and set done to true."
        )
    if len(done) < len(labels):
        print(f"scoring {len(done)} of {len(labels)} labeled rows\n")

    posts = {c["objectID"]: c for c in by_id([r["comment_id"] for r in done])}

    # the four outcomes for a field that's allowed to be absent
    right = abstained = missed = hallucinated = wrong = 0
    f1s = []

    for row in done:
        text = to_text(posts[row["comment_id"]].get("comment_text"))
        p_lo, p_hi, _ = find_salary(text)
        t_lo = row["salary_min"]

        if t_lo is None and p_lo is None:
            abstained += 1
        elif t_lo is None and p_lo is not None:
            hallucinated += 1
            print(f"  hallucinated  {row['comment_id']}  invented {p_lo}-{p_hi}")
        elif t_lo is not None and p_lo is None:
            missed += 1
            print(f"  missed        {row['comment_id']}  should be {t_lo}-{row['salary_max']}")
        elif (p_lo, p_hi) == (t_lo, row["salary_max"]):
            right += 1
        else:
            wrong += 1
            print(
                f"  wrong         {row['comment_id']}  got {p_lo}-{p_hi}, "
                f"want {t_lo}-{row['salary_max']}"
            )

        pred, true = norm(find_skills(text)), norm(row["skills"])
        if not pred and not true:
            f1s.append(1.0)
        else:
            tp = len(pred & true)
            prec = tp / len(pred) if pred else 0.0
            rec = tp / len(true) if true else 0.0
            f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)

    n = len(done)
    attempts = right + wrong + hallucinated
    print(f"\nsalary, n={n}")
    print(f"  coverage              {attempts / n:.0%}  ({attempts} attempts)")
    if attempts:
        print(f"  precision on attempts {right / attempts:.0%}")
    print(f"  abstained correctly   {abstained}")
    print(f"  missed                {missed}")
    print(f"  hallucinated          {hallucinated}   <- the only one I can't fix downstream")
    print(f"  wrong value           {wrong}")
    print(f"\nskills, n={n}")
    print(f"  macro F1              {sum(f1s) / n:.2f}")
    print("  ceiling is the 20-word list in rules_poc.py, not the regex")


if __name__ == "__main__":
    main()
