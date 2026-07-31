"""Agent tools. No API key, no network — these are plain functions, so CI covers them fully.

That's the point of keeping the tools dumb: the agent's contribution stays measurable, and the
parts that can be tested deterministically are.
"""

from agent.tools import canonical_skill, find_salary_candidates, split_roles, verify_claim


class TestSplitRoles:
    def test_single_role_returns_one_chunk(self):
        text = "Acme | Senior Engineer | Remote | $180k-$220k\n\nWe build things with Python."
        assert len(split_roles(text)) == 1

    def test_numbered_roles_split(self):
        text = (
            "We are hiring for two positions this quarter, both remote:\n"
            "1. Senior Backend Engineer working on our Python services and data platform\n"
            "2. Frontend Engineer working on the React dashboard and design system\n"
        )
        assert len(split_roles(text)) == 2

    def test_short_fragments_are_dropped(self):
        """'We're hiring:' is a header, not a role."""
        text = (
            "We're hiring:\n"
            "1. Staff Platform Engineer to own our Kubernetes and Terraform estate end to end\n"
            "2. Data Engineer to build the ingestion pipelines feeding our analytics warehouse\n"
        )
        chunks = split_roles(text)
        assert all(len(c) >= 40 for c in chunks)

    def test_never_returns_empty(self):
        assert split_roles("") == [""]
        assert len(split_roles("short")) == 1

    def test_numbered_requirements_are_not_roles(self):
        """Without the role-word check, any numbered list becomes fake roles."""
        text = (
            "About the job:\n"
            "1. You will have five or more years of professional experience shipping code\n"
            "2. You will have strong computer science fundamentals and system design skills\n"
        )
        assert len(split_roles(text)) == 1

    def test_known_limitation_interview_stages(self):
        """Measured against the corpus, roughly a third of the 1.8% of posts this flags are
        interview-process lists whose stages mention roles. The agent sees the full post as
        well as the chunks, so an advisory over-split is tolerable — but it is a known
        false positive, not a clean signal, and it is not a reliable multi-role detector.
        """
        text = (
            "1. Hiring manager chat and a short take-home to size up your fundamentals\n"
            "2. Coding challenge with another Engineer from the platform team, 45 minutes\n"
        )
        assert len(split_roles(text)) == 2  # documents current behaviour, not desired behaviour


class TestFindSalaryCandidates:
    def test_returns_candidates_with_context(self):
        out = find_salary_candidates("Compensation is $180k-$230k depending on level.")
        assert out
        cands = out[0]["candidates"]
        assert any("180" in c["match"] for c in cands)
        assert "depending on level" in cands[0]["context"]

    def test_offers_the_deterministic_parse_as_a_starting_point(self):
        out = find_salary_candidates("Salary $180k-$230k")
        assert out[0]["parsed"]["min"] == 180000

    def test_surfaces_ambiguity_rather_than_resolving_it(self):
        """Two figures, one a funding round. The agent decides — the tool just shows both."""
        text = "We raised $140M last year. The role pays $190k."
        cands = find_salary_candidates(text)[0]["candidates"]
        assert len(cands) >= 2

    def test_no_money_no_candidates(self):
        assert find_salary_candidates("A great team and a good mission.") == []


class TestVerifyClaim:
    POST = "Portless | AI Engineer | Remote | $180,000 - $230,000 | Python, Kubernetes"

    def test_exact_substring(self):
        assert verify_claim("Portless", self.POST)["grounded"] is True

    def test_number_matches_across_separators(self):
        assert verify_claim(180000, self.POST)["grounded"] is True

    def test_k_suffixed_figure(self):
        assert verify_claim(180000, "pays $180k")["grounded"] is True

    def test_invented_value_is_caught(self):
        r = verify_claim("Google", self.POST)
        assert r["grounded"] is False
        assert "does not appear" in r["reason"]

    def test_invented_salary_is_caught(self):
        assert verify_claim(999999, self.POST)["grounded"] is False

    def test_empty_is_grounded(self):
        """Abstaining is always defensible — there's nothing to ground."""
        assert verify_claim(None, self.POST)["grounded"] is True
        assert verify_claim("", self.POST)["grounded"] is True

    def test_reason_pushes_toward_abstaining(self):
        """The failure message has to steer the agent to null rather than to a second guess."""
        assert "null is correct" in verify_claim("Google", self.POST)["reason"]


class TestCanonicalSkill:
    def test_synonym_maps(self):
        assert canonical_skill("k8s")["canonical"] == "kubernetes"
        assert canonical_skill("Postgres")["canonical"] == "postgresql"

    def test_known_skill_passes_through(self):
        r = canonical_skill("Python")
        assert r["known"] is True and r["canonical"] == "python"

    def test_unknown_is_reported_not_guessed(self):
        r = canonical_skill("Blorptron")
        assert r["known"] is False and r["canonical"] is None

    def test_empty_term(self):
        assert canonical_skill("")["known"] is False
