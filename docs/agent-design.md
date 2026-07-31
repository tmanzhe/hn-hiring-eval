# The agent layer

## Why it exists

The harness measures single-call extraction. This adds a fifth config to the step-20 frontier —
a multi-step agent that plans, calls deterministic tools, and verifies its own output — and then
measures it with the same labels, scorers and slices as the other four.

The question it answers: **does planning beat one good prompt, and what does it cost?**

Both answers are useful. If the agent wins by 4 points at 8× the cost, that's a frontier point.
If it loses to a single well-prompted call, that's the more interesting result and almost nobody
publishes it.

## What it operates on

The 1,696 posts (85%) that the rules path cannot handle — `data/needs_llm.json`. These are the
genuinely hard ones: prose with no header, multi-role posts that need splitting, salary buried in
a sentence. That's where a loop can plausibly earn its cost.

## Shape

```
                    ┌──────────────────────────────┐
  hard post ───────►│  agent loop (LangGraph)      │
                    │                              │
                    │   plan → call tool → verify  │
                    │        ▲            │        │
                    │        └── retry ◄──┘        │
                    └──────────────┬───────────────┘
                                   ▼
                          Extraction (same schema)
                                   │
                                   ▼
                    evals/ — same scorers as configs 1-4
```

Same `Extraction` schema out. That's what makes it comparable — a different output shape would
mean a different benchmark and no comparison at all.

## Tools

Deterministic helpers the model orchestrates. **None of them call a model.** The agent decides
*which* to call and *what to do with the answer*; the tools themselves are plain Python and are
unit-testable without an API key.

| Tool | Does |
| --- | --- |
| `split_roles` | breaks a multi-role post into per-role chunks |
| `find_salary_candidates` | returns every salary-shaped string with surrounding context |
| `verify_claim` | checks an extracted value actually appears in the source text |
| `canonical_skill` | maps a term to the canonical skill name, or reports it's unknown |

`verify_claim` is the one that makes this agentic rather than one-shot. It's also the source of
the most interesting metric — see below.

## Stack

- **LangGraph 1.1.x** for the loop. A stateful graph with retry and conditional edges is what it
  is actually for, so it earns its place here where it would not for a single call.
- **`create_agent`** from `langchain` v1 — note `create_react_agent` from `langgraph.prebuilt` is
  deprecated in favour of it.
- **`response_format`** for structured output. In v1 this is folded into the model–tools loop
  rather than costing an extra call.
- **`AnthropicPromptCachingMiddleware`** — the system prompt and tool definitions are identical
  across all 1,696 posts, so the cacheable prefix is large and constant.
- **FastAPI** exposes it at `POST /api/extract` alongside the existing endpoints.

Deliberately **not** using LangChain's chain abstractions for the single-call configs. Those are
four lines of SDK code, and wrapping them in a framework would be the exact instinct this project
argues against. The framework is used where the framework earns it.

## How it gets measured

Two layers. The first makes it comparable to the other configs; the second is what a single-call
eval cannot capture.

**Outcome** — identical to configs 1–4, so it drops into the same Pareto table:
per-field accuracy, coverage vs precision, hallucination rate, macro-F1 on skills.

**Trajectory** — agent-specific:

| Metric | Why it matters |
| --- | --- |
| steps per post | the cost driver, and a runaway loop shows up here first |
| tool call distribution | is it using the tools or ignoring them? |
| **verification catch rate** | how often `verify_claim` failed *and* the agent then changed its answer |
| self-correction rate | of those catches, how many produced a correct final value |
| cost per post | tokens across every step, not just the final call |
| p95 latency | agents have long tails; the mean hides it |

**Verification catch rate is the headline.** It measures whether the extra machinery did anything
at all. An agent that never catches its own mistakes is a single call wearing a costume, and this
number says so with evidence.

## Honest risks

- **Non-determinism.** The same post can take different paths on different runs. Every agent eval
  row records `n_runs` and reports variance, otherwise a 2-point difference is unreadable.
- **Cost.** Multi-step means many calls. The frontier table must show cost per 1k posts, or the
  comparison flatters the agent.
- **It may lose.** That is a real possible outcome and the write-up commits to reporting it either
  way. An eval you only publish when it agrees with you is not an eval.
