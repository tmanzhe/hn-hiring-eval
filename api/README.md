# api

FastAPI over DuckDB. One Cloud Run service.

```sh
uv run uvicorn api.main:app --reload
open http://127.0.0.1:8000/docs
```

| Endpoint | Returns |
| --- | --- |
| `GET /api/jobs` | list + filter, latest thread only |
| `GET /api/trends` | skill demand by month, across all threads |
| `POST /api/match` | resume in, IDF-ranked matches + skill gaps out |
| `GET /api/evals` | `runs.jsonl`, for the public evals page |

DuckDB is embedded — a library inside this process, not a server. It queries the Parquet file
directly, so there's no database to operate or back up.

Two things to get right here:

**Cold starts.** Cloud Run scales to zero, so every cold start would re-read Parquet over
`httpfs`. Pull it to `/tmp` on startup or bake it into the image.

**No model in the counting.** `/match` does retrieval, IDF weighting and ranking in SQL and
Python. The model reads the resume and writes the closing summary; that's all. Ask a model to
count how many jobs want Terraform and it invents a plausible number, so nothing in the request
path lets it.

## Container

```sh
docker build -f api/Dockerfile -t hn-api .
docker run --rm -p 8000:8000 \
  -v "$PWD/data:/data:ro" -e PARQUET_URI=/data/postings.parquet hn-api
```

Build context is the repo root because the API imports the schema, normalizer and skill
vocabulary from `ingest/` — one system, not two.

Two things that bit me and are worth not re-learning:

**A venv can't be copied to a different path.** Console scripts bake an absolute interpreter
path at install time, so a venv built in `/build` and copied to `/app` leaves `uvicorn` pointing
at a python that doesn't exist — the container exits 127 with `uvicorn: not found`. Fixed by
building at the same path it runs at, and by invoking `python -m uvicorn` rather than the shim.

**`$PORT` has to be expanded at runtime** for Cloud Run, which means shell-form `CMD`. `exec`
keeps uvicorn as PID 1 so SIGTERM reaches it and the container stops cleanly instead of being
killed after the grace period.
