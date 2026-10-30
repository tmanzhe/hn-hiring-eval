"""Ladder selection and reporting with stubbed data/models only; no network."""

import argparse
import json
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from evals import ladder
from evals.ladder import LADDER_CONFIGS, build_disagreement_report, cost_complete, parse_configs
from ingest.normalize import normalize
from ingest.schema import Extraction


@pytest.mark.parametrize(('value', 'expected'), [
    ('F', ('F',)),
    ('f', ('F',)),
    ('B,F', ('B', 'F')),
    (' f, b, W, F, b ', ('B', 'W', 'F')),
    ('f,w,e,d,c,b', LADDER_CONFIGS),
])
def test_parse_configs(value, expected):
    assert parse_configs(value) == expected


@pytest.mark.parametrize('value', ['', ' ', ',', 'B,', ',F', 'B,,F', 'B, ,F',
                                   'A', 'unknown', 'B,unknown,F'])
def test_parse_configs_rejects_unknown_or_empty_names(value):
    with pytest.raises(argparse.ArgumentTypeError, match='invalid rung name') as exc:
        parse_configs(value)
    assert 'valid rungs: B, C, D, E, W, F' in str(exc.value)


@pytest.mark.parametrize('value', ['', 'B,,F', 'B,unknown'])
def test_invalid_config_is_a_cli_error_before_credentials_or_execution(monkeypatch, capsys, value):
    monkeypatch.setattr(sys, 'argv', ['ladder.py', '--config', value])
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    load = Mock(side_effect=AssertionError('must not load data for invalid configs'))
    monkeypatch.setattr(ladder, 'load_labels', load)
    with pytest.raises(SystemExit) as exc:
        ladder.main()
    assert exc.value.code == 2
    error = capsys.readouterr().err
    assert 'argument --config: invalid rung name' in error
    assert 'valid rungs: B, C, D, E, W, F' in error
    assert 'ANTHROPIC_API_KEY' not in error
    load.assert_not_called()


@pytest.mark.parametrize(('selection', 'expected'), [
    (None, LADDER_CONFIGS),
    ('f', ('F',)),
    ('F,b,F', ('B', 'F')),
    ('w,C,w', ('C', 'W')),
])
def test_only_selected_rungs_execute_and_appear_in_reports(monkeypatch, tmp_path,
                                                          selection, expected):
    output = tmp_path / 'quality.md'
    disagreements = tmp_path / 'disagreements.md'
    argv = ['ladder.py', '--split', 'all', '--output', str(output),
            '--disagreements', str(disagreements)]
    if selection is not None:
        argv += ['--config', selection]
    monkeypatch.setattr(sys, 'argv', argv)
    for key, value in {
        'ANTHROPIC_API_KEY': 'fake-key', 'STRONG_MODEL': 'stub-model',
        'LLM_PRICE_SOURCE': 'stub-prices',
        **{f'LLM_{kind}_USD_PER_MTOK': '1'
           for kind in ('INPUT', 'OUTPUT', 'CACHE_READ', 'CACHE_WRITE')},
    }.items():
        monkeypatch.setenv(key, value)

    # Replace every model/extractor import, including the optional agent dependencies.
    # No production extractor, model client, corpus, or label loader runs in this test.
    factory = Mock(side_effect=lambda **kwargs: SimpleNamespace(**kwargs))
    monkeypatch.setitem(sys.modules, 'langchain_anthropic',
                        SimpleNamespace(ChatAnthropic=factory))
    monkeypatch.setitem(sys.modules, 'langchain_core.callbacks',
                        SimpleNamespace(BaseCallbackHandler=object))
    calls = []

    def extract(text, config, *, model, chat_model):
        calls.append((config, text))
        response = SimpleNamespace(generations=[[SimpleNamespace(message=SimpleNamespace(
            usage_metadata={'input_tokens': 1, 'output_tokens': 1}))]])
        chat_model.callbacks[0].on_llm_end(response)
        prediction = Extraction(company='Wrong')
        trace = SimpleNamespace(error=None, model_calls=1)
        if config in ('W', 'F'):
            return prediction, trace
        return SimpleNamespace(extraction=prediction, trajectory=trace)

    monkeypatch.setitem(sys.modules, 'agent.extract_agent', SimpleNamespace(extract=extract))
    for config, module in [('W', 'agent.workflow'), ('F', 'ingest.fallback')]:
        monkeypatch.setitem(sys.modules, module, SimpleNamespace(
            extract=lambda text, _config=config, **kwargs: extract(text, _config, **kwargs)))
    monkeypatch.setattr(ladder, 'load_labels', lambda split: (
        [{'comment_id': split, 'company': 'Acme'}], 'stub-labels'))
    monkeypatch.setattr(ladder, 'by_id', lambda ids: [{'comment_text': ids[0]}])

    ladder.main()

    expected_runs = [(config, split) for config in expected for split in ('dev', 'held-out')]
    assert calls == expected_runs
    assert factory.call_count == len(expected_runs)
    rows = json.loads(output.with_suffix('.json').read_text())
    assert [(row['config'], row['split']) for row in rows] == expected_runs
    quality = output.read_text()
    assert [line for line in quality.splitlines() if line.startswith('## Config ')] == [
        f'## Config {config}' for config in expected]
    report = disagreements.read_text()
    assert '| Field | ' + ' | '.join(expected) + ' |' in report
    assert '| company | ' + ' | '.join('2' for _ in expected) + ' |' in report
    company = report.split('## company\n', 1)[1].split('## salary\n', 1)[0]
    assert [line for line in company.splitlines() if line.startswith('### Config ')] == [
        f'### Config {config} (2)' for config in expected]
    for config in set(LADDER_CONFIGS) - set(expected):
        assert f'Config {config}' not in report


