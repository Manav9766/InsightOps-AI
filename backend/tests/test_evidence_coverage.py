from copy import deepcopy

from app.services.evidence_coverage_service import (
    build_evidence_coverage,
)

from app.services import narrative_review_service


BASE_RESULT = {
    "calculation_evaluation": {
        "status": "passed",
    },
    "insight_draft": {
        "factual_claims": [
            {
                "kind": "group_extreme",
            }
        ],
    },
    "claim_verification": {
        "status": "passed",
        "verified_facts": [
            {
                "claim_index": 0,
                "status": "supported",
            }
        ],
        "rejected_claims": [],
    },
    "narrative_review": {
        "status": "qualified",
        "sections": [
            {
                "section": "headline",
                "verdict": "supported",
            },
            {
                "section": "observation",
                "verdict": "supported",
            },
            {
                "section": "business_implication",
                "verdict": "hypothesis",
            },
        ],
    },
    "evidence": {
        "E1": {
            "type": "verified_calculation_trace",
        },
        "E2": {
            "type": "verified_supporting_table",
            "rows_in_result": 4,
            "rows_included": 4,
        },
    },
}


def test_hypothesis_produces_qualified_coverage():
    result = build_evidence_coverage(
        deepcopy(BASE_RESULT)
    )

    assert result["status"] == "qualified"
    assert result["structured_claims"]["supported"] == 1
    assert result["narrative_sections"]["reviewed"] == 3
    assert result["narrative_sections"]["supported"] == 2
    assert result["narrative_sections"]["hypothesis"] == 1


def test_fully_supported_review_has_direct_support():
    data = deepcopy(BASE_RESULT)

    data["narrative_review"]["status"] = "supported"

    data["narrative_review"]["sections"][2][
        "verdict"
    ] = "supported"

    result = build_evidence_coverage(data)

    assert result["status"] == "direct_support"
    assert result["narrative_sections"]["supported"] == 3
    assert result["gaps"] == []


def test_truncated_evidence_is_qualified():
    data = deepcopy(BASE_RESULT)

    data["narrative_review"]["status"] = "supported"

    data["narrative_review"]["sections"][2][
        "verdict"
    ] = "supported"

    data["evidence"]["E2"]["rows_in_result"] = 20
    data["evidence"]["E2"]["rows_included"] = 12

    result = build_evidence_coverage(data)

    assert result["status"] == "qualified"
    assert result["supporting_table"]["truncated"] is True
    assert result["supporting_table"]["included_rows"] == 12


def test_failed_structured_claim_is_insufficient():
    data = deepcopy(BASE_RESULT)

    data["claim_verification"]["status"] = "failed"
    data["claim_verification"]["verified_facts"] = []

    result = build_evidence_coverage(data)

    assert result["status"] == "insufficient"
    assert result["structured_claims"]["supported"] == 0


def test_unsupported_narrative_is_insufficient():
    data = deepcopy(BASE_RESULT)

    data["narrative_review"]["status"] = "flagged"

    data["narrative_review"]["sections"][1][
        "verdict"
    ] = "unsupported"

    result = build_evidence_coverage(data)

    assert result["status"] == "insufficient"
    assert result["narrative_sections"]["unsupported"] == 1


def test_missing_supporting_table_is_not_automatically_bad():
    data = deepcopy(BASE_RESULT)

    # Correlation evidence normally uses E1,
    # without a grouped supporting table E2.
    del data["evidence"]["E2"]

    result = build_evidence_coverage(data)

    assert result["status"] == "qualified"
    assert result["supporting_table"] is None


def test_incomplete_narrative_review_is_insufficient():
    data = deepcopy(BASE_RESULT)

    data["narrative_review"]["sections"] = [
        {
            "section": "headline",
            "verdict": "supported",
        }
    ]

    result = build_evidence_coverage(data)

    assert result["status"] == "insufficient"


def test_reviewed_pipeline_includes_evidence_coverage(
    monkeypatch,
):
    monkeypatch.setattr(
        narrative_review_service,
        "generate_insight_draft",
        lambda **kwargs: {
            **deepcopy(BASE_RESULT),
            "insight_status": "pending_claim_verification",
        },
    )

    monkeypatch.setattr(
        narrative_review_service,
        "review_insight_narrative",
        lambda **kwargs: deepcopy(
            BASE_RESULT["narrative_review"]
        ),
    )

    result = (
        narrative_review_service.generate_reviewed_insight(
            dataset_id="test-dataset",
            question="Which region leads?",
        )
    )

    assert "evidence_coverage" in result

    assert (
        result["evidence_coverage"]["status"]
        == "qualified"
    )

    assert (
        result["insight_status"]
        == "reviewed_not_published"
    )