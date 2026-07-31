"""The measurement instrument. Tested harder than anything else in the repo, because every
claim the project makes comes out of these functions — a quiet bug here doesn't crash, it
produces a confident wrong number that ends up in a README.
"""

import pytest

from evals.scorers import (
    Outcome,
    fuzzy_ratio,
    location_matches,
    margin,
    salary_matches,
    score_enum_field,
    score_nullable,
    score_nullable_field,
    score_set_field,
    score_set_pair,
    wilson,
)


class TestFourOutcomes:
    def test_extracted(self):
        assert score_nullable(180000, 180000) is Outcome.EXTRACTED

    def test_abstained_is_its_own_outcome(self):
        """Both say 'not stated'. That's agreement and a win, not a miss."""
        assert score_nullable(None, None) is Outcome.ABSTAINED

    def test_missed(self):
        assert score_nullable(None, 180000) is Outcome.MISSED

    def test_hallucinated(self):
        """The post said nothing; the extractor invented a number."""
        assert score_nullable(180000, None) is Outcome.HALLUCINATED

    def test_wrong_is_distinct_from_hallucinated(self):
        """A wrong value where one exists is recoverable — it shows up as an outlier. An
        invented value where none exists never does."""
        assert score_nullable(150000, 180000) is Outcome.WRONG

    def test_empty_string_counts_as_absent(self):
        assert score_nullable("", None) is Outcome.ABSTAINED
        assert score_nullable("", "Acme") is Outcome.MISSED


class TestCoverageVsPrecision:
    def test_cautious_extractor_beats_confident_wrong_one(self):
        """The whole reason these are separate numbers. The cautious one answers 4/10 and is
        never wrong; the confident one answers 10/10 and is wrong 6 times. A blended accuracy
        score would rank them equal — precision must not."""
        cautious = score_nullable_field(
            "salary", [(1, 1)] * 4 + [(None, None)] * 6
        )
        confident = score_nullable_field(
            "salary", [(1, 1)] * 4 + [(99, None)] * 6
        )

        assert cautious.precision == 1.0
        assert confident.precision == pytest.approx(0.4)
        assert cautious.hallucination_rate == 0.0
        assert confident.hallucination_rate == pytest.approx(0.6)

    def test_coverage_counts_attempts_not_correctness(self):
        r = score_nullable_field("salary", [(1, 1), (2, 5), (None, 7), (None, None)])
        assert r.attempts == 2
        assert r.coverage == pytest.approx(0.5)

    def test_hallucination_never_enters_precision_numerator(self):
        r = score_nullable_field("salary", [(99, None), (1, 1)])
        assert r.precision == pytest.approx(0.5)
        assert r.hallucination_rate == pytest.approx(0.5)

    def test_all_abstained_has_zero_coverage_not_perfect_precision(self):
        r = score_nullable_field("salary", [(None, None)] * 5)
        assert r.coverage == 0.0
        assert r.precision == 0.0, "no attempts means no precision, not 100%"


class TestWilson:
    def test_known_value(self):
        """84/100 → roughly (0.755, 0.897) by the standard Wilson formula."""
        lo, hi = wilson(84, 100)
        assert lo == pytest.approx(0.7554, abs=0.002)
        assert hi == pytest.approx(0.8973, abs=0.002)

    def test_stays_inside_zero_one_at_the_extremes(self):
        """Where the normal approximation runs outside [0,1] and understates uncertainty.

        The bounds are exactly 0 and 1 in exact arithmetic; approx covers the float error.
        """
        lo, hi = wilson(0, 10)
        assert lo == pytest.approx(0.0) and 0 < hi < 1
        lo, hi = wilson(10, 10)
        assert hi == pytest.approx(1.0) and 0 < lo < 1

    def test_never_reports_outside_zero_one(self):
        """Downstream code formats these as percentages, so a 1.0000000001 would print as
        100.00001% in a README."""
        for x, n in [(0, 1), (1, 1), (0, 40), (40, 40), (3, 7), (39, 40)]:
            lo, hi = wilson(x, n)
            assert 0.0 <= lo <= hi <= 1.0, (x, n, lo, hi)

    def test_no_data_means_no_information(self):
        assert wilson(0, 0) == (0.0, 1.0)

    def test_interval_narrows_as_n_grows(self):
        assert margin(8, 10) > margin(80, 100) > margin(800, 1000)

    def test_the_projects_headline_claim(self):
        """At n=40 a measured 84% carries roughly ±11 points, so 84 vs 86 is not a result.
        If this assertion ever fails, the README's central caveat is wrong."""
        m = margin(34, 40)  # 85%
        assert 0.09 < m < 0.13


class TestSkills:
    def test_both_empty_is_agreement(self):
        assert score_set_pair([], []) == (1.0, 1.0, 1.0)

    def test_one_empty_is_total_failure(self):
        assert score_set_pair(["python"], []) == (0.0, 0.0, 0.0)

    def test_synonyms_normalised_on_both_sides(self):
        """k8s in the prediction and Kubernetes in the label are the same skill. Normalising
        one side only would make this a false negative."""
        _p, _r, f = score_set_pair(["k8s"], ["Kubernetes"])
        assert f == 1.0

    def test_partial_overlap(self):
        p, r, _f = score_set_pair(["python", "go"], ["python", "rust"])
        assert p == pytest.approx(0.5) and r == pytest.approx(0.5)

    def test_macro_not_micro(self):
        """A post with 20 skills must not outweigh a post with 1. Pooling would give ~0.95;
        macro-averaging gives 0.5."""
        report = score_set_field(
            "skills",
            [
                (["a"] * 20, ["a"] * 20),          # perfect, 20 skills
                (["python"], ["rust"]),             # zero, 1 skill
            ],
        )
        assert report.macro_f1 == pytest.approx(0.5)


class TestEnums:
    def test_per_class_recall_exposes_a_never_predicted_class(self):
        """Overall accuracy would read 80% and hide that hybrid is never predicted."""
        pairs = [("remote", "remote")] * 8 + [("remote", "hybrid")] * 2
        r = score_enum_field("remote", pairs)
        assert r.accuracy == pytest.approx(0.8)
        assert r.per_class_recall()["hybrid"] == 0.0

    def test_confusion_records_direction(self):
        r = score_enum_field("remote", [("onsite", "remote")])
        assert r.matrix[("remote", "onsite")] == 1


class TestFieldComparators:
    def test_salary_needs_both_bounds(self):
        assert salary_matches((180000, 230000), (180000, 230000))
        assert not salary_matches((180000, 999999), (180000, 230000))

    def test_location_fuzzy(self):
        assert location_matches("San Francisco, CA", "San Francisco, CA")
        assert not location_matches("San Francisco", "New York")

    def test_fuzzy_ratio_bounds(self):
        assert fuzzy_ratio("abc", "abc") == 1.0
        assert fuzzy_ratio("", "") == 1.0
        assert fuzzy_ratio("abc", "xyz") == 0.0

    def test_comparator_is_pluggable(self):
        assert score_nullable("SF", "SF, CA", compare=lambda a, b: a in b) is Outcome.EXTRACTED
