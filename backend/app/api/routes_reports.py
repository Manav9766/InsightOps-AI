
import sqlite3

from fastapi import APIRouter, HTTPException, Query

from app.services.saved_report_service import (
    get_saved_report,
    list_saved_reports,
)


router = APIRouter(
    prefix="/analysis/reports",
    tags=["Saved Business Reports"],
)


@router.get("")
def get_reports(
    analysis_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    """
    List saved report metadata.

    Optionally filter by the original analysis ID.
    """
    try:
        reports = list_saved_reports(
            analysis_id=analysis_id,
            limit=limit,
        )

        return {
            "items": reports,
            "count": len(reports),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except (sqlite3.Error, OSError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Saved report storage is unavailable.",
        ) from exc


@router.get("/{report_id}")
def get_report_detail(report_id: str):
    """
    Retrieve an unpublished reviewed report
    without rerunning the AI or pandas.
    """
    try:
        return get_saved_report(report_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except (sqlite3.Error, OSError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Saved report storage is unavailable.",
        ) from exc
