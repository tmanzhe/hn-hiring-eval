# hn-hiring-eval

Scrapes HN "Who is hiring" threads and turns each posting into a structured row.

Honestly the extractor is the boring part. I built it so I'd have something real to point an
eval harness at: a labeled set, a scorer per field, a tally of what breaks and how often, and a
cost vs quality table with actual error bars. That harness is the thing I care about.

## Where it's at

The whole pipeline runs end to end. It pulls 1,995 postings across six monthly threads, runs a
rules parser over them, normalizes, and writes Parquet. A FastAPI service reads that Parquet
through embedded DuckDB. On the eval side there are scorers for every field, a stratified
sampler, and a labeling tool that deliberately hides the parser's output from whoever's
labeling. The configs go from A (rules only) up to E, plus a W rung for the agent workflow.
`uv run agent/demo.py` runs the real agent graph against a scripted model, so you can poke at it
without an API key. 288 tests, CI is green.

80 posts are labeled and the rules baseline is scored. The LLM configs haven't been run yet
because they need an API key, so the cost vs quality table only has the free rung in it so far.

## How I score things

Every field prediction gets bucketed four ways:

- extracted: it's right
- abstained: it's null and the label is null too, which counts as a win
- missed: it's null but the post actually says something
- hallucinated: it made up a value the post doesn't support

Hallucination rate gets its own line and never gets averaged into accuracy. A field that's 90%
right and 5% made up is a very different beast from one that's 90% right and 10% blank, and one
blended number would hide that.

Every proportion ships with a 95% Wilson interval (`evals/scorers.py`). The usual normal
approximation falls apart at n=40 when p is close to 1. It'll happily give you an interval that
goes past 100%, and that's exactly where these numbers live. If two configs are closer than
their intervals, I call it noise and move on.

## Eval results, rules baseline

80 labeled posts, split 53 dev / 27 held-out. I tuned against dev only. Held-out got looked at
twice, once before the fix and once after, and that's it.

| Field      | Dev (n=53)            | Held-out (n=27)       | Halluc, held-out |
| ---------- | --------------------- | --------------------- | ---------------: |
| company    | 89.2% (75 to 96)      | 78.3% (58 to 90)      |             0.0% |
| salary     | 100% (61 to 100)      | 88.9% (56 to 98)      |             3.7% |
| location   | 82.1% (64 to 92)      | 70.6% (47 to 87)      |             3.7% |
| skills F1  | 0.718                 | 0.671                 |                  |
| remote     | 88.7% accuracy        | 88.9% accuracy        |                  |
| seniority  | 71.7% accuracy        | 70.4% accuracy        |                  |

Precision with 95% Wilson intervals in brackets. Precision here means "when it answered, was it
right", and coverage is tracked separately in `evals/runs.jsonl`. The rules pass takes about a
millisecond a post and costs nothing.

The big move was location. At baseline it was 8.1% precise on dev and 17.4% on held-out, with 9
to 15% of answers made up. Bucketing the misses showed 33 of 43 were one bug: the parser was
copying `Hybrid in Seattle, WA` and `REMOTE (US)` straight into the location column. Stripping
the work arrangement out took it to 82% on dev and 71% on held-out, and cut location
hallucination to 2 to 4%. The full breakdown by cause is in `evals/FAILURES.md`.

What's left is mostly posts without a pipe header, where the company and place only show up in
prose. Regex can't do anything with those, which is exactly the case the LLM fallback is for.

CI runs the parser over all 80 posts (`tests/test_eval_gate.py`) and fails the build if
precision drops below a floor or hallucination goes over a ceiling. I checked it bites: turning
the location fix off fails it.

**About the labels.** Claude drafted all 80 from the raw post text, never seeing parser output,
following the rules in `evals/ANNOTATION.md`. I checked every one against the post. The LLM
rungs also run on Claude, so a Claude draft could go easy on them. When those runs happen I'll
look at the disagreements before trusting any gap.

## Other numbers

**Power analysis, done before labeling anything.** `evals/sample.py --report` tells you how
tight each slice's interval will be at an assumed 80% accuracy, before you sink hours into
labeling. A plain proportional draw of 60 posts came out like this:

| Slice          |  n | ± at 80% | Verdict        |
| -------------- | -: | -------: | -------------- |
| format: pipe   | 52 |      11% | usable         |
| format: prose  |  8 |      26% | too small      |
| has salary     | 17 |      17% | weak           |
| length: long   | 24 |      16% | weak           |

That prose row was a problem. Prose posts are where regex gives up and the LLM fallback kicks
in, so prose vs pipe is the comparison the whole cost argument leans on. With 8 posts and ±26
points you can't tell 60% from 90%. So I bumped it to n=80 and oversampled prose to 20 (seed
20260801, 53 dev / 27 held-out):

| Slice          |  n | ± at 80% | Verdict               |
| -------------- | -: | -------: | --------------------- |
| format: pipe   | 60 |      10% | usable                |
| format: prose  | 20 |      17% | weak, big gaps only   |
| has salary     | 15 |      19% | weak, big gaps only   |
| length: long   | 29 |      14% | usable                |
| length: short  | 51 |      11% | usable                |

Since the sample isn't proportional anymore, the headline number has to be a weighted estimate,
not a straight mean. Per-slice numbers are fine as is. Salary is still weak and I'm leaving it
that way. I'd rather say "weak" out loud than keep growing the sample.

**DuckDB vs Spark on the `/api/trends` query.** I kept hearing "just use Spark", so I measured
it. Same Parquet on both, corpus copied up to 100M rows, `local[*]` Spark, median of three runs
on my laptop (`bench/`, `docs/scaling.md`):

| Rows        | DuckDB   | Spark (warm) | Spark / DuckDB |
| ----------- | -------: | -----------: | -------------: |
| 1,995       |   4.3 ms |     113.6 ms |          26.4x |
| 1,995,000   |  18.3 ms |     165.2 ms |           9.0x |
| 99,750,000  | 338.6 ms |   1,081.9 ms |           3.2x |

On top of that, Spark takes 2.1s just to start a session. The gap shrinks as the data grows but
DuckDB wins at every size I tried. What would actually flip it is the data no longer fitting on
one box. Row count alone doesn't.

## What's where

| Path         | What's in it                                                          |
| ------------ | --------------------------------------------------------------------- |
| `ingest/`    | fetch, rules parser, LLM fallback, normalize, write Parquet           |
| `evals/`     | `labeled.jsonl`, scorers, `run.py`, `runs.jsonl`, `ANNOTATION.md`     |
| `api/`       | FastAPI over DuckDB. `/api/jobs` `/api/trends` `/api/match`           |
| `web/`       | Next.js. jobs browser, trends, resume match, evals page               |
| `terraform/` | GCS bucket, Artifact Registry, two Cloud Run services, Job, Scheduler |
| `docs/`      | `formats.md`, the format taxonomy the schema comes from               |
| `data/`      | gitignored, rebuildable from the public API                          |

## Three loops, and only one of them has a user waiting

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

SQL and Python handle all the counting, ranking and aggregating. The model reads your resume and
writes the closing summary, and that's all it gets to do. Ask an LLM how many jobs want
Terraform and it'll confidently hand you a number that looks right and isn't, so nothing in the
request path lets it.

## Running it

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

What's on disk right now: 6 threads, Feb to Jul 2026, 1,995 postings.
