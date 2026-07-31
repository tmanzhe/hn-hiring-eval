"""The extraction agent. One LangGraph loop, five tool surfaces (see agent/configs.py).

    uv run agent/extract_agent.py --config C --id 48915735
    uv run agent/extract_agent.py --config E --limit 5

Returns the same `Extraction` schema as every other config in the frontier table. That's what
makes it comparable — a different output shape would be a different benchmark.

Every run also returns a trajectory: steps taken, tools called, tokens spent. Outcome quality
alone can't tell you whether the machinery did anything; the trajectory can.
"""

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.configs import CONFIGS, get
from ingest.corpus import by_id, to_text
from ingest.rules import parse
from ingest.schema import Extraction

SYSTEM = """\
You extract structured facts from a Hacker News "Who is hiring" job posting.

Report only what the post states. When the post is silent on a field, return null for it.
An omission costs coverage and can be corrected later; an invented value is indistinguishable
from a real one afterwards, so it is the more expensive mistake by far.

Do not convert salary periods. If the post says "per hour", report the hourly figure and set
salary_period to "hour".
"""

# A hard ceiling on the loop. Without it a confused agent can spend unbounded tokens on one
# post, and the cost column in the frontier table stops meaning anything.
MAX_MODEL_CALLS = 8


@dataclass
class Trajectory:
    """What the agent did, as opposed to what it concluded."""

    config: str
    model: str
    steps: int = 0
    tool_calls: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    latency_ms: int = 0
    verify_failures: int = 0
    error: str | None = None

    @property
    def n_tool_calls(self) -> int:
        return len(self.tool_calls)


@dataclass
class AgentResult:
    extraction: Extraction
    trajectory: Trajectory


def build(config_name: str, model: str | None = None):
    """Assemble the agent for one config. Imports live here so `agent.configs` and the tools
    stay importable without the framework installed."""
    from langchain.agents import create_agent
    from langchain.agents.middleware import ModelCallLimitMiddleware
    from langchain_anthropic import ChatAnthropic
    from langchain_anthropic.middleware import AnthropicPromptCachingMiddleware

    cfg = get(config_name)
    model = model or os.environ.get("STRONG_MODEL", "claude-opus-5")

    system = SYSTEM
    if cfg.skill:
        system = f"{SYSTEM}\n\n{cfg.skill}"

    middleware = [
        ModelCallLimitMiddleware(thread_limit=MAX_MODEL_CALLS, exit_behavior="end"),
        # The system prompt and tool definitions are byte-identical across every post, so the
        # cacheable prefix is large and constant. Without this the same prefix is re-billed
        # 1,696 times.
        AnthropicPromptCachingMiddleware(),
    ]

    agent = create_agent(
        model=ChatAnthropic(model=model, max_tokens=4096),
        tools=list(cfg.tools),
        system_prompt=system,
        middleware=middleware,
        response_format=Extraction,
    )
    return agent, cfg, model


def _prompt(text: str, seed_with_rules: bool) -> str:
    if not seed_with_rules:
        return f"Extract the posting details from this text:\n\n{text}"

    # Config E. The regex output is offered as a starting point, explicitly fallible, because
    # presenting it as authoritative would just launder the parser's mistakes through the model.
    guess, _ = parse(text)
    hint = json.dumps(guess.model_dump(exclude_defaults=True), default=str)
    return (
        f"Extract the posting details from this text:\n\n{text}\n\n"
        f"A regex parser produced this first pass. It is often incomplete and sometimes wrong. "
        f"Verify each field against the post; correct or discard anything unsupported.\n{hint}"
    )


def _walk(messages, traj: Trajectory) -> None:
    """Pull step count, tool calls and usage out of the message list."""
    for m in messages:
        traj.steps += 1
        for call in getattr(m, "tool_calls", None) or []:
            name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
            if name:
                traj.tool_calls.append(name)
        usage = getattr(m, "usage_metadata", None)
        if usage:
            traj.input_tokens += usage.get("input_tokens", 0)
            traj.output_tokens += usage.get("output_tokens", 0)
            details = usage.get("input_token_details") or {}
            traj.cache_read_tokens += details.get("cache_read", 0)
        # verify_claim returning grounded:false is the signal that the machinery earned its keep
        content = getattr(m, "content", "")
        if isinstance(content, str) and '"grounded": false' in content.replace("'", '"').lower():
            traj.verify_failures += 1


def extract(text: str, config_name: str = "C", model: str | None = None) -> AgentResult:
    agent, cfg, model_id = build(config_name, model)
    traj = Trajectory(config=config_name, model=model_id)

    started = time.perf_counter()
    try:
        result = agent.invoke({"messages": [("user", _prompt(text, cfg.seed_with_rules))]})
        _walk(result.get("messages", []), traj)
        extraction = result.get("structured_response") or Extraction()
    except Exception as exc:  # noqa: BLE001 - a failed run is a data point, not a crash
        # Deliberately broad. An agent that errors on one post must not abort a 1,696-post
        # eval run; the failure is recorded on the trajectory and scored as a miss.
        traj.error = f"{type(exc).__name__}: {exc}"
        extraction = Extraction()
    traj.latency_ms = int((time.perf_counter() - started) * 1000)

    return AgentResult(extraction=extraction, trajectory=traj)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default="C", choices=sorted(CONFIGS))
    ap.add_argument("--id", help="a single comment id")
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--model")
    args = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY is not set. cp .env.example .env and fill it in.")

    if args.id:
        posts = by_id([args.id])
    else:
        needs = json.loads((Path("data") / "needs_llm.json").read_text())
        posts = by_id(needs[: args.limit])

    for c in posts:
        res = extract(to_text(c.get("comment_text")), args.config, args.model)
        print(f"\n=== {c['objectID']}  config {args.config} ===")
        print(json.dumps(res.extraction.model_dump(exclude_defaults=True), indent=2, default=str))
        t = asdict(res.trajectory)
        t["n_tool_calls"] = res.trajectory.n_tool_calls
        print(json.dumps(t, indent=2))


if __name__ == "__main__":
    main()
