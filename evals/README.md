# evals

The extractor is the substrate. This directory is the point.

Offline, on demand and in CI. Never deploys.

```
labeled.jsonl ──► run.py ──► scorers ──► runs.jsonl ──► /evals page
```

| File | What | Status |
| --- | --- | --- |
| `sample.py` | stratified draw + slice power analysis | done |
| `label.py` | interactive labeling, never shows parser output | done |
| `ANNOTATION.md` | the hard calls, written before labeling | to write |
| `poc_labels.jsonl` | 10 labels, calibration only | to fill |
| `labeled.jsonl` | 80 stratified posts, 53 dev / 27 held-out | to fill |
| `score_poc.py` | crude scorer over the POC 10 | done, becomes `scorers.py` |
| `scorers.py` | one per field | done |
| `run.py` | config in, one `runs.jsonl` row out | done |

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

## Workflow

```sh
uv run evals/sample.py -n 80 --oversample prose=20   # draw, once
uv run evals/label.py                                # label, resumable
uv run evals/run.py --config rules --split dev       # score, no API key needed
uv run evals/run.py --report                         # the frontier table
```

`sample.py` reports what each slice will support **before** labeling starts. Drawn
proportionally at n=60 the prose slice gets 8 posts and a ±26% interval — unusable, and the
prose-vs-pipe comparison is the evidence the whole cost argument rests on. Hence n=80 with prose
boosted to 20. Finding that out after six hours of labeling would have been expensive; finding
it out from the sampler was free.

## Fixed eval split

[`splits.json`](splits.json) freezes the existing assignments from `labeled.jsonl` and
`sample.json` (sampling seed `20260801`): **53 tune / 27 held-out**, covering all 80 IDs
in `tests/eval_posts.json` exactly once. `dev` remains an alias for `tune`. The runner
uses these ID lists rather than the labels' `split` metadata; do not redraw them after tuning.

The previous tuning round looked at **all 80 posts**. The held-out set therefore overlaps
posts seen during tuning and **is not a clean generalization estimate**. Use the tune set
for future iteration; the all-post CI regression gate also still exposes held-out behavior.

Tune IDs (53):

46858476, 46858532, 46859629, 46859924, 46863917, 46869120, 46870506, 46875351,
46888712, 46893914, 46959004, 47220091, 47220599, 47220965, 47220989, 47223968,
47225525, 47229954, 47232351, 47241526, 47255238, 47256159, 47308369, 47603990,
47605264, 47605460, 47609507, 47610945, 47614308, 47625506, 47632126, 47673074,
47676433, 47975959, 47976872, 47979394, 47980297, 47986820, 48021354, 48023051,
48102189, 48358258, 48362254, 48365334, 48376486, 48747987, 48749084, 48749443,
48752786, 48787393, 48794583, 48804695, 48819370.

Held-out IDs (27):

46857494, 46857529, 46859342, 46861945, 46863837, 46873079, 46903595, 47221096,
47224803, 47230726, 47249983, 47318659, 47603496, 47604760, 47614969, 47976662,
47976769, 47978746, 48067640, 48357761, 48357775, 48357800, 48361945, 48365376,
48372101, 48408853, 48750014.

Score held-out only, with no API calls or run-history writes:

```sh
HN_RAW_DIR=/tmp/hn-eval-corpus .venv/bin/python evals/run.py --config rules --split held-out --dry-run
```

If `data/raw` is absent, rebuild a temporary corpus from `tests/eval_posts.json` using the
corpus shape `{"comments": [{"objectID": id, "comment_text": html.escape(text)}]}` in a JSON
file under `/tmp/hn-eval-corpus`. Escaping the text preserves literal angle brackets and
entities through the runner's HTML-to-text conversion. No fetching is needed.
