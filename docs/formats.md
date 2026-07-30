# Format taxonomy

**Step 03. Do not write a prompt or a schema before this file has real counts in it.**

Read 30 top-level comments from `data/raw/` by hand. For each shape you see, record roughly how
common it is. This document is where the schema comes from, and the buckets here become the
`slices` in every eval run — which is what makes "84% overall, 61% on prose" possible to say.

Skipping this is why most extraction projects end up measuring the wrong fields.

| Shape                        | Count / 30 | Notes |
| ---------------------------- | ---------- | ----- |
| Pipe-delimited header line   |            |       |
| Prose paragraphs             |            |       |
| Bulleted requirement list    |            |       |
| Multi-role post              |            |       |
| No salary stated             |            |       |
| Non-USD salary               |            |       |
| Equity-only / "competitive"  |            |       |
| Agency / recruiter spam      |            |       |

## Examples worth keeping

Paste 2–3 real comments per shape here. These become your few-shot candidates in step 19 and
your hard cases in the stratified sample in step 10.
