"""Step 14 and 21. Per-field scorers and confidence intervals.

The measurement instrument. Everything the project claims comes out of this file, so it is
deliberately boring, dependency-free, and tested harder than anything else in the repo.

Three rules it enforces:

1. **One scorer per field.** A single accuracy number over heterogeneous fields is meaningless —
   `company` is a string match, `skills` is set overlap, `remote` is a confusion matrix. They
   fail in different ways and averaging hides all of it.

2. **Four outcomes for nullable fields**, never two. Abstaining correctly is a win; hallucinating
   is the only unrecoverable failure. Coverage and precision-on-attempts are reported separately
   because a model that abstains on 60% and is never wrong beats one that always answers and is
   wrong a third of the time — and a blended score ranks those the wrong way round.

3. **Normalize both sides identically.** The synonym table is imported from `ingest.normalize`,
   the same one the pipeline uses. Applied one-sided, skills F1 measures the synonym dictionary
   rather than the extractor, and it drifts every time an entry is added.
"""

import math
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum

from ingest.normalize import normalize_skills

Z_95 = 1.959963984540054


class Outcome(str, Enum):
    """The four things that can happen to a field that is allowed to be absent."""

    EXTRACTED = "extracted"      # present in post, value correct
    ABSTAINED = "abstained"      # absent from post, null returned — a win
    MISSED = "missed"            # present in post, null returned — costs coverage
    HALLUCINATED = "hallucinated"  # absent from post, value invented — unrecoverable
    WRONG = "wrong"              # present in post, wrong value returned


def wilson(successes: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """Wilson score interval for a proportion.

    Used instead of the normal approximation because at n=40 with p near 0 or 1 the normal
    interval runs outside [0,1] and understates uncertainty — exactly the regime this project
    operates in. Returns (0.0, 1.0) for n=0: no data means no information, not certainty.
    """
    if n <= 0:
        return 0.0, 1.0
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z / denom * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, center - half), min(1.0, center + half)


def margin(successes: int, n: int) -> float:
    """Half-width of the 95% interval, in points. The number that decides whether a difference
    between two configs is a result or noise."""
    lo, hi = wilson(successes, n)
    return (hi - lo) / 2


@dataclass
class NullableReport:
    """Scores for one nullable field. Coverage and precision stay separate on purpose."""

    field_name: str
    counts: Counter = field(default_factory=Counter)

    @property
    def n(self) -> int:
        return sum(self.counts.values())

    @property
    def attempts(self) -> int:
        """Times the extractor produced a value at all."""
        return (
            self.counts[Outcome.EXTRACTED]
            + self.counts[Outcome.WRONG]
            + self.counts[Outcome.HALLUCINATED]
        )

    @property
    def coverage(self) -> float:
        return self.attempts / self.n if self.n else 0.0

    @property
    def precision(self) -> float:
        """Of the times it answered, how often was it right."""
        return self.counts[Outcome.EXTRACTED] / self.attempts if self.attempts else 0.0

    @property
    def hallucination_rate(self) -> float:
        """Never folded into an average. A miss costs a row; an invented value is
        indistinguishable from a real one forever."""
        return self.counts[Outcome.HALLUCINATED] / self.n if self.n else 0.0

    @property
    def precision_ci(self) -> tuple[float, float]:
        return wilson(self.counts[Outcome.EXTRACTED], self.attempts)

    def to_dict(self) -> dict:
        lo, hi = self.precision_ci
        return {
            "n": self.n,
            "coverage": round(self.coverage, 4),
            "precision": round(self.precision, 4),
            "precision_ci95": [round(lo, 4), round(hi, 4)],
            "precision_margin": round(margin(self.counts[Outcome.EXTRACTED], self.attempts), 4),
            "hallucination_rate": round(self.hallucination_rate, 4),
            "outcomes": {k.value: v for k, v in sorted(self.counts.items())},
        }


def score_nullable(predicted, truth, *, compare=None) -> Outcome:
    """Classify one nullable field into one of the four outcomes.

    `compare` lets a field define its own notion of 'same' — fuzzy match for location, exact for
    salary. Defaults to equality.
    """
    same = compare or (lambda a, b: a == b)
    p_missing = predicted is None or predicted == ""
    t_missing = truth is None or truth == ""

    if t_missing and p_missing:
        return Outcome.ABSTAINED
    if t_missing and not p_missing:
        return Outcome.HALLUCINATED
    if not t_missing and p_missing:
        return Outcome.MISSED
    return Outcome.EXTRACTED if same(predicted, truth) else Outcome.WRONG


