"""Regression cases for deterministic extraction, independent of the labeled corpus."""

import pytest

from ingest.normalize import normalize_skills
from ingest.rules import find_salary, find_skills, parse
from ingest.schema import Extraction


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Salary: 65 - 95k EUR", (65000, 95000, "EUR", "year")),
        ("Salary: $165000-$195000", (165000, 195000, "USD", "year")),
        (
            "Base: 65-95k EUR; second role $120k-$160k",
            (65000, 95000, "EUR", "year"),
        ),
        ("€15k signing bonus", (None, None, None, None)),
        ("Signing bonus: $15k-$20k", (None, None, None, None)),
        ("Salary: 165k-195k", (None, None, None, None)),
    ],
)
def test_salary_formats_and_base_pay_only(text, expected):
    assert find_salary(text) == expected


@pytest.mark.parametrize(
    "header,company",
    [
        ("Acme (YC W24) | Engineer | Remote", "Acme"),
        ("Acme (https://acme.example) | Engineer | Remote", "Acme"),
        ("Cologne, Germany | Acme | Engineer | Full-time", "Acme"),
        ("GTM Engineer | Acme", "Acme"),
        ("Acme is hiring software engineers.", "Acme"),
        ("COMPANY: Acme\nROLE: Engineer", "Acme"),
        ("Join Acme\nLabs in Toronto.", None),
    ],
)
def test_company_structure(header, company):
    assert parse(header)[0].company == company


def test_closed_notice_and_repeated_headers():
    post = (
        "CLOSED - thank you!\n\n"
        "Acme | Head of Engineering | Remote\n\n"
        "Acme | Senior DevOps Engineer | Remote"
    )
    ex, _ = parse(post)
    assert ex.company == "Acme"
    assert ex.seniority is None


@pytest.mark.parametrize(
    "slot,location,remote",
    [
        ("NYC (Hybrid) + Remote", "NYC", "remote"),
        ("ONSITE (3 days/week in office)", None, "hybrid"),
        ("Remote (US, Pacific hours)", "US", "remote"),
        ("Fully Remote (HQ in Berlin)", None, "remote"),
        ("Remote, US overlap preferred", None, "remote"),
        ("Remote (US time zone)", "US", "remote"),
    ],
)
def test_work_policy_and_hiring_location(slot, location, remote):
    ex, _ = parse(f"Acme | Engineer | {slot}")
    assert (ex.location, ex.remote) == (location, remote)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Stack: NextJS, Node, TS, sklearn", ["next.js", "node.js", "scikit-learn", "typescript"]),
        ("React Native, Claude Code, Docker Swarm", ["claude code", "docker swarm", "react native"]),
        ("Ruby on Rails", ["ruby on rails"]),
        ("Ruby and Rails", ["ruby", "ruby on rails"]),
        ("We go to market. https://go.acme.example careers@rust.example", []),
        ("Languages: Go, R, C/C++", ["c", "c++", "go", "r"]),
        ("Bare-metal R&D and LLM/RAG concepts", []),
        ("Founders have experience at companies such as Snowflake and Oracle.", []),
        ("Integrations with OpenAI, Twilio", ["openai", "twilio"]),
    ],
)
def test_named_technologies_and_context(text, expected):
    assert normalize_skills(find_skills(text)) == expected


@pytest.mark.parametrize(
    "title,body,expected",
    [
        ("Founding Engineer", "You'll architect systems and lead our team.", None),
        ("Senior Systems Architect", "Work with our CTO.", "senior"),
        ("Lead Software Engineer", "", "staff+"),
        ("Intern", "Mentored by a senior engineer.", "junior"),
        ("Engineer + Senior Engineer", "", None),
        ("Senior Engineer & Senior Data Scientist", "", "senior"),
        ("Senior/Staff Engineer", "", None),
    ],
)
def test_seniority_from_titles(title, body, expected):
    assert parse(f"Acme | {title} | Remote\n\n{body}")[0].seniority == expected


@pytest.mark.parametrize(
    "text",
    [
        "I'm currently looking for a job. Senior React developer. Remote. $150k.",
        "Remote: Yes\nWilling to relocate: No\nRésumé/CV: example.com\nPython architect",
    ],
)
def test_job_seekers_are_not_employer_postings(text):
    ex, confidence = parse(text)
    assert ex == Extraction()
    assert not any(confidence.values())
