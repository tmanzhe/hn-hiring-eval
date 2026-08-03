"""The groundedness check.

This is the one thing standing between a generated sentence and a user, so the tests are
written around the failure that matters: a plausible-looking number that no retrieved posting
supports.
"""

import pytest

from api.groundedness import assert_grounded, check

ROWS = [
    {"comment_id": 1, "company": "Acme", "salary_min": 180000, "salary_max": 230000,
     "skills": ["Python", "Terraform"]},
    {"comment_id": 2, "company": "Globex", "salary_min": 150000, "salary_max": 190000,
     "skills": ["Python", "React"]},
]


class TestMoney:
    def test_exact_figure_from_a_row_passes(self):
        assert check("Top match pays $180,000.", ROWS).grounded

    def test_k_abbreviation_matches_the_stored_integer(self):
        """The model writes $180k; the row stores 180000. Same claim."""
        assert check("Top match pays $180k.", ROWS).grounded

    def test_invented_figure_is_caught(self):
        r = check("Top match pays $250,000.", ROWS)
        assert not r.grounded
        assert r.ungrounded[0].kind == "money"

    def test_plausible_but_absent_figure_is_still_caught(self):
        """$200k sits between two real ranges and reads perfectly. No row contains it."""
        assert not check("Roles pay around $200k.", ROWS).grounded

    def test_comma_grouped_figure_is_not_double_scanned(self):
        """Regression: '$180,000' was verified as money and then its trailing '000' was
        re-scanned as an unsupported count. A false positive here blocks a correct summary,
        which is worse than missing a fabrication — the feature becomes unusable."""
        r = check("Top match pays $180,000.", ROWS)
        assert r.grounded
        assert [c.kind for c in r.claims] == ["money"]


class TestCounts:
    def test_result_count_is_legitimate(self):
        """'2 roles matched' is true of the result set even though no posting contains a 2."""
        assert check("2 roles matched your resume.", ROWS).grounded

    def test_wrong_count_is_caught(self):
        assert not check("7 roles matched your resume.", ROWS).grounded

    def test_hedged_count_gets_a_looser_standard(self):
        """'about 3' against an actual 2 is hedging, not fabrication. 'exactly 3' would fail."""
        assert check("About 3 roles matched.", ROWS).grounded
        assert not check("3 roles matched.", ROWS).grounded

    def test_explicit_allowed_counts(self):
        assert check("Showing 5 of 2 results.", ROWS, allowed_counts={2, 5}).grounded


class TestSkills:
    def test_skill_required_by_a_row_passes(self):
        assert check("Both roles want Python.", ROWS).grounded

    def test_skill_no_row_mentions_is_caught(self):
        r = check("These roles want Kubernetes.", ROWS)
        assert not r.grounded
        assert r.ungrounded[0].kind == "skill"

    def test_synonym_counts_as_the_canonical_skill(self):
        rows = [{"comment_id": 1, "skills": ["Kubernetes"], "salary_min": None, "salary_max": None}]
        assert check("They want k8s experience.", rows, allowed_counts={1}).grounded


class TestFailsClosed:
    def test_one_bad_claim_fails_the_whole_summary(self):
        r = check("Acme pays $180k and wants Python and Kubernetes.", ROWS)
        assert not r.grounded
        assert len(r.ungrounded) == 1

    def test_assert_raises_rather_than_returning(self):
        """A wrong number in a user-facing sentence is worse than no sentence."""
        with pytest.raises(ValueError, match="ungrounded"):
            assert_grounded("Pays $999,000.", ROWS)

    def test_assert_returns_the_report_on_success(self):
        assert assert_grounded("2 roles matched, both want Python.", ROWS).grounded

    def test_empty_summary_is_trivially_grounded(self):
        """No claims, nothing to verify. Vacuous, and honest about being vacuous."""
        r = check("", ROWS)
        assert r.grounded and r.claims == []

    def test_no_rows_means_every_figure_is_ungrounded(self):
        assert not check("Top match pays $180k.", [], allowed_counts={0}).grounded


class TestReport:
    def test_serialisable_for_the_evals_page(self):
        import json

        json.dumps(check("Pays $999k and wants Kubernetes.", ROWS).to_dict())

    def test_counts_claims_not_just_failures(self):
        d = check("2 roles want Python and pay $180k.", ROWS).to_dict()
        assert d["n_claims"] >= 3
        assert d["n_ungrounded"] == 0
