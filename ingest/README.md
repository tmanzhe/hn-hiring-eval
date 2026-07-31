# ingest

Runs monthly as a Cloud Run Job. Fetches, extracts, writes Parquet, exits. Nobody waits on it.

```
HN Algolia API
      │
      ▼
  fetch.py ──► data/raw/<thread_id>.json        raw, unparsed, never refetched
      │
      ▼
  rules.py ────────────────┐                    the easy majority, free
      │                    │
      └──► llm.py ─────────┤                    prose, odd formats, multi-role
                           ▼
              normalize.py ──► Parquet ──► GCS
```

| File | Stage | Status |
| --- | --- | --- |
| `fetch.py` | Algolia → raw JSON on disk | done |
| `corpus.py` | reading what's in `data/raw/` | done |
| `schema.py` | `Extraction` (what the model returns) and `Posting` (the row) | draft |
| `rules_poc.py` | crude two-field regex pass, prints only | throwaway, becomes `rules.py` |
| `rules.py` | deterministic parser against the schema | done |
| `llm.py` | `extract(text, model) -> Extraction`, batched | not built |
| `normalize.py` | skill synonyms, salary units, currency | done |
| `pipeline.py` | run rules over the corpus, report coverage, write Parquet | done |
| `tally.py` | interactive format tallier for step 03 | done |

Two rules this directory follows:

**Fetch and parse are separate stages.** The parser gets rewritten many times; the API gets hit
once. Raw JSON goes to disk untouched so every later stage is testable offline against a fixed
input, and so a different snapshot can't land mid-project and invalidate labels.

**Rules run before the model.** Whatever regex handles is work not worth paying for. The LLM only
sees what defeats it, and `extracted_by` records which path produced each row so the two can be
scored separately.
