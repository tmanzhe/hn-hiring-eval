"""API endpoints and the matcher.

The endpoint tests need a Parquet file, so they build a tiny one in a tmp dir and point
PARQUET_URI at it. No network, no key, no dependency on data/ having been populated.
"""

from typing import ClassVar

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from fastapi.testclient import TestClient

from api import db
from api.matching import idf, precision_at_k, rank, skills_in

ROWS = [
    {"comment_id": 1, "company": "Acme", "location": "NYC", "remote": "remote",
     "salary_min": 180000, "salary_max": 230000, "salary_period": "year", "seniority": "senior",
     "skills": ["Python", "Terraform", "AWS"], "thread_month": "2026-07"},
    {"comment_id": 2, "company": "Globex", "location": "SF", "remote": "onsite",
     "salary_min": 150000, "salary_max": 190000, "salary_period": "year", "seniority": "mid",
     "skills": ["Python", "React"], "thread_month": "2026-07"},
    {"comment_id": 3, "company": "Initech", "location": "Remote", "remote": "remote",
     "salary_min": None, "salary_max": None, "salary_period": None, "seniority": None,
     "skills": ["Python"], "thread_month": "2026-06"},
]


@pytest.fixture
def client(tmp_path, monkeypatch):
    path = tmp_path / "postings.parquet"
    pq.write_table(pa.Table.from_pylist(ROWS), path)
    monkeypatch.setenv("PARQUET_URI", str(path))
    monkeypatch.setenv("PARQUET_CACHE", str(tmp_path / "cache.parquet"))
    db.reset()
    monkeypatch.setattr(db, "LOCAL_CACHE", tmp_path / "cache.parquet")
    with TestClient(app_with_reset()) as c:
        yield c
    db.reset()


def app_with_reset():
    from api.main import app

    return app


class TestHealth:
    def test_reports_row_count(self, client):
        body = client.get("/health").json()
        assert body["status"] == "ok"
        assert body["postings"] == 3


class TestJobs:
    def test_defaults_to_the_latest_thread_only(self, client):
        """'Currently hiring' means the current thread. Spanning every thread would list roles
        filled months ago — a correctness property, not a filter preference."""
        ids = {j["comment_id"] for j in client.get("/api/jobs").json()}
        assert ids == {1, 2}, "2026-06 posting must not appear"

    def test_month_filter(self, client):
        ids = {j["comment_id"] for j in client.get("/api/jobs?month=2026-06").json()}
        assert ids == {3}

    def test_skill_filter(self, client):
        ids = {j["comment_id"] for j in client.get("/api/jobs?skill=Terraform").json()}
        assert ids == {1}

    def test_remote_filter(self, client):
        ids = {j["comment_id"] for j in client.get("/api/jobs?remote=remote").json()}
        assert ids == {1}

    def test_min_salary_filter(self, client):
        ids = {j["comment_id"] for j in client.get("/api/jobs?min_salary=170000").json()}
        assert ids == {1}

    def test_rejects_a_bad_remote_value(self, client):
        assert client.get("/api/jobs?remote=hovercraft").status_code == 422

    def test_nulls_survive_the_round_trip(self, client):
        job = client.get("/api/jobs?month=2026-06").json()[0]
        assert job["salary_min"] is None, "abstention must not become 0"


class TestTrends:
    def test_share_not_raw_count(self, client):
        """Raw counts track thread size, so a bigger thread looks like rising demand for
        everything. Share is the honest measure."""
        rows = client.get("/api/trends?skills=Python").json()
        by_month = {r["thread_month"]: r for r in rows}
        assert by_month["2026-07"]["postings"] == 2
        assert by_month["2026-07"]["share"] == pytest.approx(1.0)
        assert by_month["2026-06"]["share"] == pytest.approx(1.0)

    def test_unknown_skill_returns_nothing_rather_than_erroring(self, client):
        assert client.get("/api/trends?skills=Fortran").json() == []


class TestMatch:
    def test_ranks_and_reports_gaps(self, client):
        r = client.post("/api/match", json={"resume": "I work with Python and Terraform daily."})
        body = r.json()
        assert body["matches"][0]["comment_id"] == 1
        assert "AWS" in body["matches"][0]["gap_skills"]

    def test_states_that_no_model_ranked_these(self, client):
        assert "No model" in client.post(
            "/api/match", json={"resume": "Python and Terraform experience here."}
        ).json()["note"]

    def test_short_resume_rejected(self, client):
        assert client.post("/api/match", json={"resume": "python"}).status_code == 422


class TestMatcher:
    """The ranking maths, independent of HTTP."""

    POSTINGS: ClassVar[list[dict]] = [
        {"comment_id": 1, "company": "A", "skills": ["python", "terraform"]},
        {"comment_id": 2, "company": "B", "skills": ["python", "react"]},
        {"comment_id": 3, "company": "C", "skills": ["python"]},
        {"comment_id": 4, "company": "D", "skills": ["python", "go", "rust", "kafka"]},
    ]

    def test_idf_ranks_rare_skills_higher(self):
        weights = idf(self.POSTINGS)
        assert weights["terraform"] > weights["python"]

    def test_minimum_overlap_excludes_one_skill_posts(self):
        """Naive overlap/required gives the single-skill post a perfect 1.0 and ranks it first.
        That's the bug the floor exists to prevent."""
        out = rank("python developer", self.POSTINGS)
        assert 3 not in {m.comment_id for m in out}

    def test_rare_skill_match_beats_common_one(self):
        out = rank("python and terraform", self.POSTINGS)
        assert out[0].comment_id == 1

    def test_gaps_reported(self):
        out = rank("python and go", self.POSTINGS)
        match = next(m for m in out if m.comment_id == 4)
        assert set(match.missing) == {"kafka", "rust"}

    def test_deterministic_order(self):
        a = [m.comment_id for m in rank("python and go", self.POSTINGS)]
        b = [m.comment_id for m in rank("python and go", self.POSTINGS)]
        assert a == b

    def test_empty_resume_returns_nothing(self):
        assert rank("I enjoy long walks", self.POSTINGS) == []

    def test_skills_in_uses_word_boundaries(self):
        assert "go" not in skills_in("a while ago at Google")

    def test_precision_at_k(self):
        out = rank("python and terraform", self.POSTINGS)
        assert precision_at_k(out, {1}) == pytest.approx(1 / len(out))
        assert precision_at_k([], {1}) == 0.0
