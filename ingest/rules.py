"""Step 05. The deterministic parser.

Replaces rules_poc.py. Produces an Extraction plus a per-field confidence flag, so the pipeline
knows which posts to hand to the model.

The rule this file lives by: **abstain rather than guess.** A None costs coverage and is
recoverable downstream. A confidently wrong number is not. Every branch below that could go
either way returns None.
"""

import re

from ingest.schema import Extraction

# --- salary ------------------------------------------------------------------------------

CURRENCY = {"$": "USD", "usd": "USD", "€": "EUR", "eur": "EUR", "£": "GBP", "gbp": "GBP"}
DASH = r"(?:[-–—~]|\s+to\s+)"
NUM = r"\d{1,3}(?:,\d{3})*(?:\.\d+)?"
CUR_CLASS = r"\$|USD|EUR|GBP|€|£"

RANGE = re.compile(
    rf"(?P<cur>{CUR_CLASS})\s?"
    rf"(?P<lo>{NUM})\s?(?P<lok>[kK])?"
    rf"\s*{DASH}\s*"
    rf"(?:{CUR_CLASS})?\s?(?P<hi>{NUM})\s?(?P<hik>[kK])?",
    re.IGNORECASE,
)

# A single figure with no range: "| Full-Time | $190k |". Real, and common enough to matter —
# it was 2 of the 6 abstentions I sampled.
SINGLE = re.compile(rf"(?P<cur>{CUR_CLASS})\s?(?P<lo>{NUM})\s?(?P<lok>[kK])?", re.IGNORECASE)

# "/hr", "per hour", "annually", "/mo"
PERIOD_AFTER = re.compile(
    r"\s*(?:/|\s+per\s+)?\s*(hr|hour|hourly|yr|year|yearly|annual(?:ly)?|mo|month|monthly)\b",
    re.IGNORECASE,
)
PERIOD_MAP = {
    "hr": "hour", "hour": "hour", "hourly": "hour",
    "yr": "year", "year": "year", "yearly": "year", "annual": "year", "annually": "year",
    "mo": "month", "month": "month", "monthly": "month",
}

# "$43B/day", "$30 trillion in assets", "$1 billion through our platform" are not salaries.
SCALE_WORD = re.compile(r"\s*(?:b|bn|m|mm|billion|million|trillion)\b", re.IGNORECASE)

# What a plausible figure looks like once normalised to a period.
PLAUSIBLE = {"year": (10_000, 2_000_000), "month": (500, 200_000), "hour": (5, 2_000)}


def _to_number(raw, k_suffix, trailing_k):
    """`trailing_k` carries the k from the upper bound back to the lower one: in "$140-200k"
    the k applies to both sides, which is what rules_poc got wrong."""
    n = float(raw.replace(",", ""))
    if k_suffix or trailing_k:
        n *= 1000
    return round(n)


def _resolve(lo, hi, cur_raw, tail, infer_hourly=True):
    """Shared tail-checking for both the range and single-figure paths. Returns a tuple or None.

    `infer_hourly` is off for single figures. "$30-120" is recognisably an hourly range; a bare
    "$500" is far more often a referral bounty, a stipend, or a product price than a wage, so
    single figures have to be either explicitly periodised or large enough to be an annual
    salary. Guessing there is how "Bounty: $500 for each referral" becomes a $500/hr job.
    """
    # "$43B/day" — a scale word right after the number means this is revenue, not pay.
    if SCALE_WORD.match(tail):
        return None

    period = None
    if pm := PERIOD_AFTER.match(tail):
        period = PERIOD_MAP[pm[1].lower().rstrip(".")]

    if lo > hi:
        return None

    # No explicit period: infer only where it's unambiguous, otherwise abstain.
    if period is None:
        if lo >= 10_000:
            period = "year"
        elif infer_hourly and hi <= 500:
            period = "hour"
        else:
            return None  # the $3.5k-$4.9k band. genuinely ambiguous, so say nothing.

    low, high = PLAUSIBLE[period]
    if not (low <= lo <= high and low <= hi <= high):
        return None

    return lo, hi, CURRENCY.get(cur_raw.lower(), cur_raw.upper()), period


def find_salary(text):
    """Returns (min, max, currency, period). Any element may be None. All-None means the post
    doesn't state a salary I can trust, which is a legitimate answer."""
    for m in RANGE.finditer(text):
        hi_k = bool(m["hik"])
        got = _resolve(
            _to_number(m["lo"], bool(m["lok"]), hi_k and not m["lok"]),
            _to_number(m["hi"], hi_k, False),
            m["cur"],
            text[m.end() : m.end() + 24],
        )
        if got:
            return got

    # No range found. Fall back to a single figure, treating it as min == max.
    #
    # ANNOTATION.md has to confirm this convention — "a single figure like $190k: min, max, or
    # both?" is an open question there, and if the answer is "min only, max None" this is a
    # one-line change. Labels and this parser have to agree before step 12.
    for m in SINGLE.finditer(text):
        n = _to_number(m["lo"], bool(m["lok"]), False)
        if got := _resolve(n, n, m["cur"], text[m.end() : m.end() + 24], infer_hourly=False):
            return got

    return None, None, None, None


