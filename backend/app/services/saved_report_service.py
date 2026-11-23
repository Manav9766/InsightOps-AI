
import json
import re
import sqlite3

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.services.analysis_history_service import (
    get_connection,
)


ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")

SUPPORTED_TYPES_WITH_TABLE = {
    "groupby_aggregation_desc",
    "groupby_aggregation_asc",
    "time_trend",
}


def _connect(db_path: str | Path | None = None):
    """
    Create report tables without replacing
    existing P5-01 analysis history records.
    """
    connection = get_connection(db_path)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS saved_reports (
                    report_id TEXT PRIMARY KEY,
                    analysis_id TEXT NOT NULL,
                    dataset_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    title TEXT NOT NULL,
                    insight_status TEXT NOT NULL,
                    review_status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    report_json TEXT NOT NULL,

                    FOREIGN KEY (analysis_id)
                        REFERENCES analysis_history(analysis_id)
                )
            """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS
                    idx_saved_reports_analysis
                ON saved_reports (
                    analysis_id,
                    created_at DESC
                )
            """)

    except Exception:
        connection.close()
        raise

    return connection


def initialize_reports_db(
    db_path: str | Path | None = None,
):
    with closing(_connect(db_path)):
        pass


def save_reviewed_report(
    review: dict,
    db_path: str | Path | None = None,
) -> str:
    """
    Save a server-generated reviewed insight.

    The report is linked to an existing verified
    analysis stored in SQLite.

    Reports are saved as unpublished snapshots.
    """

    if not isinstance(review, dict):
        raise ValueError("Invalid report.")

    analysis_id = review.get("analysis_id")

    if (
        not isinstance(analysis_id, str)
        or ID_PATTERN.fullmatch(analysis_id) is None
    ):
        raise ValueError("A valid analysis_id is required.")

    insight_status = review.get("insight_status")

    if insight_status not in {
        "reviewed_not_published",
        "requires_revision",
    }:
        raise ValueError(
            "Only completed review results may be saved."
        )

    required_objects = (
        "insight_draft",
        "evidence",
        "calculation_evaluation",
        "claim_verification",
        "narrative_review",
        "evidence_coverage",
    )

    for key in required_objects:
        if not isinstance(review.get(key), dict):
            raise ValueError(
                f"Report is missing required section: {key}"
            )

    draft = review["insight_draft"]
    title = draft.get("headline")

    if not isinstance(title, str) or not title.strip():
        raise ValueError("Report headline is required.")

    evaluation = review["calculation_evaluation"]
    claims = review["claim_verification"]
    narrative = review["narrative_review"]
    coverage = review["evidence_coverage"]

    if evaluation.get("status") != "passed":
        raise ValueError(
            "Cannot save a report with unverified calculations."
        )

    # A saved draft is not automatically approved.
    if narrative.get("publication_ready") is not False:
        raise ValueError(
            "Only unpublished reports may be saved."
        )

    review_status = narrative.get("status")

    if review_status not in {
        "supported",
        "qualified",
        "flagged",
        "blocked",
    }:
        raise ValueError("Invalid narrative review status.")

    if insight_status == "reviewed_not_published":
        if (
            claims.get("status") != "passed"
            or review_status not in {"supported", "qualified"}
            or coverage.get("status")
            not in {"direct_support", "qualified"}
        ):
            raise ValueError(
                "Report verification statuses are inconsistent."
            )

    # Prevent non-JSON values such as NaN from
    # being silently stored.
    report_json = json.dumps(
        review,
        ensure_ascii=False,
        allow_nan=False,
    )

    with closing(_connect(db_path)) as connection:
        source = connection.execute(
            """
            SELECT
                dataset_id,
                question,
                analysis_type,
                evaluation_status,
                analysis_json
            FROM analysis_history
            WHERE analysis_id = ?
            """,
            (analysis_id,),
        ).fetchone()

        if source is None:
            raise FileNotFoundError(
                "The original saved analysis was not found."
            )

        if (
            source["dataset_id"] != review.get("dataset_id")
            or source["question"] != review.get("question")
            or source["analysis_type"]
            != review.get("analysis_type")
        ):
            raise ValueError(
                "Report does not match its saved analysis."
            )

        analysis = json.loads(source["analysis_json"])

        if (
            source["evaluation_status"] != "passed"
            or evaluation != analysis.get("evaluation")
        ):
            raise ValueError(
                "Report calculation verification does not "
                "match the saved analysis."
            )

        evidence = review["evidence"]

        if (
            evidence.get("E1", {}).get("data")
            != analysis.get("calculation_trace")
        ):
            raise ValueError(
                "Report calculation evidence does not "
                "match the saved analysis."
            )

        if (
            source["analysis_type"]
            in SUPPORTED_TYPES_WITH_TABLE
        ):
            table = analysis.get("table")

            if not isinstance(table, list):
                raise ValueError(
                    "Saved analysis has no supporting table."
                )

            expected_rows = table[:12]
            supporting = evidence.get("E2") or {}

            if (
                supporting.get("rows") != expected_rows
                or supporting.get("rows_in_result")
                != len(table)
                or supporting.get("rows_included")
                != len(expected_rows)
            ):
                raise ValueError(
                    "Report supporting evidence does not "
                    "match the saved analysis."
                )

        report_id = uuid4().hex

        created_at = datetime.now(
            timezone.utc
        ).isoformat(timespec="microseconds")

        with connection:
            connection.execute(
                """
                INSERT INTO saved_reports (
                    report_id,
                    analysis_id,
                    dataset_id,
                    question,
                    title,
                    insight_status,
                    review_status,
                    created_at,
                    report_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    analysis_id,
                    review["dataset_id"],
                    review["question"],
                    title.strip(),
                    insight_status,
                    review_status,
                    created_at,
                    report_json,
                ),
            )

    return report_id


def list_saved_reports(
    analysis_id: str | None = None,
    limit: int = 50,
    db_path: str | Path | None = None,
) -> list[dict]:
    if not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100.")

    query = """
        SELECT
            report_id,
            analysis_id,
            dataset_id,
            question,
            title,
            insight_status,
            review_status,
            created_at
        FROM saved_reports
    """

    parameters = []

    if analysis_id is not None:
        if ID_PATTERN.fullmatch(analysis_id) is None:
            raise ValueError("Invalid analysis_id.")

        query += " WHERE analysis_id = ?"
        parameters.append(analysis_id)

    query += """
        ORDER BY created_at DESC, report_id DESC
        LIMIT ?
    """

    parameters.append(limit)

    with closing(_connect(db_path)) as connection:
        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

    return [dict(row) for row in rows]


def get_saved_report(
    report_id: str,
    db_path: str | Path | None = None,
) -> dict:
    if ID_PATTERN.fullmatch(report_id) is None:
        raise ValueError("Invalid report_id.")

    with closing(_connect(db_path)) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM saved_reports
            WHERE report_id = ?
            """,
            (report_id,),
        ).fetchone()

    if row is None:
        raise FileNotFoundError(
            "Saved report not found."
        )

    return {
        "report_id": row["report_id"],
        "analysis_id": row["analysis_id"],
        "dataset_id": row["dataset_id"],
        "question": row["question"],
        "title": row["title"],
        "insight_status": row["insight_status"],
        "review_status": row["review_status"],
        "created_at": row["created_at"],
        "report": json.loads(row["report_json"]),
    }
