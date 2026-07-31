# agent

A multi-step extraction agent over the posts the rules path can't handle. Design and rationale
in `docs/agent-design.md`.

Not a feature bolted on the side — a **set of extra configs in the step-20 Pareto table**,
measured with the same labels, scorers and slices as the rules and single-call configs.

| File | What | Status |
| --- | --- | --- |
| `tools.py` | deterministic tools the agent orchestrates. No model calls. | done |
| `configs.py` | the A–E surface variants the experiment compares | done |
| `extract_agent.py` | the LangGraph loop | built, **live path unverified** |
| `../evals/agent_eval.py` | trajectory metrics on top of the existing scorers | not built |

The tools are plain Python on purpose. They stay fully unit-testable without an API key, and
keeping them dumb is what makes the agent's own contribution measurable — if quality improves,
it improved because of planning and verification, not because a tool got smarter.

Install: `uv sync --extra agent`


## Status caveat

`extract_agent.py` constructs correctly for all five configs and its prompt-building and
trajectory-parsing are unit tested. The **live `agent.invoke(...)` round trip has never run** —
there is no `ANTHROPIC_API_KEY` on this machine yet.

Specifically unverified: that the result dict uses `structured_response`, that messages carry
`usage_metadata` in the shape `_walk` expects, and that `AnthropicPromptCachingMiddleware`
behaves as assumed. Those are assumptions about LangChain v1.3, not facts, until one real call
confirms them.

First thing to do once a key exists:

```sh
cp .env.example .env          # add ANTHROPIC_API_KEY
uv run agent/extract_agent.py --config C --id 48915735
```

Expect to fix `_walk` on the first run.
