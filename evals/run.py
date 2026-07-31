"""Step 15 and 16. Run a config over a split, score every field, append one row to runs.jsonl.

    uv run evals/run.py --config rules --split dev
    uv run evals/run.py --config agent:C --split dev
    uv run evals/run.py --report                      # print the frontier table

Rows, not files. One JSON object per run means runs can be diffed, plotted over time, and
compared side by side — which is what turns "I changed the prompt and it felt better" into
evidence.

Two things every row carries so a number can always be attributed:

  prompt_sha   prompt changes are code changes. A metric that can't be traced to a specific
               prompt is not evidence.
  model        pinned, never an alias. An alias silently changes under you and every historical
               row becomes uncomparable.

The rules config needs no API key, so a real baseline row is available the moment labels exist.
"""

import argparse
import hashlib
import json
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evals.scorers import (
    location_matches,
    salary_matches,
    score_enum_field,
    score_nullable_field,
    score_set_field,
)
from ingest.corpus import by_id, to_text
from ingest.normalize import normalize
from ingest.rules import parse

LABELS = Path(__file__).resolve().parent / "labeled.jsonl"
POC_LABELS = Path(__file__).resolve().parent / "poc_labels.jsonl"
RUNS = Path(__file__).resolve().parent / "runs.jsonl"


def load_labels(split: str | None):
    """labeled.jsonl if it exists, otherwise the POC ten, so the harness is runnable earlier."""
    path = LABELS if LABELS.exists() else POC_LABELS
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    rows = [r for r in rows if r.get("done")]
    if split:
        rows = [r for r in rows if r.get("split", "dev") == split]
    if not rows:
        raise SystemExit(
            f"no labeled rows in {path.name}. Label them and set done:true — that's P4/step 12."
        )
    return rows, path.name


def predict_rules(text):
    """The free baseline. No model, no key, no network."""
    extraction, _ = parse(text)
    return normalize(extraction)


def predict_agent(text, variant):
    from agent.extract_agent import extract

    return extract(text, variant).extraction


def get_predictor(config: str):
    if config == "rules":
        return predict_rules, "n/a", "rules"
    if config.startswith("agent:"):
        variant = config.split(":", 1)[1].upper()
        import os

        from agent.extract_agent import SYSTEM

        return (
            lambda t: predict_agent(t, variant),
            os.environ.get("STRONG_MODEL", "claude-opus-5"),
            SYSTEM,
        )
    raise SystemExit(f"unknown config {config!r}. try: rules, agent:A .. agent:E")


def slice_of(text: str) -> str:
    """Which bucket this post belongs to. Aggregates hide everything — '84% overall, 61% on
    prose, 94% on pipe-delimited' is what tells you where a model earns its cost."""
    first = next((line for line in text.splitlines() if line.strip()), "")
    if first.count("|") >= 2:
        return "pipe"
    if len(text) > 1200:
        return "long_prose"
    return "prose"


def score_rows(pairs):
    """pairs: list of (Extraction, label dict). Returns the scores block."""
    return {
        "company": score_nullable_field(
            "company", [(p.company, t.get("company")) for p, t in pairs]
        ).to_dict(),
        "salary": score_nullable_field(
            "salary",
            [
                (
                    None if p.salary_min is None else (p.salary_min, p.salary_max),
                    None if t.get("salary_min") is None else (t["salary_min"], t.get("salary_max")),
                )
                for p, t in pairs
            ],
            compare=salary_matches,
        ).to_dict(),
        "location": score_nullable_field(
            "location",
            [(p.location, t.get("location")) for p, t in pairs],
            compare=location_matches,
        ).to_dict(),
        "skills": score_set_field(
            "skills", [(p.skills, t.get("skills", [])) for p, t in pairs]
        ).to_dict(),
        "remote": score_enum_field(
            "remote", [(p.remote, t.get("remote")) for p, t in pairs]
        ).to_dict(),
        "seniority": score_enum_field(
            "seniority", [(p.seniority, t.get("seniority")) for p, t in pairs]
        ).to_dict(),
    }


def run(config: str, split: str | None):
    labels, source = load_labels(split)
    predict, model, prompt = get_predictor(config)
    prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()[:8]

    posts = {c["objectID"]: c for c in by_id([r["comment_id"] for r in labels])}

    pairs, latencies, texts = [], [], []
    for label in labels:
        text = to_text(posts[label["comment_id"]].get("comment_text"))
        started = time.perf_counter()
        pairs.append((predict(text), label))
        latencies.append((time.perf_counter() - started) * 1000)
        texts.append(text)

    by_slice = {}
    for name in sorted({slice_of(t) for t in texts}):
        subset = [p for p, t in zip(pairs, texts, strict=True) if slice_of(t) == name]
        if subset:
            by_slice[name] = {
                "n": len(subset),
                "skills_f1": score_set_field(
                    "skills", [(p.skills, t.get("skills", [])) for p, t in subset]
                ).to_dict()["macro_f1"],
            }

    return {
        "run_id": f"{config}-{datetime.now(UTC):%Y%m%dT%H%M%S}",
        "ts": datetime.now(UTC).isoformat(),
        "config": config,
        "split": split or "all",
        "labels_from": source,
        "model": model,
        "prompt_sha": prompt_sha,
        "n": len(labels),
        "scores": score_rows(pairs),
        "slices": by_slice,
        "p50_ms": round(statistics.median(latencies), 1),
        "p95_ms": round(sorted(latencies)[int(len(latencies) * 0.95) - 1], 1),
    }


def report():
    if not RUNS.exists():
        raise SystemExit("no runs yet. try: uv run evals/run.py --config rules")
    rows = [json.loads(line) for line in RUNS.read_text().splitlines() if line.strip()]
    print(f"{'config':<12} {'n':>4} {'salary cov':>11} {'salary prec':>12} "
          f"{'halluc':>7} {'skills F1':>10} {'p95 ms':>8}")
    print("-" * 70)
    for r in rows:
        s, k = r["scores"]["salary"], r["scores"]["skills"]
        print(f"{r['config']:<12} {r['n']:>4} {s['coverage']:>10.1%} "
              f"{s['precision']:>11.1%} {s['hallucination_rate']:>6.1%} "
              f"{k['macro_f1']:>10.3f} {r['p95_ms']:>8.0f}")
    print("\nprecision carries a 95% interval — see precision_ci95 in runs.jsonl. At small n a "
          "few points of difference is noise.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default="rules")
    ap.add_argument("--split", default=None, help="dev | held-out. omit for all")
    ap.add_argument("--report", action="store_true", help="print the table, run nothing")
    ap.add_argument("--dry-run", action="store_true", help="score but don't append a row")
    args = ap.parse_args()

    if args.report:
        report()
        return

    row = run(args.config, args.split)
    print(json.dumps(row, indent=2))

    if args.dry_run:
        print("\ndry run, nothing appended")
        return

    with RUNS.open("a") as fh:
        fh.write(json.dumps(row) + "\n")
    print(f"\nappended to {RUNS.name}")


if __name__ == "__main__":
    main()
