"""Step 26. Every concrete claim in a generated summary must trace to a retrieved field.

The two-line match summary is the only free text this system produces, so it's the only place a
judge is even arguably needed. This is the programmatic option, and it's preferred: an LLM judge
would be slower, non-deterministic, and would itself need validating against human labels — and
an unvalidated judge is vibes with extra steps.

The check is deliberately narrow. It verifies three kinds of concrete claim — money figures,
counts, and skill names — against the retrieved rows. Fails closed: an unverifiable claim is a
failure, not a pass.

**What it does not cover, stated plainly rather than implied:**

  * Tone, helpfulness, or whether the summary is any good. A regex cannot know those.
  * Fabricated company names. Detecting "a capitalised word that isn't in the rows" fires on
    sentence starts, skill names and ordinary nouns; the false-positive rate makes it worse
    than nothing. A summary template that never interpolates a company name is the real fix,
    and that belongs in the prompt, not here.
  * Claims that are true of the corpus but not of the retrieved rows. The check's scope is the
    rows it was handed.

Coverage of a checker is a number worth reporting, same as coverage of an extractor.
"""

import re
from dataclasses import dataclass, field

from ingest.normalize import normalize_skills
from ingest.rules import SKILLS

# Numbers worth checking. Bare small integers ("2 roles", "top 3") are counted separately
# because they're usually claims about the result set rather than about a posting.
MONEY = re.compile(r"[$£€]\s?\d[\d,]*(?:\.\d+)?\s*[kKmM]?")
BARE_NUMBER = re.compile(r"(?<![$£€\w.])\d{1,3}(?:,\d{3})*(?![\d%])")

# Hedging language. A summary that says "roughly 12" is making a weaker claim than "12", and the
# checker should hold it to a weaker standard.
HEDGE = re.compile(r"\b(?:about|around|roughly|approximately|~|nearly|over|under|at least)\b", re.IGNORECASE)


@dataclass
class Claim:
    kind: str          # money | number | skill | company
    text: str
    grounded: bool
    reason: str = ""


@dataclass
class GroundednessReport:
    claims: list[Claim] = field(default_factory=list)

    @property
    def grounded(self) -> bool:
        """Fails closed — one ungrounded claim fails the summary."""
        return all(c.grounded for c in self.claims)

    @property
    def ungrounded(self) -> list[Claim]:
        return [c for c in self.claims if not c.grounded]

    def to_dict(self) -> dict:
        return {
            "grounded": self.grounded,
            "n_claims": len(self.claims),
            "n_ungrounded": len(self.ungrounded),
            "ungrounded": [{"kind": c.kind, "text": c.text, "reason": c.reason}
                           for c in self.ungrounded],
        }


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def _money_values(rows: list[dict]) -> set[str]:
    """Every salary figure the retrieved rows actually contain, as digit strings, plus the
    k-abbreviated form so '$180k' matches a stored 180000."""
    out: set[str] = set()
    for r in rows:
        for key in ("salary_min", "salary_max"):
            v = r.get(key)
            if v is None:
                continue
            out.add(str(int(v)))
            if int(v) % 1000 == 0:
                out.add(str(int(v) // 1000))
    return out


def check(summary: str, rows: list[dict], *, allowed_counts: set[int] | None = None) -> GroundednessReport:
    """Verify a summary against the rows it was generated from.

    `allowed_counts` are legitimate claims about the result set itself — "3 roles matched" is
    true if 3 rows came back, even though no posting contains the number 3.
    """
    report = GroundednessReport()
    allowed_counts = allowed_counts or {len(rows)}
    money = _money_values(rows)
    skills = {s for r in rows for s in normalize_skills(r.get("skills") or [])}
    hedged = bool(HEDGE.search(summary))

    # Money spans are consumed first so the bare-number pass can't re-scan the tail of a figure
    # it already checked. Without this, "$180,000" is verified as money and then its "000" is
    # flagged as an unsupported count — a false positive that would block a correct summary.
    consumed: list[tuple[int, int]] = []

    for m in MONEY.finditer(summary):
        raw = m.group()
        consumed.append(m.span())
        digits = _digits(raw)
        ok = digits in money or (raw.lower().rstrip().endswith(("k", "m")) and digits in money)
        report.claims.append(
            Claim("money", raw, ok, "" if ok else "no retrieved posting has this figure")
        )

    for m in BARE_NUMBER.finditer(summary):
        if any(start <= m.start() < end for start, end in consumed):
            continue
        raw = m.group()
        try:
            value = int(raw.replace(",", ""))
        except ValueError:
            continue
        ok = value in allowed_counts or raw in money
        if not ok and hedged and any(abs(value - c) <= 1 for c in allowed_counts):
            ok = True  # "about 3" against an actual 4 is a hedge, not a fabrication
        report.claims.append(
            Claim("number", raw, ok, "" if ok else "not a result count or a retrieved figure")
        )

    for skill in SKILLS:
        if re.search(rf"(?<![\w.+#]){re.escape(skill)}(?![\w+#])", summary, re.IGNORECASE):
            canonical = normalize_skills([skill])[0]
            ok = canonical in skills
            report.claims.append(
                Claim("skill", skill, ok, "" if ok else "not required by any retrieved posting")
            )

    return report


def assert_grounded(summary: str, rows: list[dict], **kw) -> GroundednessReport:
    """Fail-closed wrapper for the request path. Raises rather than returning a summary that
    contains an unsupported claim — a wrong number in a user-facing sentence is worse than no
    sentence."""
    report = check(summary, rows, **kw)
    if not report.grounded:
        details = ", ".join(f"{c.kind}:{c.text}" for c in report.ungrounded)
        raise ValueError(f"summary contains ungrounded claims: {details}")
    return report
