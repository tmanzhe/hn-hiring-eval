# Annotation guide

Step 11. Write it before labeling, not while labeling. Otherwise I'll contradict myself around
post 40 and the metrics end up measuring my mood.

Ambiguity I find here is a result, not a problem. "11% of posts are genuinely ambiguous on
salary" says something about the ceiling on any extractor, mine included.

## Calls to make up front

- is `$150k + equity` a salary? is "competitive"?
- does a multi-role post become one row or three?
- is "Rails" a skill, a framework, or both, and do I count both?
- does a nice-to-have count as a required skill?
- is an office city a location, a remote policy, or both?
- hourly rates: convert to annual or leave null?
- a single figure like `$180k`: min, max, or both?

## Rules

One line per answer above. Add rules as new cases come up, and go back and re-check earlier
labels every time I add one.

1. **Salary** is a stated number or range for base pay. "Competitive", equity only, and signing
   bonuses are null. A single figure like `$80k` is min = max = 80000. Amounts are stored raw
   (`150000`, not `150`), with the period as stated. Hourly stays hourly. `normalize.py`
   annualises, the label doesn't.
2. **Currency** is ISO. `$` is USD unless the post says otherwise. `$` on a Canadian post gets
   USD and a `?`.
3. **Multi-role posts** are one row. Skills are the union across roles. If the roles carry
   different ranges, take the first one stated and flag salary `?`.
4. **Seniority** comes from the title. Intern maps to junior. Senior and Sr. map to senior.
   Staff, Principal, Lead, Head of, CTO and co-founder map to staff+. "Founding engineer" and
   years-of-experience alone map to null. Roles at different levels in one post map to null.
5. **Location** is where the job is: a city if one is named, otherwise the region the post
   restricts hiring to ("US", "EU"). Several cities means the first one. A remote role with only
   an HQ mentioned is null.
6. **Remote** is `remote` if working remotely is allowed at all ("NYC or Remote" counts).
   `hybrid` if some office days are required, including "onsite, 3 days a week" and "onsite
   (hybrid OK)". `onsite` only if the post says so. If the post doesn't say, it's null.
7. **Skills** are named technologies: languages, frameworks, databases, clouds and tools the
   role uses or asks for, nice-to-haves included. Concepts ("distributed systems", "ML") are not
   skills. Customers, investors and model vendors named in passing are not skills. Cloud
   sub-services collapse to the provider (ECS goes to AWS, Cloud Run to Google Cloud). Rails is
   Ruby on Rails, and Ruby only counts as its own skill if the post names it on its own.
8. **Not a job posting** (someone looking for work) gets every field null and a note.
9. **Closed posts** get labeled anyway. The extractor sees them too.

## How the labels were made

Claude drafted all 80 from the raw post text only, following the rules above, and never saw
parser or model output. It then did a second pass against the posts, which caught four rows
where it had broken its own rule 7. That's what's in `labeled.jsonl` now, and every row says so:
`verified_by: claude-opus-5-5`, `human_verified: false`.

I haven't gone through them by hand yet. `label.py --verify` is set up for that when I do.

The catch I'm watching: the LLM rungs also run on Claude, so a Claude-made label set might read
posts the same way the model under test does, and that would flatter it. It doesn't matter for
the rules baseline. Before I trust any gap between rules and an LLM config, I'll check the posts
where they disagree by hand.

## The one hard rule

Don't look at model output while labeling. Once I have, it isn't ground truth anymore, it's me
grading my own extractor's homework.
