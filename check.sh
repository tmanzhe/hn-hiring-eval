#!/usr/bin/env bash
# Everything CI runs, locally, before pushing.
#
# The reason this exists: `data/` is gitignored, so a test that reads the real corpus passes on
# my machine and fails on a runner that has never fetched anything. That happened — 16 tests,
# two red builds. A local run that doesn't reproduce CI's environment isn't a check.
#
#   ./check.sh          lint + tests + the no-corpus simulation
#   ./check.sh --docker  also build the image and curl the container

set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"

step() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

# Sync the exact extras CI installs. Skipping this once meant a test that imports langchain
# passed locally (where I'd installed the agent extra by hand) and failed in CI on import.
step "sync deps, same extras as CI"
uv sync --quiet --extra dev --extra agent

step "lint"
uv run ruff check .

step "tests"
uv run pytest -q

step "tests without data/ — this is what CI actually sees"
hidden=""
if [ -d data/raw ]; then
  hidden="$(mktemp -d)/raw"
  mv data/raw "$hidden"
  # shellcheck disable=SC2064
  trap "mv '$hidden' data/raw" EXIT
fi
uv run pytest -q

step "pipeline against the committed fixture"
HN_RAW_DIR=tests/fixtures uv run ingest/pipeline.py --coverage
HN_RAW_DIR=tests/fixtures uv run ingest/pipeline.py >/dev/null
test -f tests/postings.parquet
rm -f tests/postings.parquet tests/needs_llm.json
echo "pipeline produced Parquet"

if [ "${1:-}" = "--docker" ]; then
  step "container"
  docker build -q -f api/Dockerfile -t hn-api-check . >/dev/null
  docker rm -f hn-api-check >/dev/null 2>&1 || true
  HN_RAW_DIR=tests/fixtures uv run ingest/pipeline.py >/dev/null
  mkdir -p .check-data && mv tests/postings.parquet .check-data/postings.parquet
  docker run -d --name hn-api-check -p 8901:8000 \
    -v "$PWD/.check-data:/data:ro" -e PARQUET_URI=/data/postings.parquet hn-api-check >/dev/null
  for _ in $(seq 30); do curl -sf localhost:8901/health >/dev/null && break; sleep 2; done
  curl -sf localhost:8901/health | grep -q '"status":"ok"'
  docker rm -f hn-api-check >/dev/null
  rm -rf .check-data tests/needs_llm.json
  echo "container serves"
fi

printf '\n\033[1;32mall green\033[0m\n'
