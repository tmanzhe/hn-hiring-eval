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
NUM = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
CUR_CLASS = r"\$|USD|EUR|GBP|€|£"

RANGE = re.compile(
    rf"(?P<cur>{CUR_CLASS})\s?"
    rf"(?P<lo>{NUM})\s?(?P<lok>[kK])?"
    rf"\s*{DASH}\s*"
    rf"(?:{CUR_CLASS})?\s?(?P<hi>{NUM})\s?(?P<hik>[kK])?",
    re.IGNORECASE,
)

# European headers often put the currency after the range: "55 - 85k EUR".
SUFFIX_RANGE = re.compile(
    rf"(?<![\w.,])(?P<lo>{NUM})\s?(?P<lok>[kK])?\s*{DASH}\s*"
    rf"(?P<hi>{NUM})\s?(?P<hik>[kK])?\s*(?P<cur>USD|EUR|GBP|€|£)\b",
    re.IGNORECASE,
)
NON_BASE_PAY = re.compile(
    r"(?:sign(?:ing|[- ]on)?|referral|learning|relocation)\s+(?:bonus|budget|allowance)"
    r"|(?:bonus|bounty|budget)\s*[:=]?\s*$",
    re.IGNORECASE,
)

# A single figure with no range: "| Full-Time | $190k |". Real, and common enough to matter —
# it was 2 of the 6 abstentions I sampled.
SINGLE = re.compile(rf"(?P<cur>{CUR_CLASS})\s?(?P<lo>{NUM})\s?(?P<lok>[kK])?", re.IGNORECASE)

# A single figure is not always a point. "up to ~$750k" is a ceiling with an unknown floor;
# reporting min == max there asserts a floor the post never stated. Found by eyeballing the
# top of /api/jobs sorted by salary, which is exactly what that endpoint is good for.
BOUND_BEFORE = re.compile(
    r"(?:(?P<upper>up\s+to|as\s+high\s+as|max(?:imum)?\s+of|no\s+more\s+than)"
    r"|(?P<lower>from|starting\s+at|at\s+least|min(?:imum)?\s+of|north\s+of|\d+\+))"
    r"[\s~≈]*$",
    re.IGNORECASE,
)

