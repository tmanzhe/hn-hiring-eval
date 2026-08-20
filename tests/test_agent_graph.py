"""The agent graph, driven end to end against a fake model.

Everything here is real except the model's own output: `create_agent`'s graph, the middleware,
the tool wiring, structured-output parsing, and the trajectory walk. That closes the gap the
unit tests couldn't — `test_agent_extract.py` checks my parsing against synthetic messages,
which only proves my code matches my assumptions. This proves it matches LangChain.

What is still unverified after this: whether Claude, given these tools and this prompt, produces
good extractions. No fake can answer that. But when the API key goes in, a failure will be about
the model's output rather than about my plumbing — which is the point of running this first.
"""

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from agent.extract_agent import build, extract

POST = "Portless | AI Engineer | Remote (North America) | $180k-$230k\n\nWe use Python."

EXTRACTION_ARGS = {
    "company": "Portless", "role_titles": ["AI Engineer"], "location": "Remote (North America)",
    "remote": "remote", "salary_min": 180000, "salary_max": 230000, "salary_currency": "USD",
    "salary_period": "year", "skills": ["Python"], "seniority": None, "visa_sponsor": None,
}


class ToolCallingFake(GenericFakeChatModel):
    """The stock fakes inherit `BaseChatModel.bind_tools`, which raises NotImplementedError, so
    `create_agent` can't build a graph around them. Binding is a no-op here — the scripted
    messages already contain whatever tool calls the test wants to exercise."""

    def bind_tools(self, tools, **kwargs):  # noqa: ARG002
        return self


def fake(*messages):
    return ToolCallingFake(messages=iter(messages))


def structured(**overrides):
    args = {**EXTRACTION_ARGS, **overrides}
    return AIMessage(content="", tool_calls=[{"name": "Extraction", "id": "s1", "args": args}])


class TestStructuredOutput:
    def test_response_lands_in_the_extraction_schema(self):
        """The assumption I flagged as unverified: that the result carries
        `structured_response` and that it parses into my Pydantic model."""
        r = extract(POST, "A", chat_model=fake(structured()))
        assert r.trajectory.error is None, r.trajectory.error
        assert r.extraction.company == "Portless"
        assert r.extraction.salary_min == 180000
        assert r.extraction.salary_period == "year"

    def test_abstention_survives_the_round_trip(self):
        """A null must arrive as None, not as 0 or "". The four-outcome scoring depends on
        telling 'absent' apart from 'zero'."""
        r = extract(POST, "A", chat_model=fake(structured(salary_min=None, salary_max=None)))
        assert r.extraction.salary_min is None
        assert r.extraction.company == "Portless"

    def test_a_model_that_returns_nothing_yields_an_empty_extraction(self):
        r = extract(POST, "A", chat_model=fake(AIMessage(content="I am not sure.")))
        assert r.extraction.model_dump(exclude_defaults=True) == {}


class TestTrajectory:
    def test_steps_and_latency_recorded(self):
        r = extract(POST, "A", chat_model=fake(structured()))
        assert r.trajectory.steps > 0
        assert r.trajectory.latency_ms >= 0
        assert r.trajectory.config == "A"

    def test_tool_calls_are_captured_from_a_real_graph_run(self):
        """Config C has four tools. A model that calls one must show up in the trajectory —
        this is the tool-call accounting the cost column depends on."""
        r = extract(
            POST,
            "C",
            chat_model=fake(
                AIMessage(content="", tool_calls=[
                    {"name": "verify_claim", "id": "t1",
                     "args": {"value": "Portless", "text": POST}},
                ]),
                structured(),
            ),
        )
        assert "verify_claim" in r.trajectory.tool_calls
        assert r.trajectory.n_tool_calls >= 1

    def test_a_model_error_is_recorded_not_raised(self):
        """One bad post must not abort a 1,696-post eval run."""

        class Boom(ToolCallingFake):
            def _generate(self, *a, **kw):
                raise RuntimeError("upstream exploded")

        r = extract(POST, "A", chat_model=Boom(messages=iter([])))
        assert r.trajectory.error is not None
        assert "upstream exploded" in r.trajectory.error
        assert r.extraction.model_dump(exclude_defaults=True) == {}


class TestConfigsAllRun:
    @pytest.mark.parametrize("config", list("ABCDE"))
    def test_every_config_completes_a_graph_run(self, config):
        """A–E have to be comparable, so all five must survive the same input. A config that
        errors would silently drop out of the frontier table."""
        r = extract(POST, config, chat_model=fake(structured()))
        assert r.trajectory.error is None, f"{config}: {r.trajectory.error}"
        assert r.extraction.company == "Portless"

    def test_config_e_seeds_the_prompt_without_breaking_the_graph(self):
        r = extract(POST, "E", chat_model=fake(structured()))
        assert r.trajectory.error is None
        assert r.trajectory.steps > 0


class TestBuild:
    def test_tool_count_matches_the_config(self):
        _, cfg_a, _ = build("A", chat_model=fake())
        _, cfg_c, _ = build("C", chat_model=fake())
        assert len(cfg_a.tools) == 0
        assert len(cfg_c.tools) == 4

    def test_model_id_is_reported_for_attribution(self):
        _, _, model = build("A", model="claude-opus-5", chat_model=fake())
        assert model == "claude-opus-5"
