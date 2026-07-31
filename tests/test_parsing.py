"""Pure-function tests. No network, no API key, no data/raw needed.

The two xfails are load-bearing: they pin bugs I already found in the crude regex so that P5
confirms them and step 05 has to fix them. When step 05 lands, these turn green and the xfail
markers come off. A bug with a test on it is a task; a bug in my head is a maybe.
"""

import pytest

from ingest.corpus import to_text
from ingest.fetch import thread_date
from ingest.rules_poc import find_salary, find_skills


class TestThreadDate:
    """thread_date separates 'currently hiring' from the historical trends set, so a silent
    None here is a correctness bug, not a cosmetic one."""

    def test_parses_month_year(self):
        assert thread_date("Ask HN: Who is hiring? (July 2026)") == "2026-07-01"
        assert thread_date("Ask HN: Who is hiring? (February 2026)") == "2026-02-01"

    def test_none_when_unparseable(self):
        assert thread_date("Ask HN: Who is hiring?") is None
        assert thread_date("") is None
        assert thread_date(None) is None

    def test_ignores_a_bogus_month(self):
        assert thread_date("Who is hiring? (Smarch 2026)") is None


class TestToText:
    def test_strips_tags_and_unescapes(self):
        assert to_text("<i>Python</i> &amp; Go") == "Python & Go"

    def test_paragraph_becomes_blank_line(self):
        assert to_text("one<p>two") == "one\n\ntwo"

    def test_handles_none(self):
        assert to_text(None) == ""

    def test_strips_links_but_keeps_label(self):
        assert to_text('<a href="http://x.com" rel="nofollow">apply</a>') == "apply"


class TestFindSalary:
    def test_k_suffix_both_sides(self):
        assert find_salary("$180k-$230k") == (180000, 230000, "USD")

    def test_comma_thousands(self):
        assert find_salary("$200,000-$250,000") == (200000, 250000, "USD")

    def test_en_dash(self):
        assert find_salary("$130k–200k") == (130000, 200000, "USD")

    def test_non_usd_currency(self):
        lo, _hi, cur = find_salary("£60,000 - 95,669")
        assert (lo, cur) == (60000, "GBP")

    def test_none_when_absent(self):
        assert find_salary("Salary: competitive") == (None, None, None)
        assert find_salary("$0 + equity") == (None, None, None)

    @pytest.mark.xfail(reason="poc bug, fixed in ingest/rules.py", strict=True)
    def test_hourly_is_not_annual(self):
        """Post 48900749 is '~$30-120/hr'. The regex reports 30-120 as if annual. Whatever
        step 05 does, it must not silently put an hourly rate in the annual column."""
        assert find_salary("~$30-120/hr") != (30, 120, "USD")

    @pytest.mark.xfail(reason="poc bug, fixed in ingest/rules.py", strict=True)
    def test_trailing_k_applies_to_lower_bound(self):
        """Post 48885246 is '$140–200k'. Currently reads lo as 140, not 140000."""
        assert find_salary("$140–200k") == (140000, 200000, "USD")


class TestFindSkills:
    def test_finds_plain_words(self):
        assert find_skills("We use Python and Terraform") == ["python", "terraform"]

    def test_word_boundaries(self):
        """'go' must not fire on 'golang', 'google', or 'ago'."""
        assert find_skills("a while ago we used Google") == []

    def test_dotted_name(self):
        assert "next.js" in find_skills("Built on Next.js")

    def test_case_insensitive(self):
        assert find_skills("KUBERNETES") == ["kubernetes"]

    def test_deduplicates(self):
        assert find_skills("python python Python") == ["python"]

    def test_synonyms_are_not_merged_here(self):
        """k8s and kubernetes both match separately. Merging is step 08's job, and it has to
        happen on labels and predictions identically or skills F1 measures the synonym table."""
        assert find_skills("k8s and kubernetes") == ["k8s", "kubernetes"]
