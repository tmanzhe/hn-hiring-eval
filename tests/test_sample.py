"""The stratified sampler.

The sample determines what the whole project can and can't claim, so the properties that matter
are reproducibility, coverage of rare strata, and honesty about statistical power.

Runs against a synthetic corpus with known strata rather than `data/raw/`. An earlier version
read the real corpus, which is gitignored — the tests passed locally and failed in CI on a
machine that had never fetched anything. Injecting the corpus makes the sampler testable and is
better design regardless.
"""

import pytest

from evals.sample import SEED, draw, slice_power, split, strata

PIPE = "Acme | Senior Engineer | Remote | {pay}\n\nWe use Python and Terraform here."
PROSE = "We are a small team looking for an engineer. {pay} We work with Python."


def corpus(n_pipe=400, n_prose=60, salary_frac=0.3, long_frac=0.4):
    """A synthetic corpus with strata I control, so allocation is checkable by arithmetic."""
    out = []
    for i in range(n_pipe + n_prose):
        template = PIPE if i < n_pipe else PROSE
        pay = "$180k-$220k" if i % int(1 / salary_frac) == 0 else "competitive pay"
        body = template.format(pay=pay)
        if i % int(1 / long_frac) == 0:
            body += " padding." * 200
        out.append({"objectID": str(100000 + i), "comment_text": body,
                    "thread_date": "2026-07-01"})
    return out


@pytest.fixture
def synthetic():
    return corpus()


class TestStrata:
    def test_pipe_header(self):
        assert strata("A | B | C | $180k\n\nbody")[0] == "pipe"

    def test_prose(self):
        assert strata("We are a small team hiring an engineer.")[0] == "prose"

    def test_salary_dimension(self):
        assert strata("Acme | Eng | Remote | $180k-$220k")[1] == "has_salary"
        assert strata("Acme | Eng | Remote | competitive")[1] == "no_salary"

    def test_length_dimension(self):
        assert strata("x" * 2000)[2] == "long"
        assert strata("short post")[2] == "short"

    def test_is_mechanical_not_judgment(self):
        """Every dimension must be derivable from text alone, or the sample can't be drawn
        before the hand tally exists."""
        assert len(strata("anything")) == 3


class TestDraw:
    def test_reproducible(self, synthetic):
        """The sampling rule lives in code. Same seed, same posts, every time — otherwise the
        labeled set can't be regenerated or audited."""
        a, _, _ = draw(30, seed=SEED, corpus=synthetic)
        b, _, _ = draw(30, seed=SEED, corpus=synthetic)
        assert [c["objectID"] for c in a] == [c["objectID"] for c in b]

    def test_different_seed_gives_a_different_sample(self, synthetic):
        a, _, _ = draw(30, seed=1, corpus=synthetic)
        b, _, _ = draw(30, seed=2, corpus=synthetic)
        assert [c["objectID"] for c in a] != [c["objectID"] for c in b]

    def test_no_duplicates(self, synthetic):
        chosen, _, _ = draw(60, corpus=synthetic)
        ids = [c["objectID"] for c in chosen]
        assert len(ids) == len(set(ids))

    def test_draws_the_requested_size(self, synthetic):
        chosen, _, _ = draw(60, corpus=synthetic)
        assert len(chosen) == 60

    def test_every_stratum_is_represented(self, synthetic):
        """Pure proportional allocation gives rare strata zero posts, and a stratum with no
        posts can't be reported on at all. The floor is what buys that."""
        _, allocation, grouped = draw(60, corpus=synthetic)
        assert all(allocation[k] >= 1 for k in grouped)

    def test_never_over_draws_a_small_stratum(self, synthetic):
        _, allocation, grouped = draw(60, corpus=synthetic)
        assert all(allocation[k] <= len(grouped[k]) for k in grouped)

    def test_not_just_the_first_n(self, synthetic):
        """A sample of the top of the thread is a sample of whoever posted on the 1st."""
        chosen, _, _ = draw(30, corpus=synthetic)
        head = {c["objectID"] for c in synthetic[:30]}
        assert len({c["objectID"] for c in chosen} & head) < 25


class TestOversample:
    def test_boosts_the_named_slice(self, synthetic):
        _, base, _ = draw(60, corpus=synthetic)
        _, boosted, grouped = draw(60, oversample={"prose": 18}, corpus=synthetic)
        prose_cells = [k for k in grouped if "prose" in k]
        assert sum(boosted[k] for k in prose_cells) >= 18
        assert sum(boosted[k] for k in prose_cells) > sum(base[k] for k in prose_cells)

    def test_still_draws_the_requested_size(self, synthetic):
        chosen, _, _ = draw(60, oversample={"prose": 18}, corpus=synthetic)
        assert len(chosen) == 60

    def test_unknown_value_is_a_no_op_not_a_crash(self, synthetic):
        chosen, _, _ = draw(60, oversample={"nonsense": 20}, corpus=synthetic)
        assert len(chosen) == 60


class TestSplit:
    def test_two_thirds_dev(self, synthetic):
        chosen, _, _ = draw(60, corpus=synthetic)
        counts = split(chosen)
        assert sum(1 for v in counts.values() if v == "dev") == 40
        assert sum(1 for v in counts.values() if v == "held-out") == 20

    def test_reproducible(self, synthetic):
        chosen, _, _ = draw(60, corpus=synthetic)
        assert split(chosen) == split(chosen)

    def test_every_post_assigned_exactly_once(self, synthetic):
        chosen, _, _ = draw(60, corpus=synthetic)
        assigned = split(chosen)
        assert len(assigned) == len(chosen)
        assert set(assigned.values()) == {"dev", "held-out"}


class TestSlicePower:
    def test_reports_a_margin_per_slice(self, synthetic):
        chosen, _, _ = draw(60, corpus=synthetic)
        rows = slice_power(chosen)
        assert {dim for dim, _, _, _ in rows} == {"format", "salary", "length"}
        assert all(0 <= m <= 1 for _, _, _, m in rows)

    def test_smaller_slices_carry_wider_margins(self, synthetic):
        """The whole point: a thin slice must visibly announce that it can't support a claim."""
        chosen, _, _ = draw(60, corpus=synthetic)
        rows = sorted(slice_power(chosen), key=lambda r: r[2])
        assert rows[0][3] > rows[-1][3]

    def test_margins_are_computed_not_hardcoded(self, synthetic):
        chosen, _, _ = draw(60, corpus=synthetic)
        for _, _, n, m in slice_power(chosen):
            assert m == pytest.approx(m)
            assert (m > 0.20) == (n < 15), "margin must track n"
