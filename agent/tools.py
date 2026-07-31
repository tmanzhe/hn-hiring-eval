"""Tools the extraction agent can call.

None of these call a model. They are plain Python, unit-testable without an API key, and the
agent's job is to decide which to call and what to do with the answer. Keeping the tools dumb
is what makes the agent's contribution measurable — if quality improves, it improved because of
planning and verification, not because a tool got smarter.

Wrapped for LangChain in agent/extract_agent.py. Importing this module pulls in no framework.
"""

import re

from ingest.normalize import SKILL_SYNONYMS
from ingest.rules import RANGE, ROLE_HINT, SINGLE, SKILLS, find_salary

# Numbered items, or an explicit "Role:" / "Position:" header.
#
# Bare bullets (`- Foo`) are deliberately NOT here. Measured against the corpus they matched
# responsibility lists and compensation-stage lists far more often than roles — they reported
# 29.5% of posts as multi-role, and spot-checking showed almost all of it was junk like
# "- Own systems end-to-end" and "- Seed (6-12 months): 75% market salary".
ROLE_SPLIT = re.compile(
    r"^\s*(?:\d+[.)]\s+|(?:role|position|opening)\s*\d*\s*[:—-]\s*)",
    re.IGNORECASE | re.MULTILINE,
)


def split_roles(text: str) -> list[str]:
    """Break a post that advertises several roles into one chunk per role.

    Returns a single-element list when the post is one role, so the caller never has to
    special-case it. Two things get dropped: the preamble before the first marker (that's the
    intro, "We're hiring for two positions:", never a role) and chunks under 40 characters.
    """
    markers = list(ROLE_SPLIT.finditer(text))
    if len(markers) < 2:
        return [text.strip()]

    chunks = []
    for i, m in enumerate(markers):
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        chunk = text[m.end() : end].strip()
        # A role chunk has to name a role. Without this, numbered requirement lists
        # ("1. 5+ years experience  2. Strong CS fundamentals") split into fake roles.
        if len(chunk) >= 40 and ROLE_HINT.search(chunk[:200]):
            chunks.append(chunk)

    return chunks if len(chunks) > 1 else [text.strip()]


def find_salary_candidates(text: str, window: int = 45) -> list[dict]:
    """Every salary-shaped string in the post, with the text around it.

    The agent gets the candidates and the context; deciding which one is the salary — as opposed
    to a funding round, a bounty, or a product price — is its job. `parsed` is what the
    deterministic parser would make of the whole post, offered as a starting point rather than
    an answer.
    """
    out, seen = [], set()
    for pattern in (RANGE, SINGLE):
        for m in pattern.finditer(text):
            if m.start() in seen:
                continue
            seen.add(m.start())
            lo = max(0, m.start() - window)
            out.append(
                {
                    "match": m.group(0),
                    "context": text[lo : m.end() + window].replace("\n", " ").strip(),
                }
            )
    lo, hi, cur, period = find_salary(text)
    return [{"candidates": out, "parsed": {"min": lo, "max": hi, "currency": cur,
                                           "period": period}}] if out else []


def verify_claim(value: str, text: str) -> dict:
    """Does this extracted value actually appear in the source post?

    The groundedness check. Returns `grounded: False` with an explanation rather than raising,
    so the agent can decide whether to revise. Digits are compared with separators stripped, so
    "180000" matches "$180,000" and "180k".
    """
    if value is None or str(value).strip() == "":
        return {"grounded": True, "reason": "empty value, nothing to ground"}

    needle = str(value).strip()
    hay = text.lower()

    if needle.lower() in hay:
        return {"grounded": True, "reason": "exact substring match"}

    digits = re.sub(r"\D", "", needle)
    if digits and len(digits) >= 2:
        compact = re.sub(r"[,\s]", "", hay)
        if digits in compact:
            return {"grounded": True, "reason": "numeric match ignoring separators"}
        if digits.endswith("000") and digits[:-3] + "k" in compact:
            return {"grounded": True, "reason": "matched as a k-suffixed figure"}

    return {
        "grounded": False,
        "reason": f"{needle!r} does not appear in the post. Do not report it unless the post "
        f"states it — returning null is correct when the post is silent.",
    }


def canonical_skill(term: str) -> dict:
    """Map a term to its canonical skill name, or say it's unrecognised.

    Stops the agent inventing skill names that no scorer will ever match, and keeps its output
    on the same vocabulary as the rules path. Unknown is reported honestly rather than guessed.
    """
    key = (term or "").strip().lower()
    if not key:
        return {"known": False, "canonical": None, "reason": "empty term"}

    canonical = SKILL_SYNONYMS.get(key, key)
    if canonical in SKILLS or canonical in SKILL_SYNONYMS.values():
        return {"known": True, "canonical": canonical}
    return {
        "known": False,
        "canonical": None,
        "reason": f"{term!r} is not in the known skill vocabulary. Include it only if the post "
        f"clearly names it as a technology.",
    }


TOOLS = [split_roles, find_salary_candidates, verify_claim, canonical_skill]
