"""Step 05 parser. Every case here came from a real post in data/raw, not from imagination."""

import pytest

from ingest.normalize import normalize, normalize_skills, to_annual
from ingest.rules import find_salary, find_skills, is_confident, parse


class TestSalaryRanges:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("$180k-$230k", (180000, 230000, "USD", "year")),
            ("$200,000-$250,000", (200000, 250000, "USD", "year")),
            ("$130k–200k", (130000, 200000, "USD", "year")),
            ("$160~170k", (160000, 170000, "USD", "year")),
            ("$175,000 to $215,000", (175000, 215000, "USD", "year")),
        ],
    )
    def test_annual_ranges(self, text, expected):
        assert find_salary(text) == expected

    def test_trailing_k_applies_to_both_bounds(self):
        """rules_poc read the low end of '$140-200k' as 140. This is the fix."""
        assert find_salary("$140–200k") == (140000, 200000, "USD", "year")

    def test_hourly_is_kept_hourly(self):
        """rules_poc reported '~$30-120/hr' as an annual 30-120."""
        assert find_salary("~$30-120/hr") == (30, 120, "USD", "hour")

    def test_monthly(self):
        assert find_salary("$4,000/month") == (4000, 4000, "USD", "month")

    def test_non_usd(self):
        assert find_salary("£60,000 - 95,669")[2] == "GBP"


class TestSingleFigures:
    def test_single_annual_figure(self):
        assert find_salary("| Full-Time | $190k | US citizenship") == (
            190000, 190000, "USD", "year",
        )

    def test_single_with_explicit_period(self):
        assert find_salary("Salary: $25/hour part time") == (25, 25, "USD", "hour")

    def test_bare_small_figure_is_not_a_wage(self):
        """'Bounty: $500 for each referral' must not become a $500/hr job. Single figures need
        an explicit period or an annual-sized magnitude."""
        assert find_salary("Bounty: $500 for each referral") == (None, None, None, None)


class TestAbstaining:
    @pytest.mark.parametrize(
        "text",
        [
            "$0 + equity",
            "Salary: competitive",
            "we've raised $140M+ and are expanding",
            "processing over $43B/day",
            "combined $30 trillion in assets under management",
            "moved over $1 billion through our platform",
            "$7/month for a pair of tickets",
        ],
    )
    def test_returns_nothing_rather_than_guessing(self, text):
        assert find_salary(text) == (None, None, None, None)

    def test_ambiguous_magnitude_abstains(self):
        """'$3.5k-$4.9k' with no period could be monthly or annual. Saying nothing is correct —
        a wrong number here is unrecoverable, a missing one only costs coverage."""
        assert find_salary("$3.5k–$4.9k") == (None, None, None, None)


class TestSkills:
    def test_word_boundaries(self):
        assert find_skills("a while ago we used Google") == []

    def test_plus_signs_survive(self):
        assert "c++" in find_skills("strong C++ background")

    def test_dotted_names(self):
        assert "next.js" in find_skills("built on Next.js")


class TestParse:
    HEADER = "Portless | AI Engineer | Remote (North America) | $180k-$230k | Full-time"

    def test_pipe_header(self):
        ex, conf = parse(self.HEADER + "\n\nWe use Python and Kubernetes.")
        assert ex.company == "Portless"
        assert ex.remote == "remote"
        assert ex.salary_min == 180000
        assert conf["salary"] is True

    def test_prose_post_yields_less(self):
        ex, conf = parse("We are a small team looking for someone to help us grow.")
        assert ex.salary_min is None
        assert conf["salary"] is False
        assert not is_confident(conf)

    def test_confidence_requires_salary_and_skills(self):
        assert is_confident({"salary": True, "skills": True}) is True
        assert is_confident({"salary": True, "skills": False}) is False
        assert is_confident({"salary": False, "skills": True}) is False


class TestNormalize:
    def test_synonyms_collapse(self):
        assert normalize_skills(["k8s", "Kubernetes", "postgres"]) == [
            "kubernetes", "postgresql",
        ]

    def test_hourly_becomes_annual(self):
        assert to_annual(50, "hour") == 104000
        assert to_annual(4000, "month") == 48000
        assert to_annual(180000, "year") == 180000

    def test_none_in_none_out(self):
        assert to_annual(None, "year") is None
        assert to_annual(100, None) is None

    def test_normalize_converts_but_keeps_period(self):
        ex, _ = parse("Contract | $30-120/hr | Python and Docker")
        out = normalize(ex)
        assert out.salary_period == "hour", "provenance must survive"
        assert out.salary_min == 30 * 2080, "column must be comparable across posts"
