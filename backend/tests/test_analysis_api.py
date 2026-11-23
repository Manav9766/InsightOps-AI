
from fastapi.testclient import TestClient
from openai import OpenAIError
import pytest

from app.main import app
from app.api import routes_analysis


client = TestClient(app)

REQUEST = {
    "dataset_id": "test-dataset-id",
    "question": "Which region has the highest revenue?",
}


def test_invalid_plan_returns_422(monkeypatch):
    def fake_execute(**kwargs):
        raise ValueError("Invalid metric column: fake_profit")

    monkeypatch.setattr(
        routes_analysis,
        "analyze_dataset_with_llm",
        fake_execute,
    )

    response = client.post(
        "/api/analysis/execute",
        json=REQUEST,
    )

    assert response.status_code == 422
    assert "Invalid metric column" in response.json()["detail"]


def test_missing_dataset_returns_404(monkeypatch):
    def fake_execute(**kwargs):
        raise FileNotFoundError("Missing dataset")

    monkeypatch.setattr(
        routes_analysis,
        "analyze_dataset_with_llm",
        fake_execute,
    )

    response = client.post(
        "/api/analysis/execute",
        json=REQUEST,
    )

    assert response.status_code == 404


def test_unconfigured_ai_returns_503(monkeypatch):
    def fake_execute(**kwargs):
        raise RuntimeError("OPENAI_API_KEY is not configured")

    monkeypatch.setattr(
        routes_analysis,
        "analyze_dataset_with_llm",
        fake_execute,
    )

    response = client.post(
        "/api/analysis/execute",
        json=REQUEST,
    )

    assert response.status_code == 503


def test_review_insight_returns_service_result(monkeypatch):
    expected = {
        "insight_status": "reviewed_not_published",
        "narrative_review": {"status": "supported"},
    }

    def fake_review(**kwargs):
        assert kwargs == REQUEST
        return expected

    monkeypatch.setattr(
        routes_analysis,
        "generate_reviewed_insight",
        fake_review,
    )

    response = client.post("/api/analysis/insights/review", json=REQUEST)

    assert response.status_code == 200
    assert response.json() == expected


@pytest.mark.parametrize(
    "error,status_code,detail",
    [
        (FileNotFoundError(), 404, "Dataset not found."),
        (ValueError("Invalid analysis"), 422, "Invalid analysis"),
        (
            routes_analysis.NarrativeReviewError(),
            502,
            "AI narrative review returned an invalid result.",
        ),
        (OpenAIError(), 502, "AI narrative review service is unavailable."),
        (RuntimeError(), 503, "AI narrative review service is not configured."),
        (ArithmeticError(), 500, "Independent calculation verification failed."),
    ],
)
def test_review_insight_maps_service_errors(monkeypatch, error, status_code, detail):
    def fake_review(**kwargs):
        raise error

    monkeypatch.setattr(
        routes_analysis,
        "generate_reviewed_insight",
        fake_review,
    )

    response = client.post("/api/analysis/insights/review", json=REQUEST)

    assert response.status_code == status_code
    assert response.json()["detail"] == detail


def test_review_insight_reuses_original_analysis(monkeypatch):
    analysis = {
        **REQUEST,
        "evaluation": {"status": "passed"},
        "table": [{"region": "North", "revenue": 110.25}],
    }
    analysis_id = routes_analysis.store_verified_analysis(analysis)

    def fake_review(**kwargs):
        assert kwargs == {**REQUEST, "verified_analysis": analysis}
        return {"insight_status": "reviewed_not_published"}

    monkeypatch.setattr(routes_analysis, "generate_reviewed_insight", fake_review)
    monkeypatch.setattr(
        routes_analysis,
        "save_reviewed_report",
        lambda result: "f" * 32,
    )

    response = client.post(
        "/api/analysis/insights/review",
        json={**REQUEST, "analysis_id": analysis_id},
    )

    assert response.status_code == 200
    assert response.json()["analysis_id"] == analysis_id
    assert response.json()["report_id"] == "f" * 32


def test_missing_cached_analysis_returns_404_without_generating(monkeypatch):
    def missing_analysis(**kwargs):
        raise routes_analysis.CachedAnalysisNotFound("Analysis not found or expired.")

    def unexpected_review(**kwargs):
        pytest.fail("Unavailable analysis must not trigger fresh insight generation")

    monkeypatch.setattr(routes_analysis, "get_verified_analysis", missing_analysis)
    monkeypatch.setattr(routes_analysis, "generate_reviewed_insight", unexpected_review)

    response = client.post(
        "/api/analysis/insights/review",
        json={**REQUEST, "analysis_id": "a" * 32},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Analysis not found or expired."


@pytest.mark.parametrize(
    "changes",
    [{"dataset_id": "another-dataset"}, {"question": "Another question?"}],
)
def test_cached_analysis_mismatch_returns_422(monkeypatch, changes):
    analysis_id = routes_analysis.store_verified_analysis({
        **REQUEST,
        "evaluation": {"status": "passed"},
    })

    def unexpected_review(**kwargs):
        pytest.fail("Mismatched analysis must not trigger insight generation")

    monkeypatch.setattr(routes_analysis, "generate_reviewed_insight", unexpected_review)

    response = client.post(
        "/api/analysis/insights/review",
        json={**REQUEST, **changes, "analysis_id": analysis_id},
    )

    assert response.status_code == 422
    assert "does not match" in response.json()["detail"]
