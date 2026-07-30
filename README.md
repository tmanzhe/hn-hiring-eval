# hn-hiring-eval

Structured job data extracted from Hacker News "Who is hiring" threads.

The extractor is the substrate. **The eval harness around it is the deliverable** — a labeled
set, per-field scorers, a failure taxonomy, and a cost/quality frontier with honest error bars.

Most teams ship LLM features on vibes. This one has a labeled set, per-field metrics with
confidence intervals, and a measured answer to "is the expensive model worth it."

## Status

Scaffolded. Nothing measured yet. See `PLAN.md`.

> Every number in this README gets filled in from `evals/runs.jsonl` at step 34.
> Until then it stays empty on purpose — a placeholder number is worse than no number.

## Layout

| Path         | What lives here                                                        |
| ------------ | ---------------------------------------------------------------------- |
| `ingest/`    | Fetch → rules parser → LLM fallback → normalize → Parquet              |
| `evals/`     | `labeled.jsonl`, scorers, `run.py`, `runs.jsonl`, `ANNOTATION.md`      |
| `api/`       | FastAPI + DuckDB-over-Parquet. `/api/jobs` `/api/trends` `/api/match`  |
| `web/`       | Next.js. Jobs browser, trends, resume match, **and the evals page**    |
| `terraform/` | GCS bucket, Artifact Registry, 2 Cloud Run services, Job + Scheduler   |
| `docs/`      | `formats.md` — the hand-written format taxonomy the schema comes from  |
| `data/`      | Gitignored. Reproducible from the public API                           |

## Three loops, only one of which a user waits on

```
INGEST — monthly, offline, nobody waiting
   HN Algolia API
         │   fetch thread + top-level comments
         ▼
   Cloud Run Job ──► rules parser ─────┐   the easy majority, free
         │                             │
         └────────► LLM fallback ──────┤   prose · odd formats · multi-role
                                       ▼
                          normalize ──► Parquet ──► GCS

SERVE — per request
   Next.js (Cloud Run) ──HTTP──► FastAPI (Cloud Run)
                                     │  /api/jobs /api/trends /api/match /api/evals
                                     ▼
                          DuckDB (in-process) ──► Parquet in /tmp ◄── GCS on cold start

EVAL — offline, on demand and in CI
   labeled.jsonl ──► run.py ──► scorers ──► runs.jsonl ──► the /evals page
```

Counting, ranking and aggregating are SQL and Python. The model reads the resume and writes
the closing summary — nothing else. Ask a model to "count how many jobs want Terraform" and it
will invent a plausible number; this shape makes that impossible.

## Setup

```sh
uv sync                      # needs uv: curl -LsSf https://astral.sh/uv/install.sh | sh
cp .env.example .env         # add ANTHROPIC_API_KEY
```

## Limitations

Filled in at step 34, from what the evals actually show.
