"""Integration test. Runs the whole rules path over a real (tiny) thread and out to Parquet.

Unit tests cover the pieces. This covers the wiring — schema drift, a normalize step that
silently drops a field, a Parquet write that can't serialise a list column. None of those show
up in a pure-function test, and all of them break the pipeline.

The fixture is six genuine posts from the July 2026 thread, committed so CI needs no network.
"""

import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from ingest.corpus import to_text
from ingest.normalize import display_skills, normalize
from ingest.rules import is_confident, parse
from ingest.schema import Posting

FIXTURE = Path(__file__).parent / "fixtures" / "sample_thread.json"


@pytest.fixture(scope="module")
def thread():
    return json.loads(FIXTURE.read_text())


@pytest.fixture(scope="module")
def rows(thread):
    """The pipeline, minus the file I/O."""
    out = []
    for c in thread["comments"]:
        extraction, confidence = parse(to_text(c.get("comment_text")))
        out.append(
            (
                Posting(
                    **normalize(extraction).model_dump(),
                    comment_id=int(c["objectID"]),
                    thread_date=thread["thread_date"],
                    extracted_by="rules",
                ),
                confidence,
            )
        )
    return out


class TestPipelineRuns:
    def test_every_post_produces_a_row(self, thread, rows):
        assert len(rows) == len(thread["comments"]) == 6

    def test_no_post_crashes_the_parser(self, rows):
        """A post that defeats the rules must yield an empty Extraction, never an exception.
        1,696 of 1,995 posts take this path, so a crash here stops the whole run."""
        assert all(isinstance(r, Posting) for r, _ in rows)

    def test_some_posts_are_handled_and_some_are_not(self, rows):
        """If everything passed, the confidence check is doing nothing and the LLM has no work.
        If nothing passed, the rules path is worthless. Both are red flags."""
        handled = [c for _, c in rows if is_confident(c)]
        assert 0 < len(handled) < len(rows)


class TestKnownValues:
    """Regression guards on real posts. If a parser change breaks these, it broke the corpus."""

    def by_id(self, rows, cid):
        return next(r for r, _ in rows if r.comment_id == cid)

    def test_pipe_delimited_post(self, rows):
        r = self.by_id(rows, 48915735)
        assert (r.salary_min, r.salary_max, r.salary_period) == (180000, 230000, "year")
        assert r.remote == "remote"

    def test_equity_only_post_abstains(self, rows):
        """'$0 + equity' — no salary is the correct answer, not zero."""
        r = self.by_id(rows, 48919859)
        assert r.salary_min is None and r.salary_currency is None

    def test_hourly_post_is_annualised_but_flagged(self, rows):
        r = self.by_id(rows, 48900749)
        assert r.salary_period == "hour", "provenance must survive normalization"
        assert r.salary_min and r.salary_min > 10_000, "column must be annual"

    def test_trailing_k_post(self, rows):
        r = self.by_id(rows, 48885246)
        assert r.salary_min == 140000, "the k in '$140-200k' applies to both bounds"


class TestParquetRoundTrip:
    def test_writes_and_reads_back(self, rows, tmp_path):
        import pyarrow as pa

        table = pa.Table.from_pylist(
            [
                {
                    **r.model_dump(),
                    "skills": display_skills(r.skills),
                    "thread_month": r.thread_date.strftime("%Y-%m"),
                }
                for r, _ in rows
            ]
        )
        dest = tmp_path / "postings.parquet"
        pq.write_table(table, dest, compression="snappy")

        back = pq.read_table(dest)
        assert back.num_rows == len(rows)

        cols = set(back.column_names)
        for required in ("comment_id", "salary_min", "salary_period", "skills",
                         "thread_date", "thread_month", "extracted_by"):
            assert required in cols, f"{required} missing from Parquet"

    def test_skills_survive_as_a_list_column(self, rows, tmp_path):
        """Nested list columns are the thing most likely to break on a schema change, and the
        trends query depends on list_contains working."""
        import pyarrow as pa

        table = pa.Table.from_pylist(
            [{"comment_id": r.comment_id, "skills": display_skills(r.skills)} for r, _ in rows]
        )
        dest = tmp_path / "skills.parquet"
        pq.write_table(table, dest)
        back = pq.read_table(dest).to_pylist()
        assert any(isinstance(row["skills"], list) and row["skills"] for row in back)
