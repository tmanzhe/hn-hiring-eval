"""The eval runner. Covers the pure parts — slicing, the scores block, attribution fields.

The parts that need labels or an API key aren't covered here; `evals/run.py --dry-run` against
real labels is the check for those.
"""

import json

import pytest

from evals.run import score_rows, slice_of
from ingest.schema import Extraction


class TestSlicing:
    def test_pipe_header_detected(self):
        assert slice_of("Acme | Engineer | Remote | $180k\n\nWe use Python.") == "pipe"

    def test_short_prose(self):
        assert slice_of("We are a small team looking for help.") == "prose"

    def test_long_prose_is_its_own_slice(self):
        """Length is a plausible driver of extraction difficulty, so it gets its own bucket
        rather than being averaged into prose."""
        assert slice_of("word " * 400) == "long_prose"

    def test_a_pipe_in_the_body_does_not_count(self):
        """Only the header line matters — a pipe inside prose isn't the convention."""
        assert slice_of("We are hiring.\n\nStack: python | go | rust") == "prose"

    def test_never_returns_none(self):
        for text in ("", "\n\n", "x"):
            assert slice_of(text)


class TestScoresBlock:
    def pair(self, **kw):
        return Extraction(**kw)

    def test_every_field_reported(self):
        pairs = [(self.pair(company="Acme"), {"company": "Acme"})]
        scores = score_rows(pairs)
        assert set(scores) == {"company", "salary", "location", "skills", "remote", "seniority"}

    def test_salary_compared_as_a_pair_not_two_fields(self):
        """Right floor, wrong ceiling is a wrong answer — not half right."""
        pairs = [(self.pair(salary_min=180000, salary_max=999999),
                  {"salary_min": 180000, "salary_max": 230000})]
        assert score_rows(pairs)["salary"]["outcomes"] == {"wrong": 1}

    def test_absent_salary_on_both_sides_is_abstained(self):
        pairs = [(self.pair(), {"salary_min": None})]
        assert score_rows(pairs)["salary"]["outcomes"] == {"abstained": 1}

    def test_invented_salary_is_hallucinated(self):
        pairs = [(self.pair(salary_min=1, salary_max=2), {"salary_min": None})]
        s = score_rows(pairs)["salary"]
        assert s["outcomes"] == {"hallucinated": 1}
        assert s["hallucination_rate"] == 1.0

    def test_confidence_interval_present_on_every_nullable_field(self):
        """A point estimate without an interval is the error the whole project criticises."""
        pairs = [(self.pair(company="Acme"), {"company": "Acme"})]
        scores = score_rows(pairs)
        for name in ("company", "salary", "location"):
            assert "precision_ci95" in scores[name], name
            lo, hi = scores[name]["precision_ci95"]
            assert 0.0 <= lo <= hi <= 1.0

    def test_block_is_json_serialisable(self):
        """It gets written to runs.jsonl, so a Counter or an Enum leaking through breaks the
        append silently at the end of a long run."""
        pairs = [(self.pair(company="Acme", remote="remote"), {"company": "Acme", "remote": "remote"})]
        json.dumps(score_rows(pairs))


class TestAttribution:
    def test_prompt_sha_changes_with_the_prompt(self):
        """Prompt changes are code changes. Two runs with different prompts must not be
        indistinguishable in runs.jsonl."""
        import hashlib

        a = hashlib.sha256(b"prompt one").hexdigest()[:8]
        b = hashlib.sha256(b"prompt two").hexdigest()[:8]
        assert a != b

    def test_unknown_config_fails_loudly(self):
        from evals.run import get_predictor

        with pytest.raises(SystemExit, match="unknown config"):
            get_predictor("magic")

    def test_rules_config_needs_no_model(self):
        """The baseline has to be runnable with no API key, or there's no baseline until
        billing is set up."""
        from evals.run import get_predictor

        _, model, _ = get_predictor("rules")
        assert model == "n/a"

    def test_hourly_label_is_annualised_before_comparing(self):
        """AES in the sample: the post says $30-40/hr, the label records 30-40 hour, and the
        prediction arrives annualised by normalize(). Same salary, so it must score extracted."""
        pairs = [(Extraction(salary_min=62400, salary_max=83200, salary_period="hour"),
                  {"salary_min": 30, "salary_max": 40, "salary_period": "hour"})]
        assert score_rows(pairs)["salary"]["outcomes"] == {"extracted": 1}
