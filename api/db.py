"""DuckDB over Parquet. A library inside this process, not a server.

Step 23's trap: Cloud Run scales to zero, so on a cold start every request would re-read the
Parquet file over httpfs — that's the slowest, ugliest request in the system and the one a
reviewer will ask about. Fixed by pulling the file to local disk once at startup and querying
that. `warm()` is idempotent, so the second worker to call it pays nothing.

Read-only by construction. Nothing in here writes.
"""

import os
import shutil
import threading
from pathlib import Path

import duckdb

REPO = Path(__file__).resolve().parent.parent
DEFAULT_PARQUET = REPO / "data" / "postings.parquet"
# Cloud Run gives every instance a writable /tmp backed by memory.
LOCAL_CACHE = Path(os.environ.get("PARQUET_CACHE", "/tmp/postings.parquet"))

_lock = threading.Lock()
_conn: duckdb.DuckDBPyConnection | None = None
_path: Path | None = None


def source_uri() -> str:
    """Where the Parquet lives. gs:// in production, a local file in development."""
    return os.environ.get("PARQUET_URI", str(DEFAULT_PARQUET))


def warm(force: bool = False) -> Path:
    """Make the Parquet available on local disk. Safe to call from every worker."""
    global _path
    with _lock:
        if _path is not None and not force:
            return _path

        uri = source_uri()
        if uri.startswith(("gs://", "s3://", "http://", "https://")):
            # Pulled once here rather than on every query. Left unhandled this is the cold-start
            # problem the plan calls out.
            LOCAL_CACHE.parent.mkdir(parents=True, exist_ok=True)
            duckdb.connect().execute(
                f"COPY (SELECT * FROM read_parquet('{uri}')) TO '{LOCAL_CACHE}' (FORMAT PARQUET)"
            )
            _path = LOCAL_CACHE
        else:
            local = Path(uri)
            if not local.exists():
                raise FileNotFoundError(
                    f"{local} not found. run: uv run ingest/pipeline.py"
                )
            if LOCAL_CACHE.parent.exists() and local != LOCAL_CACHE:
                shutil.copyfile(local, LOCAL_CACHE)
                _path = LOCAL_CACHE
            else:
                _path = local
        return _path


def connect() -> duckdb.DuckDBPyConnection:
    """One connection per process, reused. DuckDB is embedded, so this is a library handle."""
    global _conn
    with _lock:
        if _conn is None:
            _conn = duckdb.connect(database=":memory:")
        return _conn


def query(sql: str, params: list | None = None) -> list[dict]:
    """Run read-only SQL against the Parquet and return plain dicts.

    `postings` is registered as a view over the file, so callers write ordinary SQL and never
    interpolate a path. Parameters are bound, never formatted into the string.
    """
    path = warm()
    conn = connect()
    conn.execute(f"CREATE OR REPLACE VIEW postings AS SELECT * FROM read_parquet('{path}')")
    result = conn.execute(sql, params or [])
    columns = [d[0] for d in result.description]
    return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]


def reset() -> None:
    """Drop cached state. Tests only."""
    global _conn, _path
    with _lock:
        _conn = None
        _path = None
