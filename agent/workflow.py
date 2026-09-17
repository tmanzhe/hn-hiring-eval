"""A workflow, not an agent. The rung the A–E ladder was missing.

Anthropic's "Building Effective Agents" draws the line I had blurred:

  * **Workflow** — LLM calls orchestrated through *predefined code paths*. I decide the steps.
  * **Agent** — the LLM directs its own process and tool use. It decides the steps.

Configs A–E went straight from one call (A) to a tool-using agent (B–E), with nothing between.
So a win for C over A could mean two different things — that verification helps, or that
*model-directed control* helps — and the experiment couldn't tell them apart.

This is the evaluator-optimizer pattern from the paper, hardcoded: extract → verify → revise.
Same tools, same model, same verification step as config C. The only difference is **who decides
the sequence.** Comparing W against C isolates exactly that.

The paper's guidance is to use the simplest pattern that passes eval and reserve agents for when
you cannot hardcode the path but can still verify progress. Extraction is a case where the path
*is* hardcodeable — which makes "does the agent earn its loop?" a real question rather than a
rhetorical one.
"""

import json
import os
from dataclasses import dataclass, field

from agent.tools import find_salary_candidates, verify_claim
from ingest.schema import Extraction

MAX_REVISIONS = 1  # one corrective pass. more is a loop, and a loop is an agent.

EXTRACT_PROMPT = """\
Extract the posting details from this text.

Report only what the post states. When the post is silent on a field, return null for it. An
omission costs coverage and can be corrected later; an invented value is indistinguishable from
a real one afterwards.

Do not convert salary periods. If the post says "per hour", report the hourly figure and set
salary_period to "hour".

POST:
{text}
"""

REVISE_PROMPT = """\
Your extraction contained values that do not appear in the post:

{problems}

Re-extract. For each flagged field, either find the value in the post text or return null.
Returning null is the correct answer when the post does not state something.

POST:
{text}
"""


@dataclass
class WorkflowTrace:
    """Same shape of evidence the agent trajectory carries, so the two are comparable."""

    steps: int = 0
    model_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    verify_failures: int = 0
    revised: bool = False
    latency_ms: int = 0
    error: str | None = None
    tool_calls: list[str] = field(default_factory=list)


def _ungrounded(extraction: Extraction, text: str) -> list[str]:
    """Which extracted values don't appear in the post. Same `verify_claim` config C gets —
    the difference is that here it's called unconditionally by me, not when a model decides to."""
    problems = []
    for name in ("company", "location", "salary_min", "salary_max"):
        value = getattr(extraction, name)
        if value is None:
            continue
        result = verify_claim(str(value), text)
        if not result["grounded"]:
            problems.append(f"- {name}: {value!r} — {result['reason']}")
    return problems


def _call(chat_model, prompt: str, trace: WorkflowTrace) -> Extraction:
    structured = chat_model.with_structured_output(Extraction)
    trace.model_calls += 1
    trace.steps += 1
    result = structured.invoke(prompt)
    return result if isinstance(result, Extraction) else Extraction(**dict(result))


def extract(text: str, model: str | None = None, chat_model=None) -> tuple[Extraction, WorkflowTrace]:
    """Fixed path: extract, verify, revise once if verification failed. No loop, no agent."""
    import time

    trace = WorkflowTrace()
    started = time.perf_counter()

    if chat_model is None:
        from langchain_anthropic import ChatAnthropic

        model = model or os.environ.get("STRONG_MODEL", "claude-opus-5")
        chat_model = ChatAnthropic(model=model, max_tokens=4096)

    try:
        # Step 1 — extract. Salary candidates are handed over up front rather than fetched on
        # demand, because I already know this post needs them.
        candidates = find_salary_candidates(text)
        trace.tool_calls.append("find_salary_candidates")
        prompt = EXTRACT_PROMPT.format(text=text)
        if candidates:
            prompt += f"\nSalary-shaped strings found in the post:\n{json.dumps(candidates)}\n"

        extraction = _call(chat_model, prompt, trace)

        # Step 2 — verify. Always, not when the model feels like it.
        problems = _ungrounded(extraction, text)
        trace.tool_calls.extend(["verify_claim"] * 4)
        trace.verify_failures = len(problems)

        # Step 3 — revise, at most once.
        if problems and MAX_REVISIONS:
            trace.revised = True
            extraction = _call(
                chat_model,
                REVISE_PROMPT.format(problems="\n".join(problems), text=text),
                trace,
            )
    except Exception as exc:  # noqa: BLE001 - a failed post is a data point, not a crash
        trace.error = f"{type(exc).__name__}: {exc}"
        extraction = Extraction()

    trace.latency_ms = int((time.perf_counter() - started) * 1000)
    return extraction, trace
