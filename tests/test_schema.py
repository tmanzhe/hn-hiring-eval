"""Schema tests. These guard three things that are easy to break by accident and expensive
to notice later.
"""

import pytest
from pydantic import ValidationError

from ingest.schema import Extraction, Posting

NULLABLE = [
    "company", "location", "remote", "salary_min", "salary_max",
    "salary_currency", "salary_period", "seniority", "visa_sponsor",
]


class TestAbstaining:
    def test_every_field_can_be_absent(self):
        """A post that states nothing must be representable. If the schema can't express
        'not stated', the model has to invent something, and abstaining correctly stops being
        a scoreable outcome."""
        e = Extraction()
        assert all(getattr(e, f) is None for f in NULLABLE)
        assert e.skills == [] and e.role_titles == []

    @pytest.mark.parametrize("field", NULLABLE)
    def test_field_accepts_none_explicitly(self, field):
        assert getattr(Extraction(**{field: None}), field) is None


class TestStructuredOutputCompatibility:
    """This model doubles as the JSON schema for the extraction API call, so it has to stay
    inside what structured outputs accepts."""

    def test_additional_properties_false(self):
        assert Extraction.model_json_schema()["additionalProperties"] is False

    def test_rejects_unknown_fields(self):
        with pytest.raises(ValidationError):
            Extraction(compnay="typo")

    def test_no_numeric_or_length_constraints(self):
        """minimum/maximum/minLength/maxLength are rejected by structured outputs. Adding a
        Field(ge=...) would break the API call, not the model."""
        banned = {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
                  "multipleOf", "minLength", "maxLength", "minItems", "maxItems"}
        schema = Extraction.model_json_schema()

        def walk(node):
            if isinstance(node, dict):
                assert not (banned & node.keys()), f"unsupported constraint in {node}"
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(schema)


class TestPipelineOwnedFields:
    """The model is never asked for provenance. It can't know either field, and asking invites
    it to make something up."""

    def test_extraction_has_no_provenance_fields(self):
        props = Extraction.model_json_schema()["properties"]
        assert "extracted_by" not in props
        assert "thread_date" not in props
        assert "comment_id" not in props

    def test_posting_requires_them(self):
        with pytest.raises(ValidationError):
            Posting(company="Acme")

    def test_posting_round_trips(self):
        p = Posting(
            comment_id=48915735, thread_date="2026-07-01", extracted_by="llm",
            company="Portless", salary_min=180000, salary_max=230000,
            salary_currency="USD", salary_period="year", skills=["Python"],
        )
        assert p.extracted_by == "llm"
        assert p.model_dump()["salary_period"] == "year"

    def test_extracted_by_is_constrained(self):
        with pytest.raises(ValidationError):
            Posting(comment_id=1, thread_date="2026-07-01", extracted_by="vibes")
