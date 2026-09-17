# bench

One question: is the claim in `docs/scaling.md` true, or did I just repeat something I read?

    uv run --with pyspark bench/engines.py                 # all six scales, a few minutes
    uv run --with pyspark bench/engines.py --scales 1 100  # quick

`engines.py` runs the `/api/trends` aggregation on DuckDB and on Spark over identical Parquet,
replicating the real corpus up to 100M rows. Results land in `results.json` and the table in
`docs/scaling.md` is generated from them.

pyspark is deliberately not a project dependency. It is 300 MB to answer a question that gets
asked once, so it comes in through `--with` and leaves again.

Two honest limits on what this measures:

- It is `local[*]` Spark. Single-node Spark pays for coordination it cannot use, so DuckDB
  winning here is expected, not a surprise finding. The useful output is the *shape* of the
  ratio as rows grow, and where it stops shrinking.
- Times are medians of three runs on one laptop with a warm page cache. They are good enough to
  separate 4 ms from 1,100 ms. They are not good enough to argue about 10%.
