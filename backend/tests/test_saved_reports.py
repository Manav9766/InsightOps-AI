
from copy import deepcopy
from uuid import uuid4
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api import routes_analysis

from app.services import analysis_history_service as history
from app.services import saved_report_service as reports
from app.services.verified_analysis_store import (
    store_verified_analysis,
)


def make_analysis():
    return {
        "analysis_id": uuid4().hex,
        "dataset_id": str(uuid4()),
        "question": "Which region has the highest revenue?",
        "analysis_plan": {
            "analysis_type": "groupby_aggregation_desc",
        },
        "answer": "North has the highest revenue: 110.25.",
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
            "status": "passed",
        },
    }


def make_review(analysis):
    return {
        "analysis_id": analysis["analysis_id"],
        "dataset_id": analysis["dataset_id"],
        "question": analysis["question"],
        "analysis_type": "groupby_aggregation_desc",
        "insight_status": "reviewed_not_published",
        "insight_draft": {
            "headline": "North Leads Revenue",
            "observation": "North has the highest revenue.",
            "business_implication": (
                "Further investigation may be useful."
            ),
            "evidence_ids": ["E2"],
            "limitations": [
                "Profitability is unknown."
            ],
            "follow_up_questions": [
                "What are the profit margins?"
            ],
            "factual_claims": [
                {
                    "kind": "group_extreme",
                    "metric": "revenue",
                    "dimension": "region",
                    "member": "North",
                    "rank": "highest",
                    "value": 110.25,
                    "evidence_id": "E2",
                }
            ],
        },
        "evidence": {
            "E1": {
                "type": "verified_calculation_trace",
                "data": deepcopy(
                    analysis["calculation_trace"]
                ),
            },
            "E2": {
                "type": "verified_supporting_table",
                "rows": deepcopy(analysis["table"]),
                "rows_in_result": 2,
                "rows_included": 2,
            },
        },
        "calculation_evaluation": deepcopy(
            analysis["evaluation"]
        ),
        "claim_verification": {
            "status": "passed",
            "verified_facts": [
                {
                    "claim_index": 0,
                    "status": "supported",
                    "evidence_id": "E2",
                }
            ],
            "rejected_claims": [],
        },
        "narrative_review": {
            "status": "qualified",
            "method": "llm_assisted_review",
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
            "publication_ready": False,
        },
        "evidence_coverage": {
            "status": "qualified",
        },
    }


@pytest.fixture
def saved_source(tmp_path, monkeypatch):
    db_path = tmp_path / "history.db"

    monkeypatch.setattr(
        history,
        "DEFAULT_DB_PATH",
        db_path,
    )

    analysis = make_analysis()
    history.save_analysis_result(analysis)

    return analysis, db_path


def test_report_schema_is_idempotent(saved_source):
    _, db_path = saved_source

    reports.initialize_reports_db(db_path)
    reports.initialize_reports_db(db_path)

    with sqlite3.connect(db_path) as connection:
        tables = connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

    assert ("saved_reports",) in tables
    assert ("analysis_history",) in tables


def test_save_and_retrieve_report(saved_source):
    analysis, db_path = saved_source
    review = make_review(analysis)

    report_id = reports.save_reviewed_report(
        review,
        db_path,
    )

    restored = reports.get_saved_report(
        report_id,
        db_path,
    )

    assert restored["report_id"] == report_id
    assert restored["analysis_id"] == analysis["analysis_id"]
    assert restored["report"] == review
    assert restored["review_status"] == "qualified"
    assert restored["insight_status"] == "reviewed_not_published"


def test_multiple_reports_for_one_analysis(saved_source):
    analysis, db_path = saved_source
    review = make_review(analysis)

    first = reports.save_reviewed_report(review, db_path)
    second = reports.save_reviewed_report(review, db_path)

    assert first != second

    history_rows = reports.list_saved_reports(
        analysis_id=analysis["analysis_id"],
        db_path=db_path,
    )

    assert len(history_rows) == 2
    assert {row["report_id"] for row in history_rows} == {
        first,
        second,
    }


def test_mismatched_evidence_is_rejected(saved_source):
    analysis, db_path = saved_source
    review = make_review(analysis)

    review["evidence"]["E2"]["rows"][0]["revenue"] = 999

    with pytest.raises(ValueError):
        reports.save_reviewed_report(review, db_path)


def test_unverified_report_is_rejected(saved_source):
    analysis, db_path = saved_source
    review = make_review(analysis)

    review["calculation_evaluation"]["status"] = "failed"

    with pytest.raises(ValueError):
        reports.save_reviewed_report(review, db_path)


def test_missing_original_analysis_is_rejected(saved_source):
    analysis, db_path = saved_source
    review = make_review(analysis)

    review["analysis_id"] = uuid4().hex

    with pytest.raises(FileNotFoundError):
        reports.save_reviewed_report(review, db_path)


def test_list_reports_filters_by_analysis(saved_source):
    analysis, db_path = saved_source

    report_id = reports.save_reviewed_report(
        make_review(analysis),
        db_path,
    )

    rows = reports.list_saved_reports(
        analysis_id=analysis["analysis_id"],
        db_path=db_path,
    )

    assert len(rows) == 1
    assert rows[0]["report_id"] == report_id
    assert "report" not in rows[0]


def test_review_endpoint_saves_real_report(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        history,
        "DEFAULT_DB_PATH",
        tmp_path / "history.db",
    )

    analysis = make_analysis()

    # Use the actual P4-05 cache ID.
    analysis.pop("analysis_id")

    analysis_id = store_verified_analysis(analysis)
    analysis["analysis_id"] = analysis_id

    history.save_analysis_result(analysis)

    def fake_review(
        dataset_id,
        question,
        verified_analysis,
    ):
        assert dataset_id == analysis["dataset_id"]
        assert question == analysis["question"]
        assert verified_analysis["table"] == analysis["table"]

        return make_review(analysis)

    monkeypatch.setattr(
        routes_analysis,
        "generate_reviewed_insight",
        fake_review,
    )

    client = TestClient(app)

    response = client.post(
        "/api/analysis/insights/review",
        json={
            "dataset_id": analysis["dataset_id"],
            "question": analysis["question"],
            "analysis_id": analysis_id,
        },
    )

    assert response.status_code == 200

    result = response.json()
    assert result["report_id"]

    listed = client.get("/api/analysis/reports")
    assert listed.status_code == 200
    assert listed.json()["count"] == 1

    restored = client.get(
        f"/api/analysis/reports/{result['report_id']}"
    )

    assert restored.status_code == 200

    saved = restored.json()

    assert saved["analysis_id"] == analysis_id
    assert saved["report"]["insight_draft"] == (
        result["insight_draft"]
    )
    assert saved["report"]["evidence_coverage"] == (
        result["evidence_coverage"]
    )


def test_invalid_report_id_returns_422(saved_source):
    client = TestClient(app)

    response = client.get(
        "/api/analysis/reports/not-a-valid-id"
    )

    assert response.status_code == 422
