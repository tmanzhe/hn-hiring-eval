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
| The **working set exceeds one machine**, or a single query needs distributed shuffle | **Spark** | ~200 MB. JVM startup and shuffle overhead make Spark measurably *slower* at this size — see the timing in step 36. |
| **Concurrent analytical users** in the tens, or a shared semantic layer is needed | **BigQuery / Trino** | One API process, embedded DuckDB, sub-100ms. A warehouse adds cost and a network hop to serve one reader. |
| Query patterns need **sub-second point lookups by key** at high QPS | a real OLTP store | Analytical scans over a columnar file are the access pattern; there are no point lookups. |

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
