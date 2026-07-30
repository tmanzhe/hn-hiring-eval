# hn-hiring-eval

Pulls job postings out of HN "Who is hiring" threads and turns them into structured rows.

The extractor is the excuse. What I actually want is the eval harness around it: a labeled set,
a scorer per field, a count of what breaks and how often, and a cost/quality table with real
error bars on it.

## Status

Scaffolded. Nothing measured yet. Checklist is in `PLAN.md`.

Numbers in this README get filled in from `evals/runs.jsonl` at step 34. They stay empty until
then. A placeholder number is worse than no number.

## Layout

| Path         | What's in it                                                          |
| ------------ | --------------------------------------------------------------------- |
| `ingest/`    | fetch, rules parser, LLM fallback, normalize, write Parquet           |
| `evals/`     | `labeled.jsonl`, scorers, `run.py`, `runs.jsonl`, `ANNOTATION.md`     |
| `api/`       | FastAPI over DuckDB. `/api/jobs` `/api/trends` `/api/match`           |
| `web/`       | Next.js. jobs browser, trends, resume match, evals page               |
| `terraform/` | GCS bucket, Artifact Registry, two Cloud Run services, Job, Scheduler |
| `docs/`      | `formats.md`, the format taxonomy the schema comes from               |
| `data/`      | gitignored, rebuildable from the public API                          |

## Three loops, one of which a user waits on

```
INGEST — monthly, offline
   HN Algolia API
         │   thread + top-level comments
         ▼
   Cloud Run Job ──► rules parser ─────┐   easy majority, free
         │                             │
         └────────► LLM fallback ──────┤   prose, odd formats, multi-role
                                       ▼
                          normalize ──► Parquet ──► GCS

SERVE — per request
   Next.js (Cloud Run) ──HTTP──► FastAPI (Cloud Run)
                                     │  /api/jobs /api/trends /api/match /api/evals
                                     ▼
                          DuckDB in-process ──► Parquet in /tmp ◄── GCS on cold start

EVAL — offline, on demand and in CI
   labeled.jsonl ──► run.py ──► scorers ──► runs.jsonl ──► /evals page
```

Counting, ranking and aggregating are SQL and Python. The model reads the resume and writes the
closing summary. That's all it does. Ask a model to count how many jobs want Terraform and it
makes up a number that looks right, so nothing in the request path lets it.

## Setup

```sh
uv sync                  # curl -LsSf https://astral.sh/uv/install.sh | sh
cp .env.example .env     # add ANTHROPIC_API_KEY
```

The two POC scripts under `ingest/` use stdlib only, so they run before `uv sync` does.

```sh
python3 ingest/fetch.py          # writes data/raw/<thread_id>.json
python3 ingest/dump.py -n 20     # prints posts to read
```

## Limitations

Written at step 34, from whatever the evals actually show.
