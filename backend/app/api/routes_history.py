
import re
import sqlite3

from fastapi import APIRouter, HTTPException, Query

from app.services.analysis_history_service import (
    get_saved_analysis,
    list_saved_analyses,
)


router = APIRouter(
    prefix="/analysis/history",
    tags=["Analysis History"],
)


@router.get("")
def get_analysis_history(
    dataset_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    """
    List previously saved verified analyses.

    Optionally filter by dataset_id.
    Returns metadata without full analysis JSON.
    """
    try:
        records = list_saved_analyses(
            dataset_id=dataset_id,
            limit=limit,
        )

        return {
            "items": records,
            "count": len(records),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except (sqlite3.Error, OSError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Analysis history storage is unavailable.",
        ) from exc


@router.get("/{analysis_id}")
def get_analysis_history_detail(
    analysis_id: str,
):
    """
    Retrieve one saved analysis including its
    original answer, chart, table and evaluation.

    Does not call OpenAI or rerun pandas.
    """
    normalized_id = analysis_id.lower()

    if re.fullmatch(r"[0-9a-f]{32}", normalized_id) is None:
        raise HTTPException(
            status_code=422,
            detail="Invalid analysis ID format.",
        )

    try:
        return get_saved_analysis(normalized_id)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Saved analysis not found.",
        ) from exc

    except (sqlite3.Error, OSError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Analysis history storage is unavailable.",
        ) from exc
