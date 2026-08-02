"""Step 24. FastAPI over DuckDB.

    uv run uvicorn api.main:app --reload
    open http://127.0.0.1:8000/docs

Pydantic response models, so the generated docs are real documentation rather than a shape
guess. Every endpoint is a SQL query — there is no model anywhere in this file.
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from api import db
from api.matching import rank
from ingest.normalize import display_skills

RUNS = Path(__file__).resolve().parent.parent / "evals" / "runs.jsonl"


class Job(BaseModel):
    comment_id: int
    company: str | None = None
    location: str | None = None
    remote: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_period: str | None = None
    seniority: str | None = None
    skills: list[str] = []
    thread_month: str


class TrendPoint(BaseModel):
    thread_month: str
    skill: str
    postings: int
    share: float = Field(description="fraction of that month's postings mentioning the skill")


class MatchRequest(BaseModel):
    resume: str = Field(min_length=20, description="plain text resume or skills summary")
    limit: int = Field(default=10, ge=1, le=50)


class MatchResponse(BaseModel):
    matched_skills_in_resume: list[str]
    matches: list[dict]
    note: str = (
        "Ranking is IDF-weighted set overlap computed in SQL and Python. No model is involved "
        "in selecting or ordering these results."
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Pull the Parquet to local disk once, at startup, instead of on the first request.
    try:
        db.warm()
    except FileNotFoundError:
        pass  # let /health report it rather than refusing to boot
    yield


app = FastAPI(
    title="hn-hiring-eval",
    description="Structured job data from HN 'Who is hiring' threads, with its eval harness.",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict:
    try:
        n = db.query("SELECT count(*) AS n FROM postings")[0]["n"]
        return {"status": "ok", "postings": n, "source": db.source_uri()}
    except (FileNotFoundError, Exception) as exc:  # noqa: BLE001
        return {"status": "degraded", "reason": str(exc), "source": db.source_uri()}


@app.get("/api/jobs", response_model=list[Job])
def jobs(
    month: str | None = Query(None, description="YYYY-MM. omit for the current thread"),
    skill: str | None = Query(None, description="canonical skill name"),
    remote: str | None = Query(None, pattern="^(remote|hybrid|onsite)$"),
    min_salary: int | None = Query(None, ge=0),
    limit: int = Query(50, ge=1, le=500),
):
    """Current thread by default.

    'Currently hiring' means the latest thread only — a listing spanning every thread would
    show roles filled months ago. That distinction is a correctness property, not a filter.
    """
    where, params = [], []
    if month:
        where.append("thread_month = ?")
        params.append(month)
    else:
        where.append("thread_month = (SELECT max(thread_month) FROM postings)")
    if skill:
        where.append("list_contains(skills, ?)")
        params.append(skill)
    if remote:
        where.append("remote = ?")
        params.append(remote)
    if min_salary is not None:
        where.append("salary_min >= ?")
        params.append(min_salary)

    sql = f"""
        SELECT comment_id, company, location, remote, salary_min, salary_max,
               salary_period, seniority, skills, thread_month
        FROM postings WHERE {" AND ".join(where)}
        ORDER BY salary_max DESC NULLS LAST, comment_id
        LIMIT ?
    """
    return db.query(sql, [*params, limit])


@app.get("/api/trends", response_model=list[TrendPoint])
def trends(
    skills: str = Query("Python,TypeScript,Kubernetes,Terraform", description="comma separated"),
    limit_months: int = Query(24, ge=1, le=120),
):
    """Skill demand by month, as a share of that month's postings.

    Raw counts would track thread size rather than demand — a bigger thread would look like
    rising demand for everything.
    """
    wanted = [s.strip() for s in skills.split(",") if s.strip()]
    if not wanted:
        raise HTTPException(400, "no skills given")

    rows = db.query(
        """
        SELECT thread_month, unnest(skills) AS skill, count(*) OVER (PARTITION BY thread_month) AS _
        FROM postings
        """
    )
    totals = {
        r["thread_month"]: r["n"]
        for r in db.query("SELECT thread_month, count(*) AS n FROM postings GROUP BY 1")
    }

    counts: dict[tuple[str, str], int] = {}
    for r in rows:
        key = (r["thread_month"], r["skill"])
        if r["skill"] in wanted:
            counts[key] = counts.get(key, 0) + 1

    out = [
        TrendPoint(
            thread_month=month,
            skill=skill,
            postings=n,
            share=round(n / totals[month], 4) if totals.get(month) else 0.0,
        )
        for (month, skill), n in counts.items()
    ]
    out.sort(key=lambda t: (t.thread_month, t.skill))
    months = sorted({t.thread_month for t in out})[-limit_months:]
    return [t for t in out if t.thread_month in months]


@app.post("/api/match", response_model=MatchResponse)
def match(req: MatchRequest):
    """Resume in, ranked matches and skill gaps out. Deterministic."""
    from api.matching import skills_in

    postings = db.query(
        """
        SELECT comment_id, company, skills, salary_min, salary_max
        FROM postings WHERE thread_month = (SELECT max(thread_month) FROM postings)
        """
    )
    ranked = rank(req.resume, postings, limit=req.limit)
    return MatchResponse(
        matched_skills_in_resume=display_skills(skills_in(req.resume)),
        matches=[m.to_dict() for m in ranked],
    )


@app.get("/api/evals")
def evals():
    """Every eval run recorded so far. This is what the /evals page renders.

    Published deliberately. Most projects bury their evaluation in a README; making it an
    endpoint means the numbers are as inspectable as the product.
    """
    if not RUNS.exists():
        return {"runs": [], "note": "no runs yet — uv run evals/run.py --config rules"}
    runs = [json.loads(line) for line in RUNS.read_text().splitlines() if line.strip()]
    return {"runs": runs, "n": len(runs)}
