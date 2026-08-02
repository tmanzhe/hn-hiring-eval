"""Step 25. Resume → ranked jobs. No model involved.

Naive `overlap / required` ranks a two-skill posting above a genuine fit, and since almost every
post lists Python, common skills dominate the score. Two corrections:

  * **IDF weighting.** A skill's worth is inverse to how many postings mention it. Matching on
    Terraform says more than matching on Python.
  * **A minimum overlap.** A posting has to clear a floor of matched skills before it's eligible
    to rank at all, so a one-skill post can't win on a technicality.

Counting, weighting and ranking are arithmetic. The model's only job in this feature is reading
the resume text and writing the closing summary — ask it to rank and it will produce a plausible
order it cannot justify.
"""

import math
import re
from dataclasses import dataclass

from ingest.normalize import display_skills, normalize_skills
from ingest.rules import SKILLS

MIN_MATCHED_SKILLS = 2

# Longest first, so "next.js" is found before "next" and "postgresql" before "postgres".
_SKILL_PATTERNS = sorted(SKILLS, key=len, reverse=True)


def skills_in(text: str) -> list[str]:
    """Pull known skills out of free text. Same vocabulary as the extractor, so a resume and a
    posting are always compared on the same terms."""
    low = (text or "").lower()
    found = {s for s in _SKILL_PATTERNS if re.search(rf"(?<![\w.+#]){re.escape(s)}(?![\w+#])", low)}
    return normalize_skills(found)


def idf(postings: list[dict]) -> dict[str, float]:
    """Inverse document frequency per skill across the corpus.

    Smoothed so a skill appearing in every posting scores just above zero rather than exactly
    zero — otherwise a universal skill would silently drop out of every comparison.
    """
    n = len(postings)
    if not n:
        return {}
    counts: dict[str, int] = {}
    for p in postings:
        for s in normalize_skills(p.get("skills") or []):
            counts[s] = counts.get(s, 0) + 1
    return {s: math.log((n + 1) / (c + 1)) + 1.0 for s, c in counts.items()}


@dataclass
class Match:
    comment_id: int
    company: str | None
    score: float
    matched: list[str]
    missing: list[str]
    salary_min: int | None = None
    salary_max: int | None = None

    def to_dict(self) -> dict:
        # Matching happens on canonical lowercase so "k8s" and "Kubernetes" compare equal.
        # Display uses the same casing /api/jobs returns, so a skill isn't spelled two
        # different ways depending on which endpoint you asked.
        return {
            "comment_id": self.comment_id,
            "company": self.company,
            "score": round(self.score, 4),
            "matched_skills": display_skills(self.matched),
            "gap_skills": display_skills(self.missing),
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
        }


def rank(resume_text: str, postings: list[dict], limit: int = 10) -> list[Match]:
    """Rank postings against a resume. Deterministic — same inputs, same order, every time."""
    mine = set(skills_in(resume_text))
    if not mine:
        return []

    weights = idf(postings)
    out: list[Match] = []

    for p in postings:
        wanted = set(normalize_skills(p.get("skills") or []))
        if not wanted:
            continue
        matched = mine & wanted
        if len(matched) < MIN_MATCHED_SKILLS:
            continue

        earned = sum(weights.get(s, 1.0) for s in matched)
        total = sum(weights.get(s, 1.0) for s in wanted)
        if total <= 0:
            continue

        out.append(
            Match(
                comment_id=p["comment_id"],
                company=p.get("company"),
                score=earned / total,
                matched=sorted(matched),
                missing=sorted(wanted - mine),
                salary_min=p.get("salary_min"),
                salary_max=p.get("salary_max"),
            )
        )

    # Ties broken by comment_id so the order is reproducible, which matters for the matcher eval.
    out.sort(key=lambda m: (-m.score, m.comment_id))
    return out[:limit]


def precision_at_k(ranked: list[Match], relevant_ids: set[int], k: int = 10) -> float:
    """Scoring for the matcher's own eval — a handful of resumes with hand-ranked expected
    matches. Same discipline as the extractor, second component."""
    if not ranked:
        return 0.0
    top = ranked[:k]
    hits = sum(1 for m in top if m.comment_id in relevant_ids)
    return hits / len(top)
