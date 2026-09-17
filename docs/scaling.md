# Where each decision flips

Every tool below is the right answer to *some* problem. None of them are the right answer to
this one, yet. This file records the specific condition that would change each verdict, because
"we'd use Kafka if we scaled" is not an engineering position — knowing the threshold is.

## Current state

| | |
| --- | --- |
| Volume | ~2,000 postings per monthly thread, ~24k/year |
| Arrival | one batch, 12× a year, triggered by cron |
| Writers | one |
| Consumers | one |
| Working set | ~200 MB of text |
| Stack | Parquet on GCS, embedded DuckDB, Cloud Run Job + Scheduler |

## Keep the layers straight

Three separate things that get conflated:

- **Data organisation** — bronze / silver / gold. How raw and refined data are separated.
- **Storage format** — Parquet, Iceberg, Delta. How bytes sit on disk.
- **Query engine** — DuckDB, Spark, Trino, BigQuery. What reads those bytes.

Changing the engine does not move the data. DuckDB → Trino is a client swap against the same
Parquet files. That's why the engine choice here is cheap to revisit and the format choice is not.

## The thresholds

| Condition that becomes true | Add | Why not now |
| --- | --- | --- |
| Postings arrive **continuously**, or **2+ independent consumers** need the same feed, or replay-from-offset is required | **Pub/Sub** (managed; Kafka only if self-hosting is a requirement) | Data arrives 12× a year to one consumer. Replay already exists — raw JSON on disk, never refetched. A broker would add an operational component that solves nothing currently true. |
| **Concurrent writers** need atomic commits, or the schema evolves without rewriting history, or snapshot isolation / time travel matter | **Iceberg** | One writer, once a month. Atomic commits solve contention that cannot occur with a single serialised writer. |
| The **working set exceeds one machine**, or a single query needs distributed shuffle | **Spark** | ~200 MB, and single-node Spark measured 3.2x to 26x slower than DuckDB across every scale tried. See the table below. |
| **Concurrent analytical users** in the tens, or a shared semantic layer is needed | **BigQuery / Trino** | One API process, embedded DuckDB, sub-100ms. A warehouse adds cost and a network hop to serve one reader. |
| Query patterns need **sub-second point lookups by key** at high QPS | a real OLTP store | Analytical scans over a columnar file are the access pattern; there are no point lookups. |

## Measured, not assumed

`uv run --with pyspark bench/engines.py` runs the `/api/trends` aggregation on both engines over
the same Parquet: explode the skills array, group by month and skill, count. The real corpus is
replicated to reach each row count, comment ids kept unique. Median of three runs.

| Rows | Parquet | DuckDB | Spark (warm) | Spark / DuckDB |
| --- | --- | --- | --- | --- |
| 1,995 | 0.1 MB | 4.3 ms | 113.6 ms | 26.4x |
| 199,500 | 1.3 MB | 10.4 ms | 114.0 ms | 11.0x |
| 1,995,000 | 12.6 MB | 18.3 ms | 165.2 ms | 9.0x |
| 9,975,000 | 59.5 MB | 43.9 ms | 242.3 ms | 5.5x |
| 49,875,000 | 293.7 MB | 174.3 ms | 585.8 ms | 3.4x |
| 99,750,000 | 587.5 MB | 338.6 ms | 1081.9 ms | 3.2x |

Spark session startup was 2130 ms on top of every figure in that column. A scheduled job pays
that once per run; a long-lived cluster pays it once.

DuckDB won at every scale, and the ratio narrowed from 26.4x to 3.2x rather than crossing over.

The result is less interesting than why it happens. This is `local[*]` Spark: one machine, so it
pays for shuffle, serialisation and task scheduling while getting none of the distribution those
costs buy. Running it single-node and calling that a fair fight would be the wrong read. What the
table actually shows is that the trigger for Spark is not a row count at all. At 100M rows and
588 MB this workload still fits comfortably on one box, and as long as that is true, adding a
cluster adds coordination cost and removes nothing.

That is the threshold in the row above, stated precisely: the working set no longer fitting on one
machine. Not volume. A number I can point at beats an opinion about Spark, which is the entire
reason this file exists.

## Axes, not a ladder

These are independent. Real combinations:

- 10M rows, one monthly writer, one consumer → **still Parquet**, just partitioned better
- Continuous arrival, one consumer → **broker, no Iceberg**
- Nightly batch, five writers → **Iceberg, no broker**
- Big working set, one writer → **Spark, neither of the others**

Volume alone triggers none of them. Arrival pattern, writer concurrency, and working-set size
are what move each decision, and they move independently.

## Multi-source is not a broker trigger

Adding Reddit, RemoteOK or Wellfound means more batch jobs writing files into the same place —
fan-in with a common schema, not a stream. What it actually needs:

1. a source adapter interface (`fetch() -> list[RawPost]`)
2. a `source` column on `Posting` — cheap now, requires relabelling later
3. source-specific rules, since the pipe-delimited convention is an HN habit and nothing else
   shares it

The payoff is in the eval, not the infrastructure: per-source slices show exactly where
deterministic parsing stops working and a model starts earning its cost.

## What this table is for

Excluding a tool because it wasn't considered and excluding it after locating the line where it
becomes correct are different things, and only one of them survives a follow-up question. The
honest framing: *"I left Spark and Iceberg out because at this size they cost more than they
return — here's the row count where that flips."*
