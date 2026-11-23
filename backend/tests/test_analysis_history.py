from copy import deepcopy
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api import routes_analysis
from app.services import analysis_history_service

from app.services.analysis_history_service import (
    initialize_history_db,
    save_analysis_result,
    get_saved_analysis,
    list_saved_analyses,
)


DATASET_ID = (
    "1360862f-359f-45f0-a34e-0e65a86a664d"
)


BASE_ANALYSIS = {
    "analysis_id": (
        "d346e9e61b6d48fd920d1f71a8d07c5b"
    ),
    "dataset_id": DATASET_ID,
    "question": (
        "Which region has the highest revenue?"
    ),
    "analysis_plan": {
        "analysis_type": (
            "groupby_aggregation_desc"
        ),
    },
    "answer": (
        "North has the highest revenue."
    ),
    "table": [
        {
            "region": "North",
            "revenue": 110.25,
        },
        {
            "region": "West",
            "revenue": 68.99,
        },
    ],
    "evaluation": {
        "status": "passed",
    },
}


def test_database_initialization(tmp_path):
    db_path = tmp_path / "history.db"

    initialize_history_db(db_path)

    assert db_path.exists()

    # Reinitialization must preserve the schema.
    initialize_history_db(db_path)

    with sqlite3.connect(db_path) as connection:
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

    assert (
        "analysis_history",
    ) in tables


def test_save_and_retrieve_analysis(tmp_path):
    db_path = tmp_path / "history.db"

    analysis = deepcopy(BASE_ANALYSIS)

    saved_id = save_analysis_result(
        analysis,
        db_path=db_path,
    )

    result = get_saved_analysis(
        saved_id,
        db_path=db_path,
    )

    assert saved_id == analysis["analysis_id"]

    assert result["dataset_id"] == DATASET_ID

    assert result["evaluation_status"] == "passed"

    assert result["analysis"] == analysis


def test_unverified_analysis_cannot_be_saved(tmp_path):
    db_path = tmp_path / "history.db"

    analysis = deepcopy(BASE_ANALYSIS)

    analysis["evaluation"]["status"] = "failed"

    with pytest.raises(ValueError):
        save_analysis_result(
            analysis,
            db_path=db_path,
        )


def test_duplicate_analysis_id_is_rejected(tmp_path):
    db_path = tmp_path / "history.db"

    save_analysis_result(
        deepcopy(BASE_ANALYSIS),
        db_path=db_path,
    )

    with pytest.raises(
        sqlite3.IntegrityError
    ):
        save_analysis_result(
            deepcopy(BASE_ANALYSIS),
            db_path=db_path,
        )


def test_history_list_contains_saved_analysis(tmp_path):
    db_path = tmp_path / "history.db"

    save_analysis_result(
        deepcopy(BASE_ANALYSIS),
        db_path=db_path,
    )

    results = list_saved_analyses(
        dataset_id=DATASET_ID,
        db_path=db_path,
    )

    assert len(results) == 1

    assert (
        results[0]["analysis_id"]
        == BASE_ANALYSIS["analysis_id"]
    )

    assert "analysis" not in results[0]


def test_saved_analysis_survives_new_connection(tmp_path):
    db_path = tmp_path / "history.db"

    save_analysis_result(
        deepcopy(BASE_ANALYSIS),
        db_path=db_path,
    )

    # Retrieval opens an independent connection,
    # proving that data was committed to disk.
    restored = get_saved_analysis(
        BASE_ANALYSIS["analysis_id"],
        db_path=db_path,
    )

    assert (
        restored["analysis"]["table"][0]["revenue"]
        == 110.25
    )


def test_missing_saved_analysis_returns_error(tmp_path):
    db_path = tmp_path / "history.db"

    with pytest.raises(
        FileNotFoundError
    ):
        get_saved_analysis(
            "0" * 32,
            db_path=db_path,
        )


def test_verified_api_analysis_is_persisted(
    tmp_path,
    monkeypatch,
):
    db_path = tmp_path / "history.db"

    monkeypatch.setattr(
        analysis_history_service,
        "DEFAULT_DB_PATH",
        db_path,
    )

    analysis = deepcopy(BASE_ANALYSIS)
    analysis.pop("analysis_id")

    monkeypatch.setattr(
        routes_analysis,
        "analyze_dataset_with_llm",
        lambda **kwargs: deepcopy(analysis),
    )

    client = TestClient(app)

    response = client.post(
        "/api/analysis/execute",
        json={
            "dataset_id": DATASET_ID,
            "question": analysis["question"],
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["analysis_id"]
