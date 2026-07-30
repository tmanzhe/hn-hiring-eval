"""P3. Crudest thing that could work. Two fields, regex and a word list.

No schema, no classes, no LLM. Prints what it finds so I can see where it falls over.

    python3 ingest/rules_poc.py -n 30
    python3 ingest/rules_poc.py --ids 48919859,48915735

Whatever this misses is the argument for putting a model behind it. Whatever it gets right is
work I refuse to pay a model to redo.
"""

import argparse
import html
import json
import re
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

# 20 words, off the top of my head. not a real taxonomy, that comes at step 08.
SKILLS = [
    "python", "typescript", "javascript", "go", "rust", "java", "ruby", "react",
    "next.js", "django", "postgres", "postgresql", "mysql", "redis", "kafka",
    "kubernetes", "k8s", "docker", "terraform", "aws",
]

DASH = r"[-–—]|\s+to\s+"
AMT = r"\$?\s?(\d{2,3}(?:[.,]\d{3})?)\s?[kK]?"
SALARY = re.compile(
    rf"(?P<cur>\$|USD|EUR|GBP|€|£)\s?(?P<lo>\d{{1,3}}(?:[.,]\d{{3}})?)\s?(?P<lok>[kK])?"
    rf"\s*(?:{DASH})\s*"
    rf"(?:\$|USD|EUR|GBP|€|£)?\s?(?P<hi>\d{{1,3}}(?:[.,]\d{{3}})?)\s?(?P<hik>[kK])?"
)


def to_text(s):
    s = re.sub(r"<p>", "\n", s or "")
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s)


def to_dollars(n, k):
    n = float(n.replace(",", "").replace(".", "")) if "," in n or "." in n else float(n)
    v = n * 1000 if k else n
    return int(v)


def find_salary(text):
    m = SALARY.search(text)
    if not m:
        return None, None, None
    cur = {"$": "USD", "€": "EUR", "£": "GBP"}.get(m["cur"], m["cur"])
    return to_dollars(m["lo"], m["lok"]), to_dollars(m["hi"], m["hik"]), cur


def find_skills(text):
    low = text.lower()
    return sorted({s for s in SKILLS if re.search(rf"(?<![\w.]){re.escape(s)}(?![\w])", low)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=30)
    ap.add_argument("--ids")
    args = ap.parse_args()

    path = max(RAW.glob("*.json"), key=lambda p: p.stat().st_mtime)
    posts = json.loads(path.read_text())["comments"]
    if args.ids:
        want = set(args.ids.split(","))
        posts = [c for c in posts if c["objectID"] in want]
    else:
        posts = posts[: args.n]

    found = 0
    for c in posts:
        text = to_text(c.get("comment_text"))
        lo, hi, cur = find_salary(text)
        skills = find_skills(text)
        found += lo is not None
        sal = f"{cur} {lo}-{hi}" if lo else "-"
        print(f"{c['objectID']}  {sal:<22}  {', '.join(skills) or '-'}")

    print(f"\n{found}/{len(posts)} posts got a salary out of the regex")
    print("that's coverage, not accuracy. no idea yet how many are right. that's P4 and P5.")


if __name__ == "__main__":
    main()
