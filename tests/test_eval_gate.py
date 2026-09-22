"""Step 22. The rules parser against all 80 labeled posts, in CI.

The parser is deterministic, so these numbers don't wobble run to run. If one drops, a change
made the parser worse on real posts, and the build should say so before it merges.

Floors sit a few points under where the numbers are today, not at them, so a harmless change to
one post doesn't fail the build. Hallucination gets a ceiling of its own, because a parser that
starts inventing values is a worse regression than one that starts leaving them blank.

The post text is committed in tests/eval_posts.json because data/raw is gitignored and CI
doesn't have it.
"""

import json
from pathlib import Path

import pytest

from evals.run import predict_rules, score_rows

ROOT = Path(__file__).resolve().parent.parent
LABELS = ROOT / "evals" / "labeled.jsonl"
POSTS = Path(__file__).resolve().parent / "eval_posts.json"

# (field, metric, floor or ceiling). Today, over all 80: company 85.0%, salary 93.3%,
# location 77.8% precision; salary halluc 1.3%, location 2.5%; skills F1 0.702.
FLOORS = [
    ("company", "precision", 0.80),
    ("salary", "precision", 0.85),
    ("location", "precision", 0.70),
]
CEILINGS = [
    ("company", "hallucination_rate", 0.02),
    ("salary", "hallucination_rate", 0.03),
    ("location", "hallucination_rate", 0.05),
]
SKILLS_F1_FLOOR = 0.65


@pytest.fixture(scope="module")
def scores():
    labels = [json.loads(x) for x in LABELS.read_text().splitlines() if x.strip()]
    texts = json.loads(POSTS.read_text())
    assert len(labels) == 80 and set(texts) == {r["comment_id"] for r in labels}
    return score_rows([(predict_rules(texts[r["comment_id"]]), r) for r in labels])


@pytest.mark.parametrize("field,metric,floor", FLOORS)
def test_precision_floor(scores, field, metric, floor):
    assert scores[field][metric] >= floor, f"{field} {metric} {scores[field][metric]:.3f}"


@pytest.mark.parametrize("field,metric,ceiling", CEILINGS)
def test_hallucination_ceiling(scores, field, metric, ceiling):
    assert scores[field][metric] <= ceiling, f"{field} {metric} {scores[field][metric]:.3f}"


def test_skills_f1_floor(scores):
    assert scores["skills"]["macro_f1"] >= SKILLS_F1_FLOOR
