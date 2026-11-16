from types import SimpleNamespace

import pytest

from app.models.narrative_review_schema import (
    NarrativeReviewResult,
    NarrativeSectionReview,
)
from app.services import narrative_review_service


DRAFT = {
    "headline": "North leads regional revenue",
    "observation": "North has the highest revenue of 110.25.",
    "business_implication": (
        "The regional differences warrant further investigation."
    ),
    "limitations": [
        "Profitability data is unavailable."
    ],
}


EVIDENCE = {
    "E1": {
        "type": "verified_calculation_trace",
        "data": {
            "operation": "groupby_sum",
        },
    },
    "E2": {
        "type": "verified_supporting_table",
        "rows": [
            {
                "region": "North",
                "revenue": 110.25,
            },
            {
                "region": "West",
                "revenue": 68.99,
            },
        ],
    },
}


CLAIM_VERIFICATION = {
    "status": "passed",
    "verified_facts": [
        {
            "status": "supported",
            "statement": (
                "North has the highest total revenue: 110.25."
            ),
            "evidence_id": "E2",
        }
    ],
}


def make_sections(
    implication_verdict="supported",
    observation_verdict="supported",
):
    sections = []

    for name in [
        "headline",
        "observation",
        "business_implication",
    ]:

        if name == "business_implication":
            verdict = implication_verdict

        elif name == "observation":
            verdict = observation_verdict

        else:
            verdict = "supported"

        sections.append(
            NarrativeSectionReview(
                section=name,
                verdict=verdict,
                reason="Reviewed against supplied evidence.",
                evidence_ids=["E2"],
                suggested_rewrite=(
                    ""
                    if verdict == "supported"
                    else "Further investigation is needed."
                ),
            )
        )

    return sections


def mock_reviewer(monkeypatch, sections):
    monkeypatch.setenv(
        "OPENAI_API_KEY",
        "test-key",
    )

    class FakeClient:
        def __init__(self, **kwargs):
            self.responses = self

        def parse(self, **kwargs):
            return SimpleNamespace(
                output_parsed=NarrativeReviewResult(
                    sections=sections
                )
            )

    monkeypatch.setattr(
        narrative_review_service,
        "OpenAI",
        FakeClient,
    )


def run_review():
    return narrative_review_service.review_insight_narrative(
        draft=DRAFT,
        evidence=EVIDENCE,
        claim_verification=CLAIM_VERIFICATION,
    )


def test_supported_narrative_passes(monkeypatch):
    mock_reviewer(
        monkeypatch,
        make_sections(),
    )

    result = run_review()

    assert result["status"] == "supported"
    assert len(result["sections"]) == 3
    assert result["publication_ready"] is False


def test_hypothesis_is_qualified(monkeypatch):
    mock_reviewer(
        monkeypatch,
        make_sections(
            implication_verdict="hypothesis"
        ),
    )

    result = run_review()

    assert result["status"] == "qualified"


def test_unsupported_statement_is_flagged(monkeypatch):
    mock_reviewer(
        monkeypatch,
        make_sections(
            observation_verdict="unsupported"
        ),
    )

    result = run_review()

    assert result["status"] == "flagged"


@pytest.mark.parametrize(
    "section_name",
    ["headline", "observation", "business_implication"],
)
def test_undocumented_currency_overrides_supported_review(monkeypatch, section_name):
    mock_reviewer(monkeypatch, make_sections())
    draft = {**DRAFT, section_name: "North has revenue of $110.25."}

    result = narrative_review_service.review_insight_narrative(
        draft=draft,
        evidence=EVIDENCE,
        claim_verification=CLAIM_VERIFICATION,
    )

    assert result["status"] == "flagged"
    section = next(
        item for item in result["sections"]
        if item["section"] == section_name
    )
    assert section["verdict"] == "unsupported"
    assert "does not establish any currency unit" in section["reason"]
    assert section["evidence_ids"] == []
    assert "without assuming a currency" in section["suggested_rewrite"]


def test_documented_currency_preserves_supported_review(monkeypatch):
    mock_reviewer(monkeypatch, make_sections())
    evidence = {
        **EVIDENCE,
        "E1": {
            **EVIDENCE["E1"],
            "data": {**EVIDENCE["E1"]["data"], "currency": "CAD"},
        },
    }

    result = narrative_review_service.review_insight_narrative(
        draft={**DRAFT, "observation": "North has revenue of 110.25 CAD."},
        evidence=evidence,
        claim_verification=CLAIM_VERIFICATION,
    )

    assert result["status"] == "supported"


def test_failed_structured_claim_blocks_review():
    result = narrative_review_service.review_insight_narrative(
        draft=DRAFT,
        evidence=EVIDENCE,
        claim_verification={
            "status": "failed",
            "verified_facts": [],
        },
    )

    assert result["status"] == "blocked"
    assert result["method"] == "not_run"


@pytest.mark.parametrize(
    "sections",
    [
        make_sections()[:2],
        [
            make_sections()[0],
            make_sections()[0],
            make_sections()[2],
        ],
    ],
)
def test_missing_or_duplicate_sections_rejected(
    monkeypatch,
    sections,
):
    mock_reviewer(monkeypatch, sections)

    with pytest.raises(
        narrative_review_service.NarrativeReviewError
    ):
        run_review()


def test_unknown_evidence_is_rejected(monkeypatch):
    sections = make_sections()

    sections[0].evidence_ids = ["E999"]

    mock_reviewer(monkeypatch, sections)

    with pytest.raises(
        narrative_review_service.NarrativeReviewError
    ):
        run_review()


def test_reviewed_insight_gets_new_status(monkeypatch):
    monkeypatch.setattr(
        narrative_review_service,
        "generate_insight_draft",
        lambda **kwargs: {
            "dataset_id": "test-id",
            "question": "Which region leads?",
            "insight_draft": DRAFT,
            "evidence": EVIDENCE,
            "claim_verification": CLAIM_VERIFICATION,
            "insight_status": "pending_claim_verification",
        },
    )

    monkeypatch.setattr(
        narrative_review_service,
        "review_insight_narrative",
        lambda **kwargs: {
            "status": "qualified",
            "sections": [],
        },
    )

    result = narrative_review_service.generate_reviewed_insight(
        dataset_id="test-id",
        question="Which region leads?",
    )

    assert result["insight_status"] == (
        "reviewed_not_published"
    )

    assert result["narrative_review"]["status"] == (
        "qualified"
    )
def test_unsupported_currency_is_flagged(monkeypatch):
    sections = make_sections()

    mock_reviewer(monkeypatch, sections)

    draft = {
        **DRAFT,
        "observation": (
            "North generated $110.25 in revenue."
        ),
    }

    result = narrative_review_service.review_insight_narrative(
        draft=draft,
        evidence=EVIDENCE,
        claim_verification=CLAIM_VERIFICATION,
    )

    assert result["status"] == "flagged"

    observation = next(
        section
        for section in result["sections"]
        if section["section"] == "observation"
    )

    assert observation["verdict"] == "unsupported"