# --- everything else ---------------------------------------------------------------------

SKILLS = {
    "python", "typescript", "javascript", "golang", "go", "rust", "java", "ruby", "scala",
    "kotlin", "swift", "c++", "react", "vue", "angular", "next.js", "svelte", "django",
    "flask", "fastapi", "rails", "node.js", "postgres", "postgresql", "mysql", "mongodb",
    "redis", "elasticsearch", "kafka", "rabbitmq", "spark", "airflow", "dbt", "snowflake",
    "databricks", "kubernetes", "k8s", "docker", "terraform", "ansible", "aws", "gcp",
    "azure", "graphql", "grpc", "pytorch", "tensorflow", "llm", "rag",
}

REMOTE = [
    (re.compile(r"\bhybrid\b", re.IGNORECASE), "hybrid"),
    (re.compile(r"\b(?:remote|wfh|distributed|anywhere)\b", re.IGNORECASE), "remote"),
    (re.compile(r"\b(?:onsite|on-site|in[- ]office|in[- ]person)\b", re.IGNORECASE), "onsite"),
]

SENIORITY = [
    (re.compile(r"\b(?:staff|principal|distinguished|architect|director|vp|head of)\b", re.IGNORECASE), "staff+"),
    (re.compile(r"\b(?:senior|sr\.?|lead)\b", re.IGNORECASE), "senior"),
    (re.compile(r"\b(?:junior|jr\.?|entry[- ]level|new grad|graduate|intern)\b", re.IGNORECASE), "junior"),
    (re.compile(r"\b(?:mid[- ]level|intermediate)\b", re.IGNORECASE), "mid"),
]

VISA_YES = re.compile(r"\bvisa\b[^.\n]{0,40}\b(?:ok|yes|sponsor|available|support)", re.IGNORECASE)
VISA_NO = re.compile(r"\b(?:no visa|visa[^.\n]{0,20}not|cannot sponsor|no sponsorship)", re.IGNORECASE)

ROLE_HINT = re.compile(
    r"\b(?:engineer|developer|scientist|designer|manager|architect|analyst|researcher|"
    r"lead|director|devops|sre|founding)\b",
    re.IGNORECASE,
)
LOCATION_HINT = re.compile(
    r"\b(?:remote|hybrid|onsite|on-site|usa?|uk|eu|europe|latam|apac|canada|nyc|sf|"
    r"san francisco|new york|london|berlin|austin|seattle|boston|toronto|amsterdam)\b",
    re.IGNORECASE,
)


def _header(text):
    """First non-empty line. The pipe-delimited convention lives here when it's used at all."""
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def find_skills(text):
    low = text.lower()
    out = set()
    for s in SKILLS:
        if re.search(rf"(?<![\w.+#]){re.escape(s)}(?![\w+#])", low):
            out.add(s)
    return sorted(out)


def _first_match(patterns, text):
    for pattern, value in patterns:
        if pattern.search(text):
            return value
    return None


def parse(text):
    """Best-effort structured read of one posting. Returns (Extraction, confidence dict)."""
    header = _header(text)
    parts = [p.strip() for p in header.split("|") if p.strip()] if "|" in header else []

    company = parts[0] if len(parts) >= 3 else None
    if company and (len(company) > 60 or ROLE_HINT.search(company)):
        company = None  # header didn't lead with a company name

    roles = [p for p in parts[1:] if ROLE_HINT.search(p)][:3]
    location = next(
        (p for p in parts[1:] if LOCATION_HINT.search(p) and not ROLE_HINT.search(p)), None
    )

    lo, hi, cur, period = find_salary(text)

    ex = Extraction(
        company=company,
        role_titles=roles,
        location=location,
        remote=_first_match(REMOTE, header) or _first_match(REMOTE, text),
        salary_min=lo,
        salary_max=hi,
        salary_currency=cur,
        salary_period=period,
        skills=find_skills(text),
        seniority=_first_match(SENIORITY, header) or _first_match(SENIORITY, text),
        visa_sponsor=True if VISA_YES.search(text) else (False if VISA_NO.search(text) else None),
    )

    confidence = {
        "company": company is not None and bool(parts),
        "salary": lo is not None,
        "skills": len(ex.skills) >= 2,
        "remote": ex.remote is not None,
        "seniority": ex.seniority is not None,
    }
    return ex, confidence


def is_confident(confidence):
    """Whether rules handled this post well enough to skip the model.

    Salary and skills are the two fields the whole project is measured on, so both have to land.
    This threshold is what step 06 measures and what step 20's cost claim rests on — it's a
    dial, and moving it moves the cost/quality tradeoff.
    """
    return confidence["salary"] and confidence["skills"]
