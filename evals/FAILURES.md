# What breaks, and why

Rules baseline against the 53 dev posts. Every miss got bucketed by cause, not by field, because
"location is 8% precise" tells you nothing about what to fix and "the parser copies REMOTE (US)
into the location column" tells you exactly what to fix.

Held-out (27 posts) got looked at twice: once for the baseline, once after the fix. Nothing
below was tuned against it.

## Location: 43 misses on dev at baseline

| Cause                                              | Count |
| -------------------------------------------------- | ----: |
| work arrangement copied into the slot              |    33 |
| no pipe header, the place is only in the prose     |     9 |
| different spelling or granularity ("NYC" vs "New York") |     1 |

This one was a no-brainer. The header slot usually holds the place and the arrangement mashed
together: `Hybrid in Seattle, WA`, `Onsite (Burlingame, CA)`, `REMOTE (US)`. The parser was
copying the whole thing. The arrangement already has its own field (`remote`), so the fix just
strips it out of the location (`ingest/rules.py`, `_clean_location`).

| Location          | Before | After | 95% CI after | Halluc before | Halluc after |
| ----------------- | -----: | ----: | -----------: | ------------: | -----------: |
| dev (n=53)        |   8.1% | 82.1% |     64 to 92 |          9.4% |         1.9% |
| held-out (n=27)   |  17.4% | 70.6% |     47 to 87 |         14.8% |         3.7% |

Held-out jumped too, 17% to 71%, on posts I never tuned against. So it's not me overfitting to
53 posts. Coverage went down
(70% to 53% on dev) because a slot that only said `Remote` used to count as an answer and now
correctly comes back null. I'll take fewer answers that are right over more answers that are
junk.

After the fix, 14 of the 19 remaining misses come back null because the place isn't in the
header slot at all. Most are headerless prose posts, and regex has nothing to grab there.
That's the LLM fallback's job, and it's the case that justifies paying for it.

## Company: 18 misses on dev

| Cause                                          | Count |
| ---------------------------------------------- | ----: |
| no pipe header, the name is only in the prose  |    14 |
| suffix kept: `(YC S17)`, a URL, a tagline      |     3 |
| header led with the city, read as the company  |     1 |

Same story as location. Most of it is headerless posts. The suffix thing is a cheap fix and
it's next.

## Seniority: 71.7% on dev

| Cause                                                        | Count |
| ------------------------------------------------------------ | ----: |
| picked up a level word somewhere in the post, label is null  |    12 |
| wrong tier: "Lead" read as senior, "Architect" as staff+      |     3 |

The parser grabs the first "senior" or "staff" it sees anywhere. Posts that list roles at five
different levels get labeled null (ANNOTATION.md rule 4), and the parser confidently picks one
of them. This is a judgment call that regex honestly shouldn't be making.

## Skills: F1 0.718 on dev, recall is the problem

75 labeled skills missed vs 21 extra ones. The parser matches a fixed list of about 60 terms,
so anything off the list is invisible to it: Codex, HubSpot, eBPF, NumPy, Claude Code. The
extras are mostly `llm` (4), which the labels treat as a concept, not a skill.

## Salary: one real invention

Held-out salary precision is 88.9% (8 of 9, CI 56 to 98). The one invented value is Odoo's
€10k signing bonus, read as pay. Dev is 6 for 6, which sounds great until you see the interval:
61 to 100.

A scoring bug turned up here too. Predictions get annualized by `normalize()`, labels were
compared raw, so `$30-40/hr` scored as wrong even when the parser nailed it. `run.py` now puts
the label through the same conversion. Every number in this file uses the fixed scorer.

## Remote: 88.7% on dev

4 of the 6 misses are posts like `Toronto, ON (Hybrid) + Remote` where remote is allowed but the
parser checks for "hybrid" first. Small, known, not fixed yet.

## What I'd fix next, in order

1. Headerless prose posts. This is the biggest bucket across company and location both, and
   it's the one regex can't touch. It needs the LLM configs, which need an API key.
2. Company suffixes. Cheap, three posts.
3. Seniority on multi-level posts. Probably also an LLM call, since it's reading comprehension.
