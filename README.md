# hn-hiring-eval

Pulls job postings out of HN "Who is hiring" threads and turns them into structured rows.

The extractor is the excuse. What I actually want is the eval harness around it: a labeled set,
a scorer per field, a count of what breaks and how often, and a cost/quality table with real
error bars on it.

## Status

The harness is built. Nothing is scored yet.

What runs today: fetch and the rules parser over a 1,995-posting corpus, normalization and the
Parquet write, per-field scorers that sort every prediction into extracted, abstained, missed or
hallucinated, a stratified sampler that runs a power analysis per slice before any labeling, a
resumable labeling tool that never shows the annotator parser output, the FastAPI service over
DuckDB, and the A to E config ladder plus a W workflow rung. `uv run agent/demo.py` drives the
real graph against a scripted model, so it runs with no API key. 266 tests, green in CI.

What does not exist yet: `evals/labeled.jsonl` and `evals/runs.jsonl`. The 60 posts are not
labeled, so there is no accuracy, cost or hallucination number here. The coverage percentages
`check.sh` prints say how often the rules pass produced a value, not whether that value was
right.

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

```sh
uv run ingest/fetch.py --months 6   # writes data/raw/<thread_id>.json
uv run ingest/dump.py -n 20         # prints posts to read
uv run ingest/rules_poc.py -n 20    # crude regex pass, coverage only
uv run evals/score_poc.py           # scores rules against evals/poc_labels.jsonl
```

Corpus on disk: 6 threads, Feb–Jul 2026, 1,995 postings.

## Limitations

Written at step 34, from whatever the evals actually show.
