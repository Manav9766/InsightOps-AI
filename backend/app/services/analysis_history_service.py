import json
import re
import sqlite3

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from app.services.file_service import (
    validate_dataset_id,
)


APP_DIR = Path(__file__).resolve().parents[1]

DEFAULT_DB_PATH = (
    APP_DIR / "storage" / "insightops_history.db"
)


def initialize_history_db(
    db_path: str | Path | None = None,
) -> Path:
    """
    Initialize persistent SQLite storage.

    Safe to call repeatedly.
    Existing records are preserved.
    """
    path = (
        Path(db_path)
        if db_path is not None
        else DEFAULT_DB_PATH
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with closing(
        sqlite3.connect(path, timeout=10)
    ) as connection:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_history (
                analysis_id TEXT PRIMARY KEY,
                dataset_id TEXT NOT NULL,
                question TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                evaluation_status TEXT NOT NULL
                    CHECK (evaluation_status = 'passed'),
                created_at TEXT NOT NULL,
                analysis_json TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_analysis_history_dataset
            ON analysis_history (
                dataset_id,
                created_at DESC
            )
            """
        )

        connection.commit()

    return path


def get_connection(
    db_path: str | Path | None = None,
) -> sqlite3.Connection:
    """
    Open a database connection after ensuring
    the schema exists.
    """
    path = initialize_history_db(db_path)

    connection = sqlite3.connect(
        path,
        timeout=10,
    )

    connection.row_factory = sqlite3.Row

    return connection


def save_analysis_result(
    analysis: dict,
    db_path: str | Path | None = None,
) -> str:
    """
    Persist an independently verified analysis.

    The existing analysis_id becomes the
    permanent database record identifier.
    """

    evaluation = analysis.get("evaluation") or {}

    if evaluation.get("status") != "passed":
        raise ValueError(
            "Only independently verified analyses "
            "can be saved."
        )

    analysis_id = analysis.get("analysis_id")

    if (
        not isinstance(analysis_id, str)
        or re.fullmatch(
            r"[0-9a-f]{32}",
            analysis_id,
        ) is None
    ):
        raise ValueError(
            "A valid analysis_id from P4-05 "
            "is required."
        )

    dataset_id = validate_dataset_id(
        analysis.get("dataset_id", "")
    )

    question = analysis.get("question")

    if (
        not isinstance(question, str)
        or not question.strip()
    ):
        raise ValueError(
            "A non-empty analysis question "
            "is required."
        )

    plan = analysis.get("analysis_plan") or {}

    analysis_type = plan.get("analysis_type")

    if not isinstance(analysis_type, str) or not analysis_type:
        raise ValueError(
            "The analysis type is missing."
        )

    # Fail rather than silently storing invalid JSON.
    analysis_json = json.dumps(
        analysis,
        ensure_ascii=False,
        allow_nan=False,
    )

    created_at = datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")

    with closing(
        get_connection(db_path)
    ) as connection:

        with connection:
            connection.execute(
                """
                INSERT INTO analysis_history (
                    analysis_id,
                    dataset_id,
                    question,
                    analysis_type,
                    evaluation_status,
                    created_at,
                    analysis_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis_id,
                    dataset_id,
                    question.strip(),
                    analysis_type,
                    "passed",
                    created_at,
                    analysis_json,
                ),
            )

    return analysis_id


def get_saved_analysis(
    analysis_id: str,
    db_path: str | Path | None = None,
) -> dict:
    """
    Retrieve a previously saved analysis.
    """

    with closing(
        get_connection(db_path)
    ) as connection:

        row = connection.execute(
            """
            SELECT
                analysis_id,
                dataset_id,
                question,
                analysis_type,
                evaluation_status,
                created_at,
                analysis_json
            FROM analysis_history
            WHERE analysis_id = ?
            """,
            (analysis_id,),
        ).fetchone()

    if row is None:
        raise FileNotFoundError(
            "Saved analysis not found."
        )

    return {
        "analysis_id": row["analysis_id"],
        "dataset_id": row["dataset_id"],
        "question": row["question"],
        "analysis_type": row["analysis_type"],
        "evaluation_status": row[
            "evaluation_status"
        ],
        "created_at": row["created_at"],
        "analysis": json.loads(
            row["analysis_json"]
        ),
    }


def list_saved_analyses(
    dataset_id: str | None = None,
    limit: int = 50,
    db_path: str | Path | None = None,
) -> list[dict]:
    """
    List saved analysis metadata.

    Does not load full result JSON for every
    history entry.
    """

    if not 1 <= limit <= 100:
        raise ValueError(
            "History limit must be between 1 and 100."
        )

    query = """
        SELECT
            analysis_id,
            dataset_id,
            question,
            analysis_type,
            evaluation_status,
            created_at
        FROM analysis_history
    """

    parameters = []

    if dataset_id is not None:
        clean_id = validate_dataset_id(
            dataset_id
        )

        query += " WHERE dataset_id = ?"

        parameters.append(clean_id)

    query += """
        ORDER BY created_at DESC, analysis_id DESC
        LIMIT ?
    """

    parameters.append(limit)

    with closing(
        get_connection(db_path)
    ) as connection:

        rows = connection.execute(
            query,
            parameters,
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]