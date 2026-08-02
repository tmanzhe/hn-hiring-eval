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