# "/hr", "per hour", "annually", "/mo"
PERIOD_AFTER = re.compile(
    r"\s*(?:/|\s+per\s+)?\s*(hr|hour|hourly|yr|year|yearly|annual(?:ly)?|mo|month|monthly)\b",
    re.IGNORECASE,
)
PERIOD_MAP = {
    "hr": "hour",
    "hour": "hour",
    "hourly": "hour",
    "yr": "year",
    "year": "year",
    "yearly": "year",
    "annual": "year",
    "annually": "year",
    "mo": "month",
    "month": "month",
    "monthly": "month",
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
    # Sort all formats together so multi-role posts retain the first stated range.
    ranges = sorted([*RANGE.finditer(text), *SUFFIX_RANGE.finditer(text)], key=lambda m: m.start())
    for m in ranges:
        if NON_BASE_PAY.search(text[m.end() : m.end() + 40]) or NON_BASE_PAY.search(
            text[max(0, m.start() - 30) : m.start()]
        ):
            continue
        hi_k = bool(m["hik"])
        got = _resolve(
            _to_number(m["lo"], bool(m["lok"]), hi_k and not m["lok"]),
            _to_number(m["hi"], hi_k, False),
            m["cur"],
            text[m.end() : m.end() + 24],
        )
        if got:
            return got

    # No range found. Fall back to a single figure.
    #
    # A bare "$190k" becomes min == max. ANNOTATION.md has to confirm that convention — "a
    # single figure: min, max, or both?" is an open question there, and labels and this parser
    # have to agree before step 12.
    #
    # But a figure preceded by "up to" or "starting at" is NOT a point, and that isn't a
    # convention question — it's what the post says. Reporting min == max for "up to $750k"
    # asserts a floor the post never stated.
    for m in SINGLE.finditer(text):
        context = text[max(0, m.start() - 30) : m.start()]
        tail = text[m.end() : m.end() + 40]
        if NON_BASE_PAY.search(tail) or NON_BASE_PAY.search(context):
            continue
        n = _to_number(m["lo"], bool(m["lok"]), False)
        got = _resolve(n, n, m["cur"], text[m.end() : m.end() + 24], infer_hourly=False)
        if not got:
            continue

        lo, hi, cur, period = got
        if bound := BOUND_BEFORE.search(text[max(0, m.start() - 20) : m.start()]):
            if bound["upper"]:
                return None, hi, cur, period
            return lo, None, cur, period
        return got

    return None, None, None, None


# --- everything else ---------------------------------------------------------------------

SKILLS = {
    "python",
    "typescript",
    "javascript",
    "golang",
    "go",
    "rust",
    "java",
    "ruby",
    "scala",
    "kotlin",
    "swift",
    "c++",
    "react",
    "vue",
    "angular",
    "next.js",
    "svelte",
    "django",
    "flask",
    "fastapi",
    "rails",
    "node.js",
    "postgres",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "elasticsearch",
    "kafka",
    "rabbitmq",
    "spark",
    "airflow",
    "dbt",
    "snowflake",
    "databricks",
    "kubernetes",
    "k8s",
    "docker",
    "terraform",
    "ansible",
    "aws",
    "gcp",
    "azure",
    "graphql",
    "grpc",
    "pytorch",
    "tensorflow",
    "scylladb",
    "datadog",
    "helm",
    "google cloud",
    "cypress",
    "playwright",
    "nestjs",
    "cursor",
    "claude",
    "codex",
    "metal",
    "arkit",
    "core ml",
    "duckdb",
    "bigquery",
    "hasura",
    "trigger.dev",
    "pulumi",
    "django rest framework",
    "postgis",
    "celery",
    "hubspot",
    "twilio",
    "sql",
    "lldb",
    "llvm",
    "express",
    "sidekiq",
    "ios",
    "r",
    "qt",
    "scikit-learn",
    "claude code",
    "linux",
    "azure devops",
    "elk",
    "prometheus",
    "grafana",
    "argo cd",
    "webrtc",
    "sveltekit",
    "tailwind css",
    "laravel",
    "gong",
    "numpy",
    "pandas",
    "ray",
    "tengo",
    "parquet",
    "datafusion",
    "polars",
    "pnpm",
    "turborepo",
    "react native",
    "expo",
    "hono",
    "cloudflare workers",
    "benthos",
    "mcp",
    "langchain",
    "llamaindex",
    "hugging face",
    "apollo",
    "prisma",
    "shadcn/ui",
    "nextauth",
    "anthropic sdk",
    "caprover",
    "docker swarm",
    "auth0",
    "tigerdata",
    "dagster",
    "c",
    "ebpf",
    "flutter",
    "dart",
    "firebase",
    "jaspr",
    "oauth",
    "saml",
    "oidc",
    "elixir",
    "phoenix",
    "absinthe",
}

REMOTE = [
    (re.compile(r"\bhybrid\b", re.IGNORECASE), "hybrid"),
    (re.compile(r"\b(?:remote|wfh|distributed|anywhere)\b", re.IGNORECASE), "remote"),
    (re.compile(r"\b(?:onsite|on-site|in[- ]office|in[- ]person)\b", re.IGNORECASE), "onsite"),
]

VISA_YES = re.compile(r"\bvisa\b[^.\n]{0,40}\b(?:ok|yes|sponsor|available|support)", re.IGNORECASE)
VISA_NO = re.compile(
    r"\b(?:no visa|visa[^.\n]{0,20}not|cannot sponsor|no sponsorship)", re.IGNORECASE
)

ROLE_HINT = re.compile(
    r"\b(?:engineers?|developers?|scientists?|designers?|managers?|architect|analyst|researcher|"
    r"lead|director|devops|sre|founding|engineering|co-founder|cto|intern|eng)\b",
    re.IGNORECASE,
)
LOCATION_HINT = re.compile(
    r"\b(?:remote|hybrid|onsite|on-site|usa?|uk|eu|europe|latam|apac|canada|nyc|sf|"
    r"san francisco|new york|london|berlin|austin|seattle|boston|toronto|amsterdam|"
    r"paris|bilbao|san mateo|kirkland|durham|pinehurst|cologne|vancouver|denver|"
    r"boulder|chicago|hong kong|north america|latin america|germany|spain|ireland)\b",
    re.IGNORECASE,
)


# The header's location slot usually carries the work arrangement too: "Hybrid in Seattle, WA",
# "REMOTE (US)", "Onsite (Burlingame, CA)". Scoring the rules baseline showed that was most of
# the location misses (evals/FAILURES.md), so the slot gets split and the arrangement words go.
_LOC_SPLIT = re.compile(r"\s/\s|[()+]|\bor\b", re.IGNORECASE)
_LOC_NOISE = re.compile(
    r"\b(?:remote|hybrid|onsite|on-site|in[- ]office|in[- ]person|wfh|only|part|preferred|"
    r"fully|overlap|friendly|time ?zones?|hours|days?|week|\d+(?:-\d+)?)\b|-(?=\s|$)",
    re.IGNORECASE,
)


def _clean_location(part):
    """The place in a location slot, with the remote/hybrid/onsite wording stripped. None if
    nothing but the arrangement was there. HQ mentions are dropped: a remote role with an HQ
    city isn't located there (ANNOTATION.md rule 5)."""
    # A preferred timezone is not a hiring restriction. Keep a later office city if present.
    part = re.sub(
        r",\s*(?:with occasional|(?:\w+\s+)?hours|\d+\s*days?[/ ].*).*",
        "",
        part,
        flags=re.IGNORECASE,
    )
    part = re.sub(r"\s+via EOR.*", "", part, flags=re.IGNORECASE)
    # In a city list use the first city; country/region lists remain intact.
    part = re.sub(r"\bSF(?=/)", "San Francisco", part)
    if re.match(r"San Francisco/", part):
        return "San Francisco"
    if m := re.search(r"ONSITE in ([A-Z][a-z]+, [A-Z]{2})", part):
        return m[1]
    for chunk in _LOC_SPLIT.split(part):
        if re.search(r"\bpreferred\b", chunk, re.IGNORECASE):
            continue
        if re.search(r"\bHQ\b|meet-?ups?", chunk, re.IGNORECASE):
            continue
        chunk = _LOC_NOISE.sub(" ", chunk.replace("/", ", ").replace("&", ","))
        chunk = re.sub(r"^\s*in\b", " ", chunk.strip(), flags=re.IGNORECASE)
        chunk = re.sub(r"\s+", " ", chunk).strip(" ,;:-")
        chunk = re.sub(r"\s*,\s*(?:,\s*)*", ", ", chunk)
        if re.search(r"[A-Za-z]{2}", chunk):
            return chunk
    return None


def _header(text):
    """First non-empty line. The pipe-delimited convention lives here when it's used at all."""
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


# Aliases belong to extraction, not the shared scoring normalizer.
SKILL_ALIASES = {
    "nextjs": "next.js",
    "nodejs": "node.js",
    "node": "node.js",
    "vue.js": "vue",
    "react.js": "react",
    "express.js": "express",
    "js": "javascript",
    "ts": "typescript",
    "sklearn": "scikit-learn",
    "tailwindcss": "tailwind css",
    "tailwind": "tailwind css",
    "bpf": "ebpf",
    "argocd": "argo cd",
    "coreml": "core ml",
    "turbo": "turborepo",
    "django rest api": "django rest framework",
    "fast api": "fastapi",
}


def find_skills(text):
    # URLs and email addresses are links, not evidence of a technology requirement.
    text = re.sub(r"https?://\S+|[\w.+-]+@[\w.-]+", " ", text)
    # Customer/investor lists and founders' past employers are not the role's stack.
    text = re.sub(
        r"[^\n]*(?:experience at companies|our (?:customers|investors):)[^\n]*",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\b(?:R&D|bare[- ]metal|CLAUDE\.md)\b", " ", text, flags=re.IGNORECASE)
    # 'Express yourself' is not Express.js; SDK/provider names need integration evidence.
    text = re.sub(r"\bexpress (?:yourself|themselves|interest)\b", " ", text, flags=re.IGNORECASE)
    low = text.lower()
    out = set()
    for s in SKILLS | SKILL_ALIASES.keys():
        # R and C are case-sensitive; ordinary "go" is a verb, Golang is unambiguous.
        haystack = text if s in {"go", "r", "c"} else low
        token = s.capitalize() if s in {"go", "r", "c"} else s
        if s == "r":
            haystack = re.sub(r"\bR\.(?=\s+[A-Z])", " ", haystack)
        if s == "express":
            haystack = re.sub(r"\bexpress (?:your|their|an|our)\b", " ", haystack)
        if re.search(rf"(?<![\w.+#]){re.escape(token)}(?![\w+#])", haystack):
            out.add(SKILL_ALIASES.get(s, s))
    if "openai" in low and re.search(
        r"\b(?:integrations? with|OpenAI API|OpenAI SDK)\b", text, re.IGNORECASE
    ):
        out.add("openai")
    # Composite names do not imply independent technologies.
    for composite, base in [
        ("react native", "react"),
        ("claude code", "claude"),
        ("docker swarm", "docker"),
    ]:
        if composite in out and not re.search(
            rf"(?<![\w.]){base}(?![\w.])(?! {composite[len(base) + 1 :]})", low
        ):
            out.discard(base)
    if "rails" in out and not re.search(r"\bruby\b(?![ /]+(?:on[ ]+)?rails)", low):
        out.discard("ruby")
    return sorted(out)


def _first_match(patterns, text):
    for pattern, value in patterns:
        if pattern.search(text):
            return value
    return None


def _looks_like_place(value):
    return bool(
        LOCATION_HINT.search(value)
        or re.fullmatch(r"[A-Z][\w .'-]+,\s*(?:[A-Z]{2}|[A-Z][a-z]+)", value)
    )


def _company_name(value):
    value = re.sub(r"\s*\([^)]*\)\s*", " ", value).strip()
    if (
        not value
        or len(value) > 60
        or ROLE_HINT.search(value)
        or _looks_like_place(value)
        or re.search(
            r"https?://|[$€£]|\b(?:remote|hybrid|onsite|full[- ]?time)\b", value, re.IGNORECASE
        )
    ):
        return None
    return value


def find_company(text):
    first = _header(text)
    if (
        "|" not in first
        and len(first) <= 50
        and not re.search(
            r"[.!?:]|\b(?:we|hello|hiring|join|looking|welcome)\b", first, re.IGNORECASE
        )
        and (company := _company_name(first))
    ):
        return company
    # Handle both company-first and role/location-first headers, and repeated job headers.
    for line in text.splitlines():
        slots = [p.strip() for p in line.split("|") if p.strip()]
        if len(slots) >= 2:
            for slot in slots[:2]:
                if company := _company_name(slot):
                    return company
    if (m := re.search(r"^COMPANY:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)) and (
        company := _company_name(m[1])
    ):
        return company
    first = _header(text)
    first = re.sub(r"^Hey HN!\s*", "", first, flags=re.IGNORECASE)
    if m := re.match(
        r"^(.{1,60}?)(?:\s*\([^)]*\))?\s+(?:is\s+(?:hiring|looking for|the|a|an)\b"
        r"|[-—–]\s+(?:we|full[- ]?time|founding|full[- ]stack|software)\b)",
        first,
        re.IGNORECASE,
    ):
        return _company_name(m[1])
    if len(first) <= 50 and not re.search(
        r"[.!?:]|\b(?:we|hello|hiring|join|looking|welcome)\b", first, re.IGNORECASE
    ):
        return _company_name(first)
    return None


def find_location(text, parts):
    candidates = [
        p
        for p in parts
        if not ROLE_HINT.search(p)
        and _looks_like_place(p)
        and not re.search(r"full[- ]?time", p, re.IGNORECASE)
    ]
    # A location may share its slot with the title.
    candidates += [
        m[1]
        for p in parts
        if (m := re.match(r"^(.+?)\s+\((?:in person|onsite|hybrid)\)", p, re.IGNORECASE))
    ]
    candidates += [
        m[1] for m in re.finditer(r"^LOCATION:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
    ]
    for candidate in candidates:
        if location := _clean_location(candidate):
            return location
    # Explicit prose location statements; an HQ mention alone never establishes job location.
    for pattern in [
        (
            r"\b(?i:all positions are|we(?:'re| are) hiring|is hiring|hiring) in "
            r"([A-Z][\w ,]+?)(?:[.!:]| across)(?:\s|$)"
        ),
        r"\bour ([A-Z][a-z]+) office\b",
        r"\b(?:downtown )?(SF)\b",
        r"\b(NY)-based\b",
        r"\b(Remote US)\b",
        r"\b(U\.S\.)-based\b",
        r"\((Latin America) Remote\)",
        r"\bRemote, (LatAm(?:/Europe)?)\b",
    ]:
        if m := re.search(pattern, text):
            return {
                "SF": "San Francisco",
                "NY": "New York",
                "Remote US": "US",
                "U.S.": "US",
                "LatAm": "Latin America",
                "LatAm/Europe": "LatAm, Europe",
            }.get(m[1], m[1])
    return None


def find_remote(text, header):
    def arrangement(value):
        # A partial office week is hybrid, even when the author calls it onsite.
        if re.search(r"\b(?:[1-4](?:-[1-4])?\s*days?|part remote)\b", value, re.IGNORECASE) and (
            re.search(r"onsite|office|in-person", value, re.IGNORECASE)
        ):
            return "hybrid"
        if re.search(r"\bremote\b", value, re.IGNORECASE) and re.search(
            r"\bor\s+(?:remote|hybrid)\b|\+\s*remote\b|remote,\s*onsite", value, re.IGNORECASE
        ):
            return "remote"
        return _first_match(REMOTE, value)

    if found := arrangement(header):
        return found
    for line in text.splitlines():
        if (
            re.search(
                r"\b(?:remote|hybrid|onsite|office|location|roles?|positions?)\b",
                line,
                re.IGNORECASE,
            )
            and not re.search(r"customers|\bHQ\b", line, re.IGNORECASE)
            and (found := arrangement(line))
        ):
            return found
    return None


TITLE_LEVELS = [
    (
        re.compile(
            r"\b(?:staff|principal|distinguished|director|vp|head of|cto|co-founder|leads?)\b",
            re.IGNORECASE,
        ),
        "staff+",
    ),
    (re.compile(r"\b(?:senior|sr\.?)\b(?!\s+staff)", re.IGNORECASE), "senior"),
    (
        re.compile(r"\b(?:junior|jr\.?|entry[- ]level|new grad|graduate|intern)\b", re.IGNORECASE),
        "junior",
    ),
    (re.compile(r"\b(?:mid[- ]level|intermediate)\b", re.IGNORECASE), "mid"),
]


def find_seniority(text, parts):
    titles = [p for p in parts if ROLE_HINT.search(p) and not re.search(r"https?://", p)]
    for line in text.splitlines():
        if line.count("|") >= 2:
            titles.extend(
                p.strip()
                for p in line.split("|")
                if ROLE_HINT.search(p) and not re.search(r"https?://", p)
            )
    header_levels = {v for title in titles for pat, v in TITLE_LEVELS if pat.search(title)}
    for line in text.splitlines():
        if "|" in line:
            continue
        line = re.sub(
            r"^\s*(?:[-*>•]+|\d+[.)])?\s*(?:ROLE:|Open roles:)?\s*", "", line, flags=re.IGNORECASE
        )
        # Title lines, not descriptions of colleagues, responsibilities or experience.
        if (
            len(line) < 220
            and re.match(
                r"(?:senior|sr\.?|staff|principal|junior|intern|head of|lead|"
                r"(?:full[- ]stack|backend|software|distributed systems) engineer)\b",
                line,
                re.IGNORECASE,
            )
            and ROLE_HINT.search(line)
        ):
            title = line.split("https://")[0]
            if not header_levels or any(pat.search(title) for pat, _ in TITLE_LEVELS):
                titles.append(title)
    # An explicit hiring sentence can carry a title in otherwise unstructured prose.
    if not titles and (
        m := re.search(
            r"(?i:hiring (?:for a |a |an )?)((?:Senior|senior|Junior|junior) "
            r"[^,.\n]{0,60}(?:[Dd]eveloper|[Ee]ngineer)[^,.\n]*)",
            text,
        )
    ):
        titles.append(m[1])
    if not titles:
        return None
    levels = set()
    for title in titles:
        title = re.sub(r"\([^)]*\)", "", title)
        for role in re.split(r"\s+[+&]\s+", title):
            matches = {value for pattern, value in TITLE_LEVELS if pattern.search(role)}
            levels.update(matches or {None})
    # One row represents all advertised roles. Mixed grades have no single seniority.
    return next(iter(levels)) if len(levels) == 1 else None


def parse(text):
    """Best-effort structured read of one posting. Returns (Extraction, confidence dict)."""
    seeker = re.search(
        r"\bI(?:'m| am|’m)(?: currently)? looking for (?:a job|work)\b", text, re.IGNORECASE
    )
    seeker = seeker or (
        re.search(r"^R[eé]sum[eé]/CV:", text, re.IGNORECASE | re.MULTILINE)
        and re.search(r"^Willing to relocate:", text, re.IGNORECASE | re.MULTILINE)
    )
    if seeker:
        return Extraction(), dict.fromkeys(
            ["company", "salary", "skills", "remote", "seniority"], False
        )
    # A closure notice can precede a perfectly valid job header.
    text = re.sub(r"^CLOSED[^\n]*\n+", "", text, flags=re.IGNORECASE)
    header = _header(text)
    parts = [p.strip() for p in header.split("|") if p.strip()] if "|" in header else []
    company = find_company(text)
    roles = [p for p in parts if ROLE_HINT.search(p)][:3]
    location = find_location(text, parts)
    lo, hi, cur, period = find_salary(text)
    ex = Extraction(
        company=company,
        role_titles=roles,
        location=location,
        remote=find_remote(text, header),
        salary_min=lo,
        salary_max=hi,
        salary_currency=cur,
        salary_period=period,
        skills=find_skills(text),
        seniority=find_seniority(text, parts),
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
