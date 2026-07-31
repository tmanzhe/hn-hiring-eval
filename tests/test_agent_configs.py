"""The A–E experiment is data, so it can be checked without an API key.

These tests exist because a broken config matrix invalidates the comparison silently — two
configs accidentally identical would produce two indistinguishable rows and nobody would notice
until the write-up.
"""

import pytest

from agent.configs import CONFIGS, FORMAT_SKILL, get


class TestMatrix:
    def test_all_five_present(self):
        assert set(CONFIGS) == {"A", "B", "C", "D", "E"}

    def test_configs_are_actually_distinct(self):
        """If two configs are identical, the experiment compares a variable against itself."""
        signatures = {
            k: (tuple(c.tool_names), c.skill is not None, c.seed_with_rules)
            for k, c in CONFIGS.items()
        }
        assert len(set(signatures.values())) == len(signatures), signatures

    def test_each_config_states_what_it_isolates(self):
        for key, c in CONFIGS.items():
            assert c.tests, f"{key} does not say what it tests"

    def test_baseline_has_no_tools(self):
        assert CONFIGS["A"].tools == []
        assert CONFIGS["A"].skill is None
        assert CONFIGS["A"].seed_with_rules is False


class TestOneVariableAtATime:
    """Each step adds exactly one thing. Change two at once and the result is unreadable."""

    def test_b_adds_only_verification(self):
        assert CONFIGS["B"].tool_names == ["verify_claim"]
        assert CONFIGS["B"].skill is None

    def test_c_adds_only_tools(self):
        assert len(CONFIGS["C"].tools) == 4
        assert CONFIGS["C"].skill is None, "C must differ from D by the skill alone"

    def test_d_adds_only_the_skill(self):
        assert CONFIGS["D"].tool_names == CONFIGS["C"].tool_names
        assert CONFIGS["D"].skill is not None
        assert CONFIGS["D"].seed_with_rules is False

    def test_e_adds_only_the_rules_seed(self):
        assert CONFIGS["E"].tool_names == CONFIGS["D"].tool_names
        assert CONFIGS["E"].skill == CONFIGS["D"].skill
        assert CONFIGS["E"].seed_with_rules is True


class TestSkillContent:
    def test_pushes_toward_abstaining(self):
        """The single most important instruction. Losing it would quietly raise hallucination
        rate across every config that uses it."""
        assert "return null" in FORMAT_SKILL.lower()
        assert "invented" in FORMAT_SKILL.lower()

    def test_warns_that_money_is_not_always_salary(self):
        assert "Series B" in FORMAT_SKILL
        assert "bounties" in FORMAT_SKILL or "bounty" in FORMAT_SKILL

    def test_covers_the_bugs_the_parser_hit(self):
        """Both regressions the rules parser had are described in prose, so the model has a
        chance at what the regex needed a fix for."""
        assert "$140-200k" in FORMAT_SKILL
        assert "/hr" in FORMAT_SKILL

    def test_does_not_leak_labels(self):
        """A skill file must describe format, never the answers for specific posts. Naming a
        comment_id here would contaminate the benchmark."""
        assert "comment_id" not in FORMAT_SKILL
        assert not any(tok.isdigit() and len(tok) > 6 for tok in FORMAT_SKILL.split())


class TestLookup:
    def test_case_insensitive(self):
        assert get("a").name.startswith("A")
        assert get(" e ").seed_with_rules is True

    def test_unknown_raises_with_options(self):
        with pytest.raises(KeyError, match="unknown config"):
            get("Z")
