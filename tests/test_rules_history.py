import json
from datetime import UTC, datetime

import httpx

from ingest import rules_history
from ingest.schema import Extraction


def history_row(date="2026-10-29", thread_id="123", total=0):
    return {
        "date": date,
        "thread_id": thread_id,
        "total_posts": total,
        **dict.fromkeys(rules_history.FIELDS, 0),
    }


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_counts_non_null_including_false_zero_and_empty_lists(monkeypatch):
    extractions = iter([
        Extraction(company="Acme", visa_sponsor=False, salary_min=0),
        Extraction(),
    ])
    monkeypatch.setattr(rules_history.rules, "parse", lambda text: (next(extractions), {}))

    counts = rules_history.count_extractions([{"comment_text": "a"}, {"comment_text": "b"}])

    assert counts == {
        "total_posts": 2,
        **dict.fromkeys(rules_history.FIELDS, 0),
        "company": 1,
        "visa_sponsor": 1,
        "salary_min": 1,
        "role_titles": 2,
        "skills": 2,
    }


def test_empty_thread_counts():
    assert rules_history.count_extractions([]) == {
        "total_posts": 0, **dict.fromkeys(rules_history.FIELDS, 0),
    }


def test_history_appends_and_preserves_other_dates_and_threads(tmp_path):
    path = tmp_path / "nested" / "history.jsonl"
    rows = [history_row(), history_row(thread_id="456"), history_row(date="2026-10-30")]
    for row in rows:
        rules_history.update_history(path, row)
    assert read_rows(path) == rows
    assert path.read_text().endswith("\n")


def test_history_replaces_same_date_thread_including_old_duplicates(tmp_path):
    path = tmp_path / "history.jsonl"
    old = history_row(thread_id=123)
    other = history_row(thread_id="456")
    path.write_text("\n".join(json.dumps(row) for row in [old, other, old]) + "\n")
    replacement = history_row(total=5)

    rules_history.update_history(path, replacement)
    rules_history.update_history(path, replacement)

    assert read_rows(path) == [replacement, other]


def test_trend_table_has_every_field_and_sorted_run():
    earlier = history_row(total=2)
    later = history_row(date="2026-10-30", total=3)
    later["company"] = 1
    lines = rules_history.trend_table([later, earlier]).splitlines()

    assert lines[0].split() == ["date", "thread_id", "total_posts", *Extraction.model_fields]
    assert lines[1].split() == [str(value) for value in earlier.values()]
    assert lines[2].split() == [str(value) for value in later.values()]
    assert len(lines) == 3


def test_main_fetches_top_level_pages_and_runs_real_rules_offline(tmp_path, monkeypatch, capsys):
    requests = []

    def respond(request):
        requests.append(request)
        assert request.url.path == "/api/v1/search"
        assert request.url.params["tags"] == "comment,story_123"
        page = int(request.url.params["page"])
        hits = [
            {"parent_id": 123, "comment_text": (
                "Acme | Senior Engineer | Remote (Canada) | $100k-$150k"
                "<p>Python &amp; Docker. No sponsorship."
            )},
            {"parent_id": 999, "comment_text": "Reply | Engineer | Remote | $200k"},
        ] if page == 0 else [{"parent_id": "123", "comment_text": None}]
        return httpx.Response(200, json={"nbPages": 2, "hits": hits})

    monkeypatch.setattr(
        rules_history.fetch, "client",
        lambda: httpx.Client(base_url=rules_history.fetch.API, transport=httpx.MockTransport(respond)),
    )
    monkeypatch.setattr(rules_history.fetch.time, "sleep", lambda seconds: None)
    path = tmp_path / "history.jsonl"
    prior = history_row(date="2020-01-01", thread_id="456")
    rules_history.update_history(path, prior)

    rules_history.main(["--thread", "123", "--history", str(path)])

    assert len(requests) == 2
    rows = read_rows(path)
    assert rows[0] == prior
    assert rows[1] == {
        "date": rules_history.run_date(),
        "thread_id": "123",
        "total_posts": 2,
        **{field: 1 for field in rules_history.FIELDS},
        "role_titles": 2,
        "skills": 2,
    }
    assert capsys.readouterr().out == rules_history.trend_table(rows) + "\n"


def test_run_date_after_8pm_toronto_stays_on_toronto_date():
    # 2026-10-30 01:30 UTC == 2026-10-29 21:30 EDT
    assert rules_history.run_date(datetime(2026, 10, 30, 1, 30, tzinfo=UTC)) == "2026-10-29"
    # winter (EST, UTC-5): 2026-12-02 04:59 UTC == 2026-12-01 23:59
    assert rules_history.run_date(datetime(2026, 12, 2, 4, 59, tzinfo=UTC)) == "2026-12-01"
