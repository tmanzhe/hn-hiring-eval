"""The tool-surface experiment: A through E.

The claim being tested is "an agent is only as good as the tools you give it." That's usually
asserted. Here it's an eval axis — same posts, same labels, same scorers, same model, varying
only the surface. The result is a curve, not an opinion.

Two ways it can come out interesting:

  * Not monotonic. If D beats C but E beats D, written guidance is doing work that extra tools
    aren't. If C == B, three of the four tools aren't earning their tokens.
  * E wins. That's the deterministic-first thesis applied to agents — seeding the model with
    regex output improves accuracy AND cuts tokens, which is the whole project in miniature.

Nothing here imports LangChain. The configs are data, so they're testable without an API key
and readable without knowing the framework.
"""

from dataclasses import dataclass, field

from agent.tools import canonical_skill, find_salary_candidates, split_roles, verify_claim

# Written guidance, loaded into the system prompt for configs that enable it. This is the
# "skill" in the Agent Skills sense — instructions rather than capability. Every claim in it
# came from reading the corpus, not from imagination.
FORMAT_SKILL = """\
HN "Who is hiring" posts follow loose conventions. What the corpus actually shows:

- Many posts open with a pipe-delimited header: Company | Role | Location | Remote | Salary.
  When present it is the most reliable part of the post. When absent, everything is prose.
- Money in a post is often NOT compensation. Funding rounds ("$145M Series B"), transaction
  volumes ("$43B/day"), referral bounties ("$500 per referral") and product prices ("$7/month")
  all appear. Compensation is usually adjacent to a role or a word like salary, comp, or base.
- Salary is stated per year, per month, or per hour. "$30-120/hr" is a real posting. Report the
  period you actually saw; do not convert.
- A trailing k applies to both bounds: "$140-200k" means 140,000 to 200,000.
- Equity-only and "competitive" are common. Neither is a number. Return null.
- Roughly 2% of posts advertise several roles. Most numbered lists are requirements or
  interview stages, not roles.

When the post does not state something, return null. An omission costs coverage and can be
fixed later. An invented value cannot be distinguished from a real one afterwards.
"""


@dataclass(frozen=True)
class AgentConfig:
    name: str
    tools: list = field(default_factory=list)
    skill: str | None = None
    seed_with_rules: bool = False
    tests: str = ""

    @property
    def tool_names(self) -> list[str]:
        return [t.__name__ for t in self.tools]


CONFIGS = {
    "A": AgentConfig(
        name="A: single call, no tools",
        tests="the baseline. any agent config that loses to this is pure overhead.",
    ),
    "B": AgentConfig(
        name="B: verification only",
        tools=[verify_claim],
        tests="does self-checking alone help, without any other machinery?",
    ),
    "C": AgentConfig(
        name="C: full tool surface",
        tools=[split_roles, find_salary_candidates, verify_claim, canonical_skill],
        tests="does the whole surface beat verification alone? if C == B, three tools are dead weight.",
    ),
    "D": AgentConfig(
        name="D: full surface + written guidance",
        tools=[split_roles, find_salary_candidates, verify_claim, canonical_skill],
        skill=FORMAT_SKILL,
        tests="does telling it how posts are shaped beat giving it more things to call?",
    ),
    "E": AgentConfig(
        name="E: full surface + guidance + rules output as a hint",
        tools=[split_roles, find_salary_candidates, verify_claim, canonical_skill],
        skill=FORMAT_SKILL,
        seed_with_rules=True,
        tests="deterministic-first, applied to agents. does regex pre-work raise quality "
        "and cut tokens at the same time?",
    ),
}


def get(name: str) -> AgentConfig:
    key = name.strip().upper()
    if key not in CONFIGS:
        raise KeyError(f"unknown config {name!r}. one of: {', '.join(CONFIGS)}")
    return CONFIGS[key]
