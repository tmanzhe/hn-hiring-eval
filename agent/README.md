# agent

A multi-step extraction agent over the posts the rules path can't handle. Design and rationale
in `docs/agent-design.md`.

Not a feature bolted on the side — a **set of extra configs in the step-20 Pareto table**,
measured with the same labels, scorers and slices as the rules and single-call configs.

| File | What | Status |
| --- | --- | --- |
| `tools.py` | deterministic tools the agent orchestrates. No model calls. | done |
| `configs.py` | the A–E surface variants the experiment compares | done |
| `extract_agent.py` | the LangGraph loop | built, graph verified against a fake model |
| `../evals/agent_eval.py` | trajectory metrics on top of the existing scorers | not built |

The tools are plain Python on purpose. They stay fully unit-testable without an API key, and
keeping them dumb is what makes the agent's own contribution measurable — if quality improves,
it improved because of planning and verification, not because a tool got smarter.

Install: `uv sync --extra agent`


## What is and isn't verified

`tests/test_agent_graph.py` drives all five configs through the real `create_agent` graph with a
fake model. Everything except the model's own output is exercised: the middleware, the tool
wiring, structured-output parsing into `Extraction`, the trajectory walk, and error capture.

That settled three assumptions I had flagged as guesses — the result dict does use
`structured_response`, messages do carry `usage_metadata` in the shape `_walk` expects, and tool
calls appear where it looks for them.

**Still unverified: whether Claude, given these tools and this prompt, extracts well.** No fake
can answer that. But when the key goes in, a failure will be about the model's output rather
than about plumbing — which is the entire point of running the fake first.

```sh
cp .env.example .env          # add ANTHROPIC_API_KEY
uv run agent/extract_agent.py --config C --id 48915735   # one post, ~1 cent
```
