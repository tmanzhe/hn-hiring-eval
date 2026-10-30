"""Regenerate dashboard/data/fixture-rules.json (rules output for the fixture example post).

Run from the repo root: uv run python dashboard/scripts/gen_fixture_rules.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ingest.corpus import to_text
from ingest.rules import parse

thread = json.loads(Path("tests/fixtures/sample_thread.json").read_text())
post = thread["comments"][0]
extraction, _ = parse(to_text(post["comment_text"]))
out = {"source": "tests/fixtures/sample_thread.json", "post_id": post["objectID"],
       "generated_by": "dashboard/scripts/gen_fixture_rules.py (ingest.rules.parse)",
       "extraction": extraction.model_dump(mode="json")}
Path("dashboard/data/fixture-rules.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
