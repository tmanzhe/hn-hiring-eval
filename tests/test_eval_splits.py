"""Frozen eval membership and held-out CLI isolation; no raw corpus or API needed."""

import html
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from evals import run

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "tests" / "eval_posts.json"


def test_frozen_split_partitions_all_posts_and_preserves_existing_assignments():
    splits = json.loads(run.SPLITS.read_text())
    tune, held_out = splits["tune"], splits["held-out"]
    assert len(tune) == len(set(tune)) == 53
    assert len(held_out) == len(set(held_out)) == 27
    assert set(tune).isdisjoint(held_out)
    assert set(tune) | set(held_out) == set(json.loads(POSTS.read_text()))
    labels, _ = run.load_labels(None)
    assert set(tune) == {r["comment_id"] for r in labels if r["split"] == "dev"}
    assert set(held_out) == {r["comment_id"] for r in labels if r["split"] == "held-out"}
    assert run.load_labels("tune") == run.load_labels("dev")
    assert run.load_labels("all") == run.load_labels(None)


def test_membership_uses_frozen_ids_even_if_label_split_metadata_changes(monkeypatch, tmp_path):
    expected, _ = run.load_labels("held-out")
    labels, _ = run.load_labels(None)
    for row in labels:
        row["split"] = "dev"  # Moving metadata cannot move a held-out post into tune.
    path = tmp_path / "labels.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in reversed(labels)))
    monkeypatch.setattr(run, "LABELS", path)
    actual, _ = run.load_labels("held-out")
    assert {r["comment_id"] for r in actual} == {r["comment_id"] for r in expected}
    tune, _ = run.load_labels("tune")
    assert len(tune) == 53
    assert {r["comment_id"] for r in tune}.isdisjoint(r["comment_id"] for r in actual)


@pytest.mark.parametrize("problem", ["missing", "duplicate", "unfinished"])
def test_incomplete_or_duplicate_labels_cannot_silently_reduce_eval_size(
    monkeypatch, tmp_path, problem,
):
    labels, _ = run.load_labels(None)
    if problem == "missing":
        labels.pop()
    elif problem == "duplicate":
        labels[-1] = labels[0]
    else:
        labels[-1]["done"] = False
    path = tmp_path / "labels.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in labels))
    monkeypatch.setattr(run, "LABELS", path)
    with pytest.raises(SystemExit, match="frozen split IDs"):
        run.load_labels("held-out")


def test_held_out_cli_scores_only_held_out_posts(monkeypatch, tmp_path):
    texts = json.loads(POSTS.read_text())
    held_out = json.loads(run.SPLITS.read_text())["held-out"]
    # Only held-out inputs exist: requesting any tune input fails in by_id().
    corpus = {"comments": [
        {"objectID": cid, "comment_text": html.escape(texts[cid])} for cid in held_out
    ]}
    (tmp_path / "corpus.json").write_text(json.dumps(corpus))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    previous_runs = run.RUNS.read_bytes() if run.RUNS.exists() else None
    result = subprocess.run(
        [sys.executable, "evals/run.py", "--config", "rules", "--split", "held-out", "--dry-run"],
        cwd=ROOT, env={**os.environ, "HN_RAW_DIR": str(tmp_path)},
        capture_output=True, text=True, timeout=30, check=True,
    )
    row, _ = json.JSONDecoder().raw_decode(result.stdout)
    assert row["split"] == "held-out"
    assert row["config"] == "rules"
    assert row["model"] == "n/a"
    assert row["n"] == 27
    assert set(row["scores"]) == {"company", "salary", "location", "skills", "remote", "seniority"}
    assert all(score["n"] == 27 for score in row["scores"].values())
    assert (run.RUNS.read_bytes() if run.RUNS.exists() else None) == previous_runs