def test_disagreement_report_uses_scoring_matches_and_groups_field_then_config():
    label = dict(comment_id=101, company='Acme', location='San Francisco',
                 salary_min=30, salary_max=40, salary_period='hour',
                 skills=['Kubernetes'], remote='remote', seniority='senior')
    agrees = normalize(Extraction(company='Acme', location=' SAN FRANCISCO ',
                                  salary_min=30, salary_max=40, salary_period='hour',
                                  skills=['k8s'], remote='remote', seniority='senior'))
    wrong = Extraction(company='Other | <Co>', location='New York',
                       salary_min=62400, salary_max=99999,
                       skills=['k8s', 'python'], remote='onsite', seniority='junior')
    report = build_disagreement_report([
        ('B', 'dev', [(agrees, label), (Extraction(company=''), {'comment_id': 102})]),
        ('C', 'dev', [(wrong, label)]),
        ('C', 'held-out', [(wrong, {**label, 'comment_id': 201})]),
        ('W', 'dev', [(Extraction(), label)]),
    ])

    # All six fields disagree twice for C and once for W; normalized B is a full match.
    for field in ('company', 'salary', 'location', 'skills', 'remote', 'seniority'):
        assert f'| {field} | 0 | 2 | 0 | 0 | 1 | 0 |' in report
    company = report.split('## company\n', 1)[1].split('## salary\n', 1)[0]
    assert company.index('### Config B (0)') < company.index('### Config C (2)')
    assert company.index('### Config C (2)') < company.index('### Config W (1)')
    assert '| dev | <code>101</code> |' in company
    assert '| held-out | <code>201</code> |' in company
    assert '&quot;Acme&quot;' in company
    assert 'Other &#124; &lt;Co&gt;' in company
    assert '<code>null</code>' in company
    assert '<code>102</code>' not in report
    salary = report.split('## salary\n', 1)[1].split('## location\n', 1)[0]
    assert '&quot;min&quot;: 30' in salary and '&quot;period&quot;: &quot;hour&quot;' in salary
    assert '&quot;min&quot;: 62400' in salary and '&quot;max&quot;: 99999' in salary


def test_ladder_lists_fallback_and_reports_its_disagreements():
    assert LADDER_CONFIGS == ('B', 'C', 'D', 'E', 'W', 'F')
    report = build_disagreement_report([
        ('F', 'dev', [(Extraction(), {'comment_id': 301, 'company': 'Acme'})]),
    ])
    assert '| Field | B | C | D | E | W | F |' in report
    assert '| company | 0 | 0 | 0 | 0 | 0 | 1 |' in report
    assert '### Config F (1)' in report
    assert '<code>301</code>' in report


def test_rules_only_fallback_has_complete_zero_cost_but_missing_usage_still_fails():
    assert cost_complete('F', responses=0, missing=False, errors=[])
    assert cost_complete('F', responses=1, missing=False, errors=[])
    assert not cost_complete('F', responses=0, missing=True, errors=[])
    assert not cost_complete('F', responses=1, missing=True, errors=[])
    assert not cost_complete('F', responses=0, missing=False, errors=['failed call'])
    for config in ('B', 'C', 'D', 'E', 'W'):
        assert not cost_complete(config, responses=0, missing=False, errors=[])


def test_skip_missing_flag_is_registered():
    import subprocess
    import sys
    out = subprocess.run([sys.executable, 'evals/ladder.py', '--help'],
                         capture_output=True, text=True, check=True).stdout
    assert '--skip-missing' in out
