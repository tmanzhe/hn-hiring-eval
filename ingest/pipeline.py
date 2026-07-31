"""Steps 06 and 09. Run the rules path over the whole corpus, report coverage, write Parquet.

    uv run ingest/pipeline.py              # parse everything, write Parquet
    uv run ingest/pipeline.py --coverage   # just the numbers, write nothing

Coverage is not accuracy. This says how often rules produce an answer, not how often the answer
is right — that needs labels, and it's step 14. But coverage is the number every later cost
claim is measured against, and it establishes that the free option was tried first.

The LLM fallback (step 07) is not built yet, so every row here is extracted_by="rules". The
ids that rules could not handle are written to data/needs_llm.json for step 07 to pick up.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from ingest.corpus import RAW, posts, to_text
from ingest.normalize import display_skills, normalize
from ingest.rules import is_confident, parse
from ingest.schema import Posting

OUT = RAW.parent / "postings.parquet"
NEEDS_LLM = RAW.parent / "needs_llm.json"


def run():
    rows, needs_llm, conf_counts = [], [], Counter()

    for c in posts():
        text = to_text(c.get("comment_text"))
        extraction, confidence = parse(text)
        extraction = normalize(extraction)

        for field, ok in confidence.items():
            conf_counts[field] += ok

        if not is_confident(confidence):
            needs_llm.append(c["objectID"])

        rows.append(
            Posting(
                **extraction.model_dump(),
                comment_id=int(c["objectID"]),
                thread_date=c["thread_date"],
                extracted_by="rules",
            )
        )
    return rows, needs_llm, conf_counts


def report(rows, needs_llm, conf_counts):
    n = len(rows)
    handled = n - len(needs_llm)
    print(f"corpus: {n} postings across {len({r.thread_date for r in rows})} threads\n")

    print("per-field coverage (rules produced a value):")
    for field, hits in sorted(conf_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {field:<12} {hits / n:>6.1%}  ({hits})")

    print(f"\nfully handled by rules   {handled / n:>6.1%}  ({handled})")
    print(f"would go to the model    {len(needs_llm) / n:>6.1%}  ({len(needs_llm)})")
    print("\ncoverage, not accuracy. whether these values are RIGHT needs labels — step 14.")

    periods = Counter(r.salary_period for r in rows if r.salary_period)
    if periods:
        print(f"\nsalary periods found: {dict(periods)}")
        print("  (all converted to annual in the salary columns; period kept for provenance)")


def write_parquet(rows):
    table = pa.Table.from_pylist(
        [
            {
                **r.model_dump(),
                "thread_date": r.thread_date,
                "skills": display_skills(r.skills),
                "thread_month": r.thread_date.strftime("%Y-%m"),
            }
            for r in rows
        ]
    )
    pq.write_table(table, OUT, compression="snappy")
    size = OUT.stat().st_size / 1024
    print(f"\nwrote {OUT.relative_to(OUT.parent.parent)}  {len(rows)} rows  {size:.0f} KB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coverage", action="store_true", help="report only, write nothing")
    args = ap.parse_args()

    rows, needs_llm, conf_counts = run()
    report(rows, needs_llm, conf_counts)

    if args.coverage:
        return

    write_parquet(rows)
    Path(NEEDS_LLM).write_text(json.dumps(sorted(needs_llm), indent=2))
    print(f"wrote data/needs_llm.json  {len(needs_llm)} ids for step 07")


if __name__ == "__main__":
    main()
