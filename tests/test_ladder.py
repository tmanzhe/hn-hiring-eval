"""Pure disagreement reporting; no model calls or ladder execution."""

from evals.ladder import LADDER_CONFIGS, build_disagreement_report, cost_complete
from ingest.normalize import normalize
from ingest.schema import Extraction


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