def score_nullable_field(name: str, pairs, *, compare=None) -> NullableReport:
    """pairs is an iterable of (predicted, truth)."""
    report = NullableReport(field_name=name)
    for predicted, truth in pairs:
        report.counts[score_nullable(predicted, truth, compare=compare)] += 1
    return report


@dataclass
class SetReport:
    """Skills. Macro-F1 — averaged per post, not pooled — so one post listing twenty skills
    can't dominate the score."""

    field_name: str
    per_post: list = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.per_post)

    @property
    def macro_f1(self) -> float:
        return sum(f for _, _, f in self.per_post) / self.n if self.n else 0.0

    @property
    def macro_precision(self) -> float:
        return sum(p for p, _, _ in self.per_post) / self.n if self.n else 0.0

    @property
    def macro_recall(self) -> float:
        return sum(r for _, r, _ in self.per_post) / self.n if self.n else 0.0

    def to_dict(self) -> dict:
        return {
            "n": self.n,
            "macro_f1": round(self.macro_f1, 4),
            "macro_precision": round(self.macro_precision, 4),
            "macro_recall": round(self.macro_recall, 4),
        }


def score_set_pair(predicted, truth) -> tuple[float, float, float]:
    """P/R/F1 for one post. Both sides normalised through the same table."""
    p_set = set(normalize_skills(predicted))
    t_set = set(normalize_skills(truth))

    if not p_set and not t_set:
        return 1.0, 1.0, 1.0  # both say "no skills" — agreement, not a failure
    if not p_set or not t_set:
        return 0.0, 0.0, 0.0

    tp = len(p_set & t_set)
    precision = tp / len(p_set)
    recall = tp / len(t_set)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def score_set_field(name: str, pairs) -> SetReport:
    report = SetReport(field_name=name)
    for predicted, truth in pairs:
        report.per_post.append(score_set_pair(predicted, truth))
    return report


@dataclass
class EnumReport:
    """Enums get a confusion matrix and per-class recall. An overall accuracy would hide a model
    that never predicts 'hybrid'."""

    field_name: str
    matrix: Counter = field(default_factory=Counter)

    @property
    def n(self) -> int:
        return sum(self.matrix.values())

    @property
    def accuracy(self) -> float:
        correct = sum(v for (t, p), v in self.matrix.items() if t == p)
        return correct / self.n if self.n else 0.0

    def per_class_recall(self) -> dict:
        out = {}
        classes = {t for t, _ in self.matrix}
        for cls in classes:
            total = sum(v for (t, _), v in self.matrix.items() if t == cls)
            hit = self.matrix[(cls, cls)]
            out[str(cls)] = round(hit / total, 4) if total else 0.0
        return out

    def to_dict(self) -> dict:
        return {
            "n": self.n,
            "accuracy": round(self.accuracy, 4),
            "per_class_recall": self.per_class_recall(),
            "confusion": {f"{t}->{p}": v for (t, p), v in sorted(self.matrix.items(), key=str)},
        }


def score_enum_field(name: str, pairs) -> EnumReport:
    report = EnumReport(field_name=name)
    for predicted, truth in pairs:
        report.matrix[(truth, predicted)] += 1
    return report


def salary_matches(predicted, truth) -> bool:
    """Salary is a (min, max) tuple. Both bounds must agree — reporting the right floor and a
    wrong ceiling is a wrong answer, not a half-right one."""
    return tuple(predicted) == tuple(truth)


def fuzzy_ratio(a: str, b: str) -> float:
    """Character-bigram Dice coefficient. Used for `location`, where 'San Francisco, CA' and
    'San Francisco' are the same answer and exact match would be too harsh."""
    a, b = (a or "").lower().strip(), (b or "").lower().strip()
    if a == b:
        return 1.0
    if len(a) < 2 or len(b) < 2:
        return 0.0
    pa = Counter(a[i : i + 2] for i in range(len(a) - 1))
    pb = Counter(b[i : i + 2] for i in range(len(b) - 1))
    overlap = sum((pa & pb).values())
    return 2 * overlap / (sum(pa.values()) + sum(pb.values()))


def location_matches(predicted, truth, threshold: float = 0.9) -> bool:
    return fuzzy_ratio(str(predicted), str(truth)) >= threshold
