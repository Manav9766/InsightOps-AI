from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api import routes_analysis
from app.models.insight_schema import (
    FactualClaim,
    InsightDraft,
)
from app.services import (
    insight_service,
    narrative_review_service,
    verified_analysis_store,
)


client = TestClient(app)

QUESTION = "Which region has the highest revenue?"

ANALYSIS = {
    "dataset_id": "test-dataset",
    "question": QUESTION,
    "analysis_plan": {
        "analysis_type": "groupby_aggregation_desc",
    },
    "answer": "North has the highest revenue.",
    "table": [
        {"region": "North", "revenue": 110.25},
        {"region": "West", "revenue": 68.99},
    ],
    "chart": {
        "type": "bar",
    },
    "calculation_trace": {
        "operation": "groupby_sum",
        "group_by": "region",
        "metric": "revenue",
        "sort_direction": "desc",
        "rows_returned": 2,
    },
    "evaluation": {
        "status": "passed",
    },
}


def test_review_reuses_original_execution(monkeypatch):
    execution_count = 0

    def fake_execute(**kwargs):
        nonlocal execution_count
        execution_count += 1
        return deepcopy(ANALYSIS)

    def fail_if_reexecuted(**kwargs):
        raise AssertionError(
            "The analysis must not execute twice."
        )

    monkeypatch.setattr(
        routes_analysis,
        "analyze_dataset_with_llm",
        fake_execute,
    )

    monkeypatch.setattr(
        routes_analysis,
        "save_analysis_result",
        lambda result: result["analysis_id"],
    )

    monkeypatch.setattr(
        routes_analysis,
        "save_reviewed_report",
        lambda result: "f" * 32,
    )

    monkeypatch.setattr(
        insight_service,
        "analyze_dataset_with_llm",
        fail_if_reexecuted,
    )

    monkeypatch.setenv(
        "OPENAI_API_KEY",
        "test-key",
    )

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.responses = self

        def parse(self, **kwargs):
            draft = InsightDraft(
                headline="North leads revenue",
                observation=(
                    "North has the highest revenue "
                    "at 110.25 units."
                ),
                business_implication=(
                    "Further investigation could "
                    "identify growth opportunities."
                ),
                evidence_ids=["E2"],
                limitations=[
                    "Profitability is unknown."
                ],
                follow_up_questions=[
                    "What are the profit margins?"
                ],
                factual_claims=[
                    FactualClaim(
                        kind="group_extreme",
                        metric="revenue",
                        dimension="region",
                        member="North",
                        rank="highest",
                        value=110.25,
                        evidence_id="E2",
                    )
                ],
            )

            return SimpleNamespace(
                output_parsed=draft
            )

    monkeypatch.setattr(
        insight_service,
        "OpenAI",
        FakeOpenAI,
    )

    monkeypatch.setattr(
        narrative_review_service,
        "review_insight_narrative",
        lambda **kwargs: {
            "status": "qualified",
            "sections": [],
            "publication_ready": False,
        },
    )

    execute_response = client.post(
        "/api/analysis/execute",
        json={
            "dataset_id": "test-dataset",
            "question": QUESTION,
        },
    )

    assert execute_response.status_code == 200

    analysis_id = execute_response.json()["analysis_id"]

    review_response = client.post(
        "/api/analysis/insights/review",
        json={
            "dataset_id": "test-dataset",
            "question": QUESTION,
            "analysis_id": analysis_id,
        },
    )

    assert review_response.status_code == 200

    review = review_response.json()

    assert execution_count == 1
    assert review["analysis_id"] == analysis_id

    assert (
        review["claim_verification"]["status"]
        == "passed"
    )

    assert (
        review["evidence"]["E2"]["rows"]
        == ANALYSIS["table"]
    )


def test_question_mismatch_is_rejected():
    analysis_id = (
        verified_analysis_store.store_verified_analysis(
            ANALYSIS
        )
    )

    response = client.post(
        "/api/analysis/insights/review",
        json={
            "dataset_id": "test-dataset",
            "question": "What is the total revenue?",
            "analysis_id": analysis_id,
        },
    )

    assert response.status_code == 422


def test_unknown_analysis_id_returns_404():
    response = client.post(
        "/api/analysis/insights/review",
        json={
            "dataset_id": "test-dataset",
            "question": QUESTION,
            "analysis_id": "0" * 32,
        },
    )

    assert response.status_code == 404
    assert "expired" in response.json()["detail"]


def test_cached_analysis_is_defensively_copied():
    analysis_id = (
        verified_analysis_store.store_verified_analysis(
            ANALYSIS
        )
    )

    first = verified_analysis_store.get_verified_analysis(
        analysis_id,
        "test-dataset",
        QUESTION,
    )

    first["table"][0]["revenue"] = 9999

    second = verified_analysis_store.get_verified_analysis(
        analysis_id,
        "test-dataset",
        QUESTION,
    )

    assert second["table"][0]["revenue"] == 110.25


def test_expired_analysis_is_rejected(monkeypatch):
    monkeypatch.setattr(
        verified_analysis_store,
        "TTL_SECONDS",
        -1,
    )

    analysis_id = (
        verified_analysis_store.store_verified_analysis(
            ANALYSIS
        )
    )

    with pytest.raises(
        verified_analysis_store.CachedAnalysisNotFound
    ):
        verified_analysis_store.get_verified_analysis(
            analysis_id,
            "test-dataset",
            QUESTION,
        )
