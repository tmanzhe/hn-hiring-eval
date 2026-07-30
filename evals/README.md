# evals

The extractor is the substrate. This directory is the point.

Offline, on demand and in CI. Never deploys.

```
labeled.jsonl ──► run.py ──► scorers ──► runs.jsonl ──► /evals page
```

| File | What | Status |
| --- | --- | --- |
| `ANNOTATION.md` | the hard calls, written before labeling | to write |
| `poc_labels.jsonl` | 10 labels, calibration only | to fill |
| `labeled.jsonl` | 60 stratified posts, 40 dev / 20 held-out | not built |
| `score_poc.py` | crude scorer over the POC 10 | done, becomes `scorers.py` |
| `scorers.py` | one per field | not built |
| `run.py` | config in, one `runs.jsonl` row out | not built |

## Four outcomes, not two

Any field allowed to be absent has four possible results. Averaging them destroys the only
information worth having:

| outcome | meaning | cost |
| --- | --- | --- |
| extracted | value present, value right | none |
| **abstained** | absent in the post, `null` returned | none — this is a win |
| missed | present in the post, `null` returned | recoverable, costs coverage |
| **hallucinated** | absent in the post, value invented | unrecoverable |

So **coverage** and **precision on attempts** are reported as separate numbers, and hallucination
rate gets its own line that never enters an average. A model that abstains on 60% and is never
wrong beats one that always answers and is wrong a third of the time — a single accuracy score
ranks those the wrong way round.

## Rules

- **Baseline before tuning.** Record the number, then change things. Otherwise there's no way to
  tell a real gain from noise.
- **Normalize both sides identically.** Apply the synonym table to labels and predictions or
  skills F1 is measuring the synonym table, and it drifts every time an entry is added.
- **Error bars on everything.** At n=40 a measured 84% carries a 95% interval of roughly ±11
  points, so 84% vs 86% is not a result.
- **Hash the prompt into every row.** A metric that can't be attributed to a specific prompt and
  a pinned model is not evidence.

## Why hand-rolled

At 60 examples, understanding the mechanics beats adopting a framework. promptfoo, Braintrust,
LangSmith, DeepEval and Inspect all do this properly at scale — that's roughly 200 lines here,
and the tradeoff is written up in the top-level README.
