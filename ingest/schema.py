"""Step 04. The extraction schema.

Draft. Step 03 (reading 30 posts and filling in docs/formats.md) can still add or drop fields —
that's the point of doing 03 before locking this. Every change here is a change to labels too,
so change it before step 12, not after.

Two models on purpose:

  Extraction  what the LLM is asked for. Only fields readable from the post text.
  Posting     the row that lands in Parquet. Extraction plus what the pipeline knows.

Asking a model for `thread_date` or `extracted_by` invites it to make something up about
provenance. It can't know either. The pipeline sets them.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict

Remote = Literal["remote", "hybrid", "onsite"]
Seniority = Literal["junior", "mid", "senior", "staff+"]
Period = Literal["year", "month", "hour"]
Source = Literal["rules", "llm"]


class Extraction(BaseModel):
    """What one posting says. Anything the post doesn't state is None.

    Every optional field must be allowed to come back None. Forcing a value is how I'd
    manufacture hallucinations, and abstaining correctly is a win I want to be able to score
    (see the four outcomes in evals/score_poc.py).

    No Field(ge=...) / max_length constraints anywhere — structured outputs rejects numeric and
    string constraints, and I want this model to double as the JSON schema for the API call.
    """

    model_config = ConfigDict(extra="forbid")  # additionalProperties: false

    company: str | None = None
    role_titles: list[str] = []
    location: str | None = None
    remote: Remote | None = None

    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str | None = None
    # Not in the original spec. Added because the corpus actually contains "$30-120/hr" and
    # "$3.5k-$4.9k/mo" alongside "$180k-$230k". Without this, an hourly rate lands in the same
    # column as an annual salary and every downstream number is quietly wrong. The rules_poc
    # regex already gets this wrong on post 48900749 — that's the evidence.
    salary_period: Period | None = None

    skills: list[str] = []
    seniority: Seniority | None = None
    visa_sponsor: bool | None = None


class Posting(Extraction):
    """One row of the Parquet file."""

    comment_id: int
    thread_date: date
    # Lets me score the rules path and the LLM path separately, which is the whole basis of
    # step 20's cost comparison.
    extracted_by: Source


# Open questions for ANNOTATION.md, all visible in the first 20 posts of the July thread:
#   - "$0 + equity" and "competitive" — salary present, or None?
#   - "$140-200k" — the k applies to both sides. rules_poc currently reads lo as 140.
#   - multi-role posts — one row or three?
#   - "$150k for senior band" alongside a base range — which numbers win?
