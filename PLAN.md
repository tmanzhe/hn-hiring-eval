# Build plan, Jul 29 to Sep 13 2026

37 steps, in order. Later ones assume earlier ones.

Labels are for when the calendar gets tight:

- **Ship** — no app and no link without these.
- **Edge** — the part nobody else has. Cut Ship work before cutting these.
- **Opt** — drop it, no regrets.

Full reasoning lives in the build-plan artifact. This is just the checklist.

---

## Day zero, proof of concept (~5 hr)

Job here is to try to kill the premise before spending seven weeks on it.

- [x] P1 · pull one thread, dump the JSON — 30 min
- [ ] P2 · read twenty posts, tally the formats — 30 min
- [x] P3 · crudest rules pass, two fields — 1.5 hr
- [ ] P4 · hand-label ten posts, same two fields — 45 min  ← template in `evals/poc_labels.jsonl`
- [ ] P5 · score it, print one honest number — 1.5 hr  ← script done, needs P4 first

Reading the gate:

- rules miss a real share → LLM has actual work to do, keep going
- rules get nearly everything → premise is dead, change the source or the field set now
- can't label consistently → tighten the annotation rules before doing 60 of them

None of it is throwaway. The rules code grows into 05, the ten labels seed 12, the scorer
becomes 14.

## Phase 0, ground truth first (Jul 29 – Aug 2)

Read the data, let it pick the schema. No prompt yet.

- [x] 01 · scaffold the repo — Ship — 30 min
- [ ] 02 · fetch one thread end to end — Ship — 1 hr
- [ ] 03 · read 30 posts, write `docs/formats.md` — Edge — 1.5 hr
- [ ] 04 · define the Pydantic schema — Ship — 1 hr

## Phase 1, extraction, cheap path first (Aug 3 – Aug 9)

- [ ] 05 · deterministic parser — Ship — 4 hr
- [ ] 06 · measure rules coverage before adding the LLM — Edge — 1 hr
- [ ] 07 · LLM extractor behind one function — Ship — 4 hr
- [ ] 08 · normalization layer — Ship — 2 hr
- [ ] 09 · write Parquet — Ship — 1 hr

Trap on 08: normalize before scoring, and normalize labels and predictions the same way. Skip
that and skills F1 is measuring the synonym table, not the model. It'll drift every time I add
an entry.

## Phase 2, the labeled set and the harness (Aug 10 – Aug 16)

Comes before any prompt tuning. Without it there's no way to tell a real gain from noise.

- [ ] 10 · stratified sample of 60 posts — Edge — 1 hr
- [ ] 11 · annotation guide, written first — Edge — 1 hr
- [ ] 12 · hand-label all 60 — Edge — 4–6 hr
- [ ] 13 · split 40 dev / 20 held-out — Edge — 15 min
- [ ] 14 · per-field scorers — Edge — 3 hr
- [ ] 15 · runner + results schema — Edge — 3 hr
- [ ] 16 · slice reporting — Edge — 1.5 hr
- [ ] 17 · baseline run, recorded, no tuning — Edge — 30 min

Four outcomes for any field that's allowed to be absent. Averaging them throws away the only
thing I care about:

- extracted correctly, value present and right
- abstained correctly, absent in the post and null came back. that's a win, count it as one
- missed, present in the post and null came back. recoverable, costs coverage
- hallucinated, absent in the post and a value got invented. the one that can't be fixed
  downstream, so it gets its own rate and never goes into an average

Coverage and precision-on-attempts are separate numbers. A model that abstains on 60% and is
never wrong beats one that always answers and is wrong a third of the time.

## Phase 3, the improvement loop (Aug 17 – Aug 23)

- [ ] 18 · failure taxonomy, bucketed by cause, with counts — Edge — 3 hr
- [ ] 19 · fix the biggest bucket, re-run, record — Edge — 4 hr
- [ ] 20 · cost/quality frontier, four configs — Edge — 3 hr
- [ ] 21 · confidence intervals on everything — Edge — 1.5 hr
- [ ] 22 · threshold gate in CI — Opt — 1.5 hr

At n=40 a measured 84% has a 95% interval of about ±11 points. So 84% vs 86% isn't a result.
Calling it one is the most common mistake in this whole area.

## Phase 4, the product surface (Aug 24 – Aug 30)

- [ ] 23 · DuckDB over Parquet — Ship — 2 hr
- [ ] 24 · FastAPI endpoints — Ship — 4 hr
- [ ] 25 · IDF-weighted matching, plus an eval for the matcher — Ship — 3 hr
- [ ] 26 · groundedness check on the generated summary — Edge — 2 hr
- [ ] 27 · Next.js, three pages, then stop — Ship — 6 hr
- [ ] 28 · public evals page — Edge — 3 hr

Trap on 23: Cloud Run scales to zero, so every cold start re-reads Parquet over httpfs. Pull it
to /tmp on startup or bake it into the image.

28 is the highest-leverage hour in the plan. Everyone else buries this in a README.

## Phase 5, deploy (Aug 31 – Sep 6)

- [ ] 29 · Dockerfiles for API and web — Ship — 3 hr
- [ ] 30 · deploy by hand with gcloud — Ship — 4 hr
- [ ] 31 · codify in Terraform, then destroy and re-apply — Ship — 5 hr
- [ ] 32 · scheduled monthly ingest — Ship — 2 hr
- [ ] 33 · online monitoring, separate from the offline evals — Edge — 3 hr

Trap on 30: working first, reproducible second. Writing Terraform for infra I've never stood up
by hand is how three days disappear into a service-account error I can't isolate.

## Phase 6, the story (Sep 7 – Sep 13)

Nobody reads the code. Make the reasoning easy to follow, then practice saying it.

- [ ] 34 · README with real numbers — Ship — 3 hr
- [ ] 35 · scaling table — Ship — 1.5 hr
- [ ] 36 · one Databricks evening — Opt — 4 hr
- [ ] 37 · rehearse out loud — Ship — 2 hr

---

## Done means

- **Sep 6** — public HTTPS URL, both services up, resume paste works end to end.
- **Sep 13** — evals page live with real numbers and intervals, failure taxonomy with counts,
  README done. Then freeze.

Seven weeks is enough time to overbuild. The risk isn't running out of time, it's never shipping
because I kept widening the scope. Anything not on this list waits.
