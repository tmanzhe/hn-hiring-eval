"""The F rung uses scripted structured responses only; no network or API key."""

import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ingest.fallback import extract
from ingest.rules import parse

PROSE = (
    'We are Acme Labs, hiring a senior Python engineer to work in Toronto. '
    'Salary is $180k per year; visa sponsorship available.'
)


def fake(response):
    chat = Mock()
    chat.with_structured_output.return_value.invoke.return_value = response
    return chat


def test_rules_success_skips_model_even_when_other_fields_are_null(monkeypatch):
    # No salary: this gate must depend on company/location, not is_confident().
    post = 'Acme | Engineer | Toronto'
    chat = fake({})
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    result, trace = extract(post, chat_model=chat)
    assert result == parse(post)[0]
    chat.with_structured_output.assert_not_called()
    assert trace.model_calls == 0 and trace.error is None
    # A rules-only post also works without an injected client or importing LangChain.
    without_client, skipped = extract(post)
    assert without_client == result
    assert skipped.model_calls == 0 and skipped.error is None


def test_prose_fills_both_missing_fields_and_preserves_every_other_rules_value():
    chat = fake({'company': 'Acme Labs', 'location': 'Toronto'})
    result, trace = extract(PROSE, chat_model=chat)
    assert trace.model_calls == 1 and trace.error is None
    assert result.company == 'Acme Labs' and result.location == 'Toronto'
    before = parse(PROSE)[0].model_dump(exclude={'company', 'location'})
    assert result.model_dump(exclude={'company', 'location'}) == before
    schema = chat.with_structured_output.call_args.args[0]
    assert set(schema.model_fields) == {'company', 'location'}
    prompt = chat.with_structured_output.return_value.invoke.call_args.args[0]
    assert 'Return null' in prompt and 'Do not guess' in prompt and PROSE in prompt


@pytest.mark.parametrize(('post', 'field', 'response'), [
    ('Acme | Engineer | Remote\nWork from Toronto.', 'location', 'Toronto'),
    ('Senior Engineer | Toronto | Onsite\nJoin Acme Labs.', 'company', 'Acme Labs'),
])
def test_only_null_field_is_requested(post, field, response):
    chat = fake({field: response})
    original = parse(post)[0]
    result, trace = extract(post, chat_model=chat)
    assert trace.error is None
    schema = chat.with_structured_output.call_args.args[0]
    assert set(schema.model_fields) == {field}
    prompt = chat.with_structured_output.return_value.invoke.call_args.args[0]
    assert prompt.splitlines()[0] == f'Extract only these missing fields: {field}.'
    assert getattr(result, field) == response
    assert result.model_dump(exclude={field}) == original.model_dump(exclude={field})


def test_abstention_keeps_null():
    result, trace = extract(PROSE, chat_model=fake({'company': None, 'location': None}))
    assert result.company is None and result.location is None
    assert trace.model_calls == 1 and trace.verify_failures == 0 and trace.error is None


def test_unsupported_values_are_rejected_independently():
    result, trace = extract(PROSE, chat_model=fake({'company': 'Google', 'location': 'Toronto'}))
    assert result.company is None and result.location == 'Toronto'
    assert trace.verify_failures == 1 and trace.error is None


def test_unsupported_location_is_rejected():
    result, trace = extract(PROSE, chat_model=fake({'company': 'Acme Labs', 'location': 'Paris'}))
    assert result.company == 'Acme Labs' and result.location is None
    assert trace.verify_failures == 1


def test_partial_word_is_not_evidence_for_company():
    result, _ = extract('We build metaverse tools.', chat_model=fake({'company': 'Meta'}))
    assert result.company is None


def test_normalized_source_span_is_accepted():
    chat = fake({'company': 'acme labs', 'location': 'TORONTO'})
    result, trace = extract('Join Acme\nLabs in Toronto.', chat_model=chat)
    assert result.company == 'acme labs' and result.location == 'TORONTO'
    assert trace.verify_failures == 0


def test_structured_pydantic_response_is_accepted():
    chat = Mock()

    def structured(schema):
        runner = Mock()
        runner.invoke.return_value = schema(company='Acme Labs', location='Toronto')
        return runner

    chat.with_structured_output.side_effect = structured
    result, trace = extract(PROSE, chat_model=chat)
    assert trace.error is None
    assert result.company == 'Acme Labs' and result.location == 'Toronto'


@pytest.mark.parametrize('model', [None, 'explicit-stub-model'])
def test_client_uses_existing_model_settings_without_network(monkeypatch, model):
    factory = Mock(return_value=fake({'company': 'Acme Labs', 'location': 'Toronto'}))
    monkeypatch.setitem(sys.modules, 'langchain_anthropic',
                        SimpleNamespace(ChatAnthropic=factory))
    monkeypatch.setenv('STRONG_MODEL', 'env-stub-model')
    result, trace = extract(PROSE, model=model)
    assert trace.error is None and result.company == 'Acme Labs'
    factory.assert_called_once_with(model=model or 'env-stub-model', max_tokens=4096, max_retries=0)


def test_unsolicited_fields_cannot_override_rules():
    post = 'Acme | Engineer | Remote\nWork from Toronto.'
    result, trace = extract(post, chat_model=fake({'location': 'Toronto', 'company': 'Other'}))
    assert result.company == 'Acme'
    assert trace.error is not None  # response violated the missing-fields-only schema


def test_model_failure_keeps_rules_and_records_error():
    chat = fake({})
    chat.with_structured_output.return_value.invoke.side_effect = RuntimeError('offline failure')
    result, trace = extract(PROSE, chat_model=chat)
    assert result == parse(PROSE)[0]
    assert trace.model_calls == 1 and 'offline failure' in trace.error


@pytest.mark.parametrize('response', [[], {'company': 123}, {'company': ''}])
def test_malformed_or_empty_response_cannot_fill_missing_fields(response):
    result, _ = extract(PROSE, chat_model=fake(response))
    assert result.company is None and result.location is None
