"""Step 36. Where DuckDB stops winning.

docs/scaling.md claims Spark is slower than DuckDB at this size. That was an assertion. This
measures it, on the real Parquet, at four scales, with the same aggregation on both engines.

    uv run --with pyspark bench/engines.py
    uv run --with pyspark bench/engines.py --scales 1 100      # quicker

The aggregation is the /api/trends query: explode the skills array, group by month and skill,
count. It is the heaviest thing the product actually does.

Two numbers are reported for Spark because they answer different questions. Total includes
session startup, which is what a scheduled job pays every run. Query-only assumes a warm
session, which is what a long-lived cluster pays. The honest comparison depends on which one
you would actually be running, so both are here.
"""

import argparse
import json
import shutil
import statistics
import tempfile
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "postings.parquet"
OUT = ROOT / "bench" / "results.json"

DUCK_SQL = """
SELECT thread_month, skill, count(*) AS n
FROM (SELECT thread_month, unnest(skills) AS skill FROM read_parquet('{path}'))
GROUP BY 1, 2
ORDER BY n DESC
LIMIT 20
"""

REPEATS = 3


def scaled_parquet(scale: int, tmp: Path) -> Path:
    """Replicate the real corpus `scale` times, keeping comment_id unique.

    Generated with DuckDB rather than pandas so that 10M rows does not have to fit in memory
    as Python objects first.
    """
    dst = tmp / f"postings_{scale}x.parquet"
    if scale == 1:
        shutil.copy(SRC, dst)
        return dst
    duckdb.execute(
        f"""
        COPY (
            SELECT p.* REPLACE (p.comment_id + r.range * 100000000 AS comment_id)
            FROM read_parquet('{SRC}') p, range(0, {scale}) r
        ) TO '{dst}' (FORMAT parquet)
        """
    )
    return dst


def time_it(fn, repeats=REPEATS) -> float:
    """Median of n runs. Median, not mean, so one GC pause does not set the number."""
    times = []
    for _ in range(repeats):
        started = time.perf_counter()
        fn()
        times.append((time.perf_counter() - started) * 1000)
    return round(statistics.median(times), 1)


def bench_duckdb(path: Path) -> float:
    # A fresh connection each run. A reused one caches the Parquet footer and would measure
    # the second read, not the first.
    def run():
        con = duckdb.connect()
        con.execute(DUCK_SQL.format(path=path)).fetchall()
        con.close()

    return time_it(run)


def bench_spark(path: Path, spark) -> float:
    from pyspark.sql import functions as F

    def run():
        (
            spark.read.parquet(str(path))
            .select("thread_month", F.explode("skills").alias("skill"))
            .groupBy("thread_month", "skill")
            .count()
            .orderBy(F.desc("count"))
            .limit(20)
            .collect()
        )

    return time_it(run)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scales", type=int, nargs="+", default=[1, 100, 1000, 5000])
    args = ap.parse_args()

    if not SRC.exists():
        raise SystemExit(f"no corpus at {SRC}. run: uv run ingest/pipeline.py")

    from pyspark.sql import SparkSession

    started = time.perf_counter()
    spark = (
        SparkSession.builder.master("local[*]")
        .appName("bench")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    startup_ms = round((time.perf_counter() - started) * 1000, 1)
    print(f"spark session startup: {startup_ms} ms (paid once per job, not per query)\n")

    rows_per_scale = duckdb.execute(f"SELECT count(*) FROM read_parquet('{SRC}')").fetchone()[0]
    results = []

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        print(f"{'rows':>12}  {'parquet':>9}  {'duckdb':>10}  {'spark':>10}  {'spark+start':>12}")
        print("-" * 60)
        for scale in args.scales:
            path = scaled_parquet(scale, tmp)
            rows = rows_per_scale * scale
            size_mb = path.stat().st_size / 1_000_000

            duck_ms = bench_duckdb(path)
            spark_ms = bench_spark(path, spark)
            path.unlink()  # 100M rows is 600MB. Keeping every scale would need 1GB of temp.

            results.append(
                {
                    "rows": rows,
                    "parquet_mb": round(size_mb, 1),
                    "duckdb_ms": duck_ms,
                    "spark_query_ms": spark_ms,
                    "spark_total_ms": round(spark_ms + startup_ms, 1),
                    "ratio_query_only": round(spark_ms / duck_ms, 1),
                }
            )
            print(
                f"{rows:>12,}  {size_mb:>7.1f}MB  {duck_ms:>8.1f}ms  {spark_ms:>8.1f}ms  "
                f"{spark_ms + startup_ms:>10.1f}ms"
            )

    spark.stop()

    OUT.write_text(json.dumps({"startup_ms": startup_ms, "scales": results}, indent=2) + "\n")
    print(f"\nwrote {OUT.relative_to(ROOT)}")

    crossover = [r for r in results if r["ratio_query_only"] < 1]
    if crossover:
        print(f"spark wins on query time from {min(r['rows'] for r in crossover):,} rows up")
    else:
        print(
            "duckdb ahead at every scale measured.\n"
            "this is local[*] spark, one machine. that is the point: single-node spark pays\n"
            "shuffle and serialisation costs for parallelism it cannot use. the threshold that\n"
            "matters is not a row count, it is whether the working set still fits on one box."
        )


if __name__ == "__main__":
    main()
