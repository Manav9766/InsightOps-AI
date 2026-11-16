
from types import SimpleNamespace

import pytest

from app.models.insight_schema import InsightDraft
from app.services import insight_service


def sample_analysis(status="passed"):
    return {
        "analysis_plan": {
            "analysis_type": "groupby_aggregation_desc",
        },
        "table": [
            {"region": "North", "revenue": 110.25},
            {"region": "West", "revenue": 68.99},
        ],
        "calculation_trace": {
            "operation": "groupby_sum",
            "group_by": "region",
            "metric": "revenue",
            "sort_direction": "desc",
            "rows_returned": 2,
        },
        "evaluation": {
            "status": status,
            "checks": {
                "table_matches_source_data": status == "passed",
            },
        },
    }


def test_unverified_calculation_is_rejected(monkeypatch):
    monkeypatch.setattr(
        insight_service,
        "analyze_dataset_with_llm",
        lambda **kwargs: sample_analysis("failed"),
    )

    with pytest.raises(ArithmeticError):
        insight_service.generate_insight_draft(
            dataset_id="test-id",
            question="Which region has the highest revenue?",
        )


def test_evidence_packet_contains_computed_results():
    evidence = insight_service.build_evidence_packet(
        sample_analysis()
    )

    assert "E1" in evidence
    assert "E2" in evidence

    assert (
        evidence["E2"]["rows"][0]["revenue"]
        == 110.25
    )


def test_valid_draft_returns_unverified_status(monkeypatch):
    monkeypatch.setenv(
        "OPENAI_API_KEY",
        "test-key",
    )

    monkeypatch.setattr(
        insight_service,
        "analyze_dataset_with_llm",
        lambda **kwargs: sample_analysis(),
    )

    draft = InsightDraft(
        headline="North leads revenue",
        observation="North leads regional revenue.",
        business_implication="The regional difference warrants investigation.",
        evidence_ids=["E1", "E2"],
        limitations=["Only a small sample is available."],
        follow_up_questions=[
            "Which products drive North's revenue?"
        ],
    )

    class FakeClient:
        def __init__(self, **kwargs):
            self.responses = self

        def parse(self, **kwargs):
            return SimpleNamespace(
                output_parsed=draft
            )

    monkeypatch.setattr(
        insight_service,
        "OpenAI",
        FakeClient,
    )

    result = insight_service.generate_insight_draft(
        dataset_id="test-id",
        question="Which region has the highest revenue?",
    )

    assert result["insight_status"] == (
        "pending_claim_verification"
    )

    assert result["insight_draft"]["headline"] == (
        "North leads revenue"
    )

    assert result["calculation_evaluation"]["status"] == (
        "passed"
    )
