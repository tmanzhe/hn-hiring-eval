"""Agent plumbing that can be tested without an API key.

What this DOES cover: prompt construction, and the trajectory parser that turns a message list
into step/tool/token counts.

What it does NOT cover: the live `agent.invoke(...)` round trip. The shape of the returned dict
(`structured_response`, `usage_metadata`, `tool_calls`) is an assumption about LangChain until
a real call confirms it. Marked in the repo as unverified for exactly that reason — see the note
in agent/README.md.
"""

from types import SimpleNamespace

import pytest

from agent.extract_agent import Trajectory, _prompt, _walk


def msg(content="", tool_calls=None, usage=None):
    return SimpleNamespace(content=content, tool_calls=tool_calls or [], usage_metadata=usage)


class TestPrompt:
    TEXT = "Acme | Senior Engineer | Remote | $180k-$220k\n\nWe use Python and Kubernetes."

    def test_plain_prompt_contains_the_post(self):
        p = _prompt(self.TEXT, seed_with_rules=False)
        assert self.TEXT in p
        assert "regex parser" not in p

    def test_seeded_prompt_adds_the_regex_pass(self):
        p = _prompt(self.TEXT, seed_with_rules=True)
        assert self.TEXT in p
        assert "regex parser" in p
        assert "Acme" in p

    def test_seeded_prompt_marks_the_hint_as_fallible(self):
        """Presenting the regex output as authoritative would launder the parser's mistakes
        through the model, which is the opposite of what config E is testing."""
        p = _prompt(self.TEXT, seed_with_rules=True)
        assert "sometimes wrong" in p or "often incomplete" in p
        assert "Verify each field" in p

    def test_seeding_never_crashes_on_an_unparseable_post(self):
        assert _prompt("we are a small team", seed_with_rules=True)


class TestWalk:
    def test_counts_steps(self):
        t = Trajectory(config="C", model="m")
        _walk([msg(), msg(), msg()], t)
        assert t.steps == 3

    def test_collects_tool_names(self):
        t = Trajectory(config="C", model="m")
        _walk([msg(tool_calls=[{"name": "verify_claim"}, {"name": "split_roles"}])], t)
        assert t.tool_calls == ["verify_claim", "split_roles"]
        assert t.n_tool_calls == 2

    def test_handles_object_style_tool_calls(self):
        t = Trajectory(config="C", model="m")
        _walk([msg(tool_calls=[SimpleNamespace(name="canonical_skill")])], t)
        assert t.tool_calls == ["canonical_skill"]

    def test_sums_tokens_across_steps(self):
        t = Trajectory(config="C", model="m")
        _walk(
            [
                msg(usage={"input_tokens": 100, "output_tokens": 20}),
                msg(usage={"input_tokens": 300, "output_tokens": 40,
                           "input_token_details": {"cache_read": 250}}),
            ],
            t,
        )
        assert (t.input_tokens, t.output_tokens, t.cache_read_tokens) == (400, 60, 250)

    def test_counts_verification_failures(self):
        """The headline agent metric — how often self-checking actually caught something."""
        t = Trajectory(config="C", model="m")
        _walk([msg(content='{"grounded": false, "reason": "not in post"}'), msg(content="ok")], t)
        assert t.verify_failures == 1

    def test_tolerates_messages_with_nothing_useful(self):
        t = Trajectory(config="C", model="m")
        _walk([msg(), SimpleNamespace()], t)
        assert t.steps == 2 and t.n_tool_calls == 0


class TestTrajectory:
    def test_defaults_are_zero_not_none(self):
        """Averaging over a run breaks if a field is None, and one bad row would poison the
        whole config's cost number."""
        t = Trajectory(config="A", model="m")
        for f in ("steps", "input_tokens", "output_tokens", "latency_ms", "verify_failures"):
            assert getattr(t, f) == 0
        assert t.error is None

    @pytest.mark.parametrize("config", list("ABCDE"))
    def test_every_config_produces_a_labelled_trajectory(self, config):
        assert Trajectory(config=config, model="m").config == config
