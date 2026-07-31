"""Smoke tests that actually invoke the CLI scripts as subprocesses.

test_pipeline.py exercises the parse → normalize → Parquet chain by calling the functions. That
leaves a hole: if `pipeline.py`'s own main() breaks — a bad argparse flag, a bad import, a
crash in the report — every other test still passes. These run the real thing.

HN_RAW_DIR points the scripts at tests/fixtures, so there's no network and no data/ dependency.
"""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


def run(script, *args, **kwargs):
    return subprocess.run(
        [sys.executable, str(ROOT / script), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        env={**kwargs.pop("env", {}), "HN_RAW_DIR": str(FIXTURES), "PATH": ""},
        timeout=120,
        check=False,
    )


class TestPipeline:
    def test_coverage_runs_and_reports(self):
        r = run("ingest/pipeline.py", "--coverage")
        assert r.returncode == 0, r.stderr
        assert "postings across" in r.stdout
        assert "fully handled by rules" in r.stdout

    def test_coverage_writes_nothing(self, tmp_path):
        before = set(FIXTURES.iterdir())
        run("ingest/pipeline.py", "--coverage")
        assert set(FIXTURES.iterdir()) == before, "--coverage must not write files"

    def test_full_run_writes_parquet(self):
        r = run("ingest/pipeline.py")
        assert r.returncode == 0, r.stderr
        out = FIXTURES.parent / "postings.parquet"
        try:
            assert out.exists(), "pipeline did not write Parquet"
            assert "wrote" in r.stdout
        finally:
            out.unlink(missing_ok=True)
            (FIXTURES.parent / "needs_llm.json").unlink(missing_ok=True)

    def test_coverage_never_exceeds_total(self):
        """A percentage over 100 means posts are being counted twice somewhere."""
        r = run("ingest/pipeline.py", "--coverage")
        for line in r.stdout.splitlines():
            if "%" in line:
                pct = float(line.split("%")[0].split()[-1])
                assert 0 <= pct <= 100, line


class TestOtherScripts:
    def test_dump_prints_posts(self):
        r = run("ingest/dump.py", "-n", "2")
        assert r.returncode == 0, r.stderr
        assert "id=" in r.stdout

    def test_dump_by_id(self):
        r = run("ingest/dump.py", "--ids", "48915735")
        assert r.returncode == 0, r.stderr
        assert "48915735" in r.stdout

    def test_dump_unknown_id_fails_loudly(self):
        """Silently scoring the wrong posts is worse than an error."""
        r = run("ingest/dump.py", "--ids", "does-not-exist")
        assert r.returncode != 0
        assert "not in" in (r.stdout + r.stderr)

    def test_rules_poc_still_runs(self):
        r = run("ingest/rules_poc.py", "-n", "3")
        assert r.returncode == 0, r.stderr
        assert "coverage, not accuracy" in r.stdout

    def test_score_poc_refuses_without_labels(self):
        """P4 isn't done, so this must exit non-zero with an instruction rather than pretend."""
        r = run("evals/score_poc.py")
        assert r.returncode != 0
        assert "P4" in (r.stdout + r.stderr)

    def test_tally_report_is_safe_to_rerun(self):
        r = run("ingest/tally.py", "--report")
        assert r.returncode == 0, r.stderr


@pytest.mark.parametrize(
    "script",
    ["ingest/fetch.py", "ingest/dump.py", "ingest/pipeline.py", "ingest/tally.py",
     "ingest/rules_poc.py", "evals/score_poc.py"],
)
def test_script_has_no_import_errors(script):
    """--help exercises imports and argparse without doing any work."""
    r = run(script, "--help")
    assert r.returncode == 0, f"{script} --help failed:\n{r.stderr}"
