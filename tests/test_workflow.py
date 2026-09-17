"""The workflow config (W). Driven against a fake model, so no key is needed.

W exists to isolate one variable against config C: who decides the sequence. Both use the same
tools, the same model and the same verification step; W's path is hardcoded and C's is chosen by
the model. These tests pin the properties that make that comparison valid.
"""


from agent.workflow import MAX_REVISIONS, extract

POST = "Portless | AI Engineer | Remote | $180,000 - $230,000\n\nWe use Python."


class StructuredFake:
    """A duck-typed stand-in, not a BaseChatModel subclass.

    The workflow only ever calls `with_structured_output`, so a real model class buys nothing
    and costs something: pydantic model fields can't hold per-instance mutable state cleanly,
    and a shared class attribute would leak scripted responses between tests.
    """

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls: list = []

    def with_structured_output(self, schema, **kwargs):
        outer = self

        class Runner:
            def invoke(self, prompt, **_):
                outer.calls.append(prompt)
                idx = min(len(outer.calls) - 1, len(outer.responses) - 1)
                return outer.responses[idx]

        return Runner()


def fake(*responses):
    return StructuredFake(*responses)


def good(**over):
    from ingest.schema import Extraction

    return Extraction(**{"company": "Portless", "salary_min": 180000, "salary_max": 230000,
                         "skills": ["Python"], **over})


class TestFixedPath:
    def test_clean_extraction_takes_one_call(self):
        """Nothing ungrounded means no revision. The workflow must not pay for a second call
        it doesn't need — that's the efficiency it trades the agent loop for."""
        m = fake(good())
        out, trace = extract(POST, chat_model=m)
        assert trace.error is None, trace.error
        assert trace.model_calls == 1
        assert trace.revised is False
        assert out.company == "Portless"

    def test_ungrounded_value_triggers_exactly_one_revision(self):
        """A fabricated company is caught by verify_claim and sent back once. Once, not looped —
        a loop is what makes something an agent."""
        m = fake(good(company="Google"), good())
        out, trace = extract(POST, chat_model=m)
        assert trace.verify_failures >= 1
        assert trace.revised is True
        assert trace.model_calls == 1 + MAX_REVISIONS
        assert out.company == "Portless"

    def test_verification_runs_unconditionally(self):
        """The difference from config C: here I call verify_claim, the model doesn't choose to.
        It runs on every post whether the model wants it or not."""
        _, trace = extract(POST, chat_model=fake(good()))
        assert "verify_claim" in trace.tool_calls

    def test_salary_candidates_handed_over_up_front(self):
        """The workflow knows this post needs them, so it fetches them rather than waiting for
        the model to ask — one fewer round trip than the agent path."""
        m = fake(good())
        extract(POST, chat_model=m)
        assert "find_salary_candidates" in _trace_tools(m)


def _trace_tools(m):
    _, trace = extract(POST, chat_model=m)
    return trace.tool_calls


class TestComparability:
    def test_trace_carries_the_same_evidence_as_an_agent_trajectory(self):
        """W and C land in the same frontier table, so the cost columns have to be populated
        the same way or the comparison is meaningless."""
        _, trace = extract(POST, chat_model=fake(good()))
        for attr in ("model_calls", "input_tokens", "output_tokens", "latency_ms",
                     "verify_failures", "tool_calls"):
            assert hasattr(trace, attr), attr

    def test_returns_the_same_schema_as_every_other_config(self):
        from ingest.schema import Extraction

        out, _ = extract(POST, chat_model=fake(good()))
        assert isinstance(out, Extraction)

    def test_a_failure_is_recorded_not_raised(self):
        class Boom(StructuredFake):
            def with_structured_output(self, schema, **kwargs):
                raise RuntimeError("upstream exploded")

        out, trace = extract(POST, chat_model=Boom())
        assert trace.error is not None and "exploded" in trace.error
        assert out.model_dump(exclude_defaults=True) == {}


class TestAbstention:
    def test_null_survives(self):
        out, _ = extract(POST, chat_model=fake(good(salary_min=None, salary_max=None)))
        assert out.salary_min is None

    def test_abstained_fields_are_not_flagged_ungrounded(self):
        """A null has nothing to ground, so it must never trigger a revision. Otherwise the
        workflow would punish exactly the behaviour the whole project rewards."""
        _, trace = extract(POST, chat_model=fake(good(company=None, salary_min=None,
                                                      salary_max=None)))
        assert trace.verify_failures == 0
        assert trace.revised is False
