# agent

A multi-step extraction agent over the posts the rules path can't handle. Design and rationale
in `docs/agent-design.md`.

Not a feature bolted on the side — a **set of extra configs in the step-20 Pareto table**,
measured with the same labels, scorers and slices as the rules and single-call configs.

| File | What | Status |
| --- | --- | --- |
| `tools.py` | deterministic tools the agent orchestrates. No model calls. | done |
| `configs.py` | the A–E surface variants the experiment compares | done |
| `extract_agent.py` | the LangGraph loop | not built |
| `../evals/agent_eval.py` | trajectory metrics on top of the existing scorers | not built |

The tools are plain Python on purpose. They stay fully unit-testable without an API key, and
keeping them dumb is what makes the agent's own contribution measurable — if quality improves,
it improved because of planning and verification, not because a tool got smarter.

Install: `uv sync --extra agent`
