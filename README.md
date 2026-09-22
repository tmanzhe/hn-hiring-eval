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

What does not exist yet: `evals/labeled.jsonl` and `evals/runs.jsonl`. The 80 sampled posts are
not labeled, so there is no accuracy, cost or hallucination number here. The coverage percentages
`check.sh` prints say how often the rules pass produced a value, not whether that value was
right.

Extraction numbers get filled in from `evals/runs.jsonl` at step 34. They stay empty until
then. A placeholder number is worse than no number.

## How it gets measured

Every field prediction lands in one of four buckets: extracted (right), abstained (null when the
label is null), missed (null when the label has a value) or hallucinated (a value the post does
not support). Hallucination rate is reported on its own line. It never gets averaged into an
accuracy number, because a field that is 90% right and 5% invented is a different thing from
one that is 90% right and 10% blank.

Every proportion comes with a 95% Wilson interval (`evals/scorers.py`). At n=40 and p near 1 the
normal approximation runs past 100%, which is the regime this project lives in. If two configs
differ by less than the interval, the difference is noise and the table says so.

## Measured so far

These two come from code that already runs. Neither is an extraction score.

**Power analysis, before labeling.** `evals/sample.py --report` works out what each slice can
support at an assumed 80% accuracy before any post is labeled. A proportional draw of 60 from
the 1,995-post corpus looked like this:

| Slice          |  n | ± at 80% | Verdict        |
| -------------- | -: | -------: | -------------- |
| format: pipe   | 52 |      11% | usable         |
| format: prose  |  8 |      26% | too small      |
| has salary     | 17 |      17% | weak           |
| length: long   | 24 |      16% | weak           |

Prose posts are where the rules parser gives up and the LLM fallback takes over, so prose vs
pipe is the comparison the cost argument depends on. Eight posts and ±26 points cannot tell 60%
from 90%. I redrew at n=80 with prose oversampled to 20 (seed 20260801, 53 dev / 27 held-out):

| Slice          |  n | ± at 80% | Verdict        |
| -------------- | -: | -------: | -------------- |
| format: pipe   | 60 |      10% | usable         |
| format: prose  | 20 |      17% | weak, large gaps only |
| has salary     | 15 |      19% | weak, large gaps only |
| length: long   | 29 |      14% | usable         |
| length: short  | 51 |      11% | usable         |

The oversampled draw is not proportional to the corpus any more, so the overall number will be a
weighted estimate, not a plain mean. Salary stays weak. I'd rather report it that way than widen
the sample again.

**DuckDB vs Spark on the `/api/trends` query.** Median of three runs on one laptop,
`local[*]` Spark, same Parquet, corpus replicated up to 100M rows (`bench/`, `docs/scaling.md`):

| Rows        | DuckDB   | Spark (warm) | Spark / DuckDB |
| ----------- | -------: | -----------: | -------------: |
| 1,995       |   4.3 ms |     113.6 ms |          26.4x |
| 1,995,000   |  18.3 ms |     165.2 ms |           9.0x |
| 99,750,000  | 338.6 ms |   1,081.9 ms |           3.2x |

Spark adds 2.1 s of session startup on top. The gap narrows as rows grow but never crosses, so
the thing that would flip this is the working set outgrowing one machine, not row count.

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
