
from fastapi.testclient import TestClient

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
