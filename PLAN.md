# Build plan — Jul 29 to Sep 13, 2026

37 steps. Sequenced: later ones assume earlier ones.
Labels tell you what is negotiable when the calendar tightens.

- **Ship** — non-negotiable. Without these there is no app and no link to send.
- **Edge** — the differentiator. Cut Ship-work before cutting these.
- **Opt** — drop without regret.

Source of truth: the build-plan artifact. This file is the checklist.

---

## Day zero — Proof of concept (~5 hr)

Its job is to try to **kill the premise**, not to prove you can fetch a URL.

- [ ] P1 · Pull one thread, dump the JSON — 30 min
- [ ] P2 · Read twenty posts, tally the formats — 30 min
- [ ] P3 · Crudest rules pass, two fields only — 1.5 hr
- [ ] P4 · Hand-label ten posts, same two fields — 45 min
- [ ] P5 · Score it, print one honest number — 1.5 hr

**Read the gate honestly:**
- Rules miss a real share → the LLM has genuine work. Proceed.
- Rules get almost everything → premise is dead. Change the source or field set *now*.
- You can't label consistently → tighten the rules before scaling to 60.

Nothing here is throwaway: rules code grows into 05, the ten labels seed 12, the scorer becomes 14.

## Phase 0 — Ground truth first (Jul 29 – Aug 2)

Let the data dictate the schema. **Do not write a prompt yet.**

- [x] 01 · Scaffold the repo — Ship — 30 min
- [ ] 02 · Fetch one thread end to end — Ship — 1 hr
- [ ] 03 · Read 30 posts, write `docs/formats.md` — Edge — 1.5 hr
- [ ] 04 · Define the extraction schema (Pydantic) — Ship — 1 hr

## Phase 1 — Extraction, cheap path first (Aug 3 – Aug 9)

- [ ] 05 · Deterministic parser — Ship — 4 hr
- [ ] 06 · Measure rules coverage *before* adding the LLM — Edge — 1 hr
- [ ] 07 · LLM extractor behind a one-function interface — Ship — 4 hr
- [ ] 08 · Normalization layer — Ship — 2 hr
- [ ] 09 · Write Parquet — Ship — 1 hr

> **Trap (08).** Normalize *before* scoring, and normalize labels and predictions identically.
> Otherwise skills F1 measures your synonym table, not the model.

## Phase 2 — The labeled set and the harness (Aug 10 – Aug 16)

Build this **before** tuning any prompt. Without it you cannot tell improvement from noise.

- [ ] 10 · Stratified sample of 60 posts — Edge — 1 hr
- [ ] 11 · Annotation guide first — Edge — 1 hr
- [ ] 12 · Hand-label all 60 — Edge — 4–6 hr
- [ ] 13 · Split 40 dev / 20 held-out — Edge — 15 min
- [ ] 14 · Per-field scorers — Edge — 3 hr
- [ ] 15 · Runner + results schema (`runs.jsonl`) — Edge — 3 hr
- [ ] 16 · Slice reporting — Edge — 1.5 hr
- [ ] 17 · Baseline run — record it, **do not tune yet** — Edge — 30 min

> **The nullable-field decomposition.** Four outcomes, and averaging them destroys the only
> information you care about:
> - *Extracted correctly* — present, right.
> - *Abstained correctly* — absent, `null` returned. **This is a win.**
> - *Missed* — present, `null` returned. Recoverable; costs coverage.
> - *Hallucinated* — absent, value invented. **The only unrecoverable failure.** Own rate, never averaged.
>
> Report coverage separately from precision-on-attempts.

## Phase 3 — The improvement loop (Aug 17 – Aug 23)

The week that produces your best material.

- [ ] 18 · Build the failure taxonomy — Edge — 3 hr
- [ ] 19 · Fix the largest bucket, re-run, record — Edge — 4 hr
- [ ] 20 · Cost/quality frontier (4 configs, Pareto table) — Edge — 3 hr
- [ ] 21 · Confidence intervals on every number — Edge — 1.5 hr
- [ ] 22 · Threshold gate in CI — Opt — 1.5 hr

> At n=40 a measured 84% carries a 95% interval of roughly **±11 points**. So 84% vs 86% is
> *not* a result. Reporting it as one is the most common error in this discipline.

## Phase 4 — The product surface (Aug 24 – Aug 30)

- [ ] 23 · DuckDB over Parquet — Ship — 2 hr
- [ ] 24 · FastAPI endpoints — Ship — 4 hr
- [ ] 25 · IDF-weighted matching + a matcher eval — Ship — 3 hr
- [ ] 26 · Groundedness check on the generated summary — Edge — 2 hr
- [ ] 27 · Next.js, three pages, then stop — Ship — 6 hr
- [ ] 28 · **A public evals page** — Edge — 3 hr

> **Trap (23).** Cloud Run scales to zero, so every cold start re-reads Parquet over `httpfs`.
> Download to `/tmp` on startup or bake it into the image.

> 28 is the single highest-leverage hour in the plan. Most people bury this in a README.

## Phase 5 — Deploy (Aug 31 – Sep 6)

- [ ] 29 · Dockerfiles for API and web — Ship — 3 hr
- [ ] 30 · Deploy by hand with `gcloud` — Ship — 4 hr
- [ ] 31 · Codify in Terraform, then destroy and re-apply — Ship — 5 hr
- [ ] 32 · Scheduled monthly ingest — Ship — 2 hr
- [ ] 33 · The online half: monitoring, not just evals — Edge — 3 hr

> **Trap (30).** Working first, reproducible second. Terraform for infra you have never stood up
> is how people lose three days to a service-account error they cannot isolate.

## Phase 6 — The story (Sep 7 – Sep 13)

Nobody will read your code. Make the reasoning legible, then rehearse it.

- [ ] 34 · README with real numbers — Ship — 3 hr
- [ ] 35 · The scaling table — Ship — 1.5 hr
- [ ] 36 · One Databricks evening — Opt — 4 hr
- [ ] 37 · Rehearse out loud — Ship — 2 hr

---

## Definition of done

- **Sep 6** — public HTTPS URL, both services, resume-paste working end to end.
- **Sep 13** — evals page live with real numbers and intervals, failure taxonomy with counts,
  README complete. Then **freeze**.

Seven weeks is enough to overbuild. The risk is not running out of time — it is never shipping
because you kept widening. **If a step is not on this list, it waits.**
