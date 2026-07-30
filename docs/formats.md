# Format taxonomy

Step 03. No prompt and no schema until this file has real counts in it.

Read 30 top-level comments out of `data/raw/` by hand. For each shape, note roughly how often it
shows up. The schema comes from this. The buckets here also become the slices in every eval run,
which is what makes "84% overall, 61% on prose" a thing I can say.

| Shape                       | Count / 30 | Notes |
| --------------------------- | ---------- | ----- |
| pipe-delimited header line  |            |       |
| prose paragraphs            |            |       |
| bulleted requirements       |            |       |
| multi-role post             |            |       |
| no salary stated            |            |       |
| non-USD salary              |            |       |
| equity only / "competitive" |            |       |
| agency or recruiter spam    |            |       |

## Examples worth keeping

Two or three real comments per shape. These end up as few-shot candidates in step 19 and as the
hard cases in the stratified sample in step 10.
