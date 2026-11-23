
from copy import deepcopy
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import analysis_history_service as history


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "history.db"

    monkeypatch.setattr(
        history,
        "DEFAULT_DB_PATH",
        db_path,
    )

    with TestClient(app) as test_client:
        yield test_client


def make_analysis(dataset_id=None):
    return {
        "analysis_id": uuid4().hex,
        "dataset_id": dataset_id or str(uuid4()),
        "question": "Which region has the highest revenue?",
        "analysis_plan": {
            "analysis_type": "groupby_aggregation_desc",
        },
        "answer": "North leads with 110.25.",
        "table": [
            {"region": "North", "revenue": 110.25},
            {"region": "West", "revenue": 68.99},
        ],
        "chart": {
            "type": "bar",
            "x_key": "region",
            "y_key": "revenue",
            "data": [
                {"region": "North", "revenue": 110.25},
                {"region": "West", "revenue": 68.99},
            ],
        },
        "calculation_trace": {
            "operation": "groupby_sum",
        },
        "evaluation": {
            "status": "passed",
        },
    }


def test_history_list_returns_metadata(client):
    first = make_analysis()
    second = make_analysis()

    history.save_analysis_result(first)
    history.save_analysis_result(second)

    response = client.get("/api/analysis/history")

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 2
    assert len(data["items"]) == 2

    ids = {
        item["analysis_id"]
        for item in data["items"]
    }

    assert ids == {
        first["analysis_id"],
        second["analysis_id"],
    }

    for item in data["items"]:
        assert "analysis" not in item
        assert item["evaluation_status"] == "passed"


def test_history_can_filter_by_dataset(client):
    first = make_analysis()
    second = make_analysis()

    history.save_analysis_result(first)
    history.save_analysis_result(second)

    response = client.get(
        "/api/analysis/history",
        params={"dataset_id": first["dataset_id"]},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 1

    item = response.json()["items"][0]

    assert item["analysis_id"] == first["analysis_id"]


def test_history_detail_returns_original_result(client):
    analysis = make_analysis()

    history.save_analysis_result(analysis)

    response = client.get(
        f"/api/analysis/history/{analysis['analysis_id']}"
    )

    assert response.status_code == 200

    saved = response.json()

    assert saved["analysis_id"] == analysis["analysis_id"]
    assert saved["analysis"] == analysis

    assert saved["analysis"]["answer"] == analysis["answer"]
    assert saved["analysis"]["chart"] == analysis["chart"]
    assert saved["analysis"]["table"] == analysis["table"]


def test_missing_analysis_returns_404(client):
    response = client.get(
        f"/api/analysis/history/{uuid4().hex}"
    )

    assert response.status_code == 404


def test_invalid_analysis_id_returns_422(client):
    response = client.get(
        "/api/analysis/history/not-a-valid-id"
    )

    assert response.status_code == 422


def test_invalid_pagination_limit_returns_422(client):
    response = client.get(
        "/api/analysis/history",
        params={"limit": 0},
    )

    assert response.status_code == 422


def test_invalid_dataset_filter_returns_422(client):
    response = client.get(
        "/api/analysis/history",
        params={"dataset_id": "not-a-uuid"},
    )

    assert response.status_code == 422
