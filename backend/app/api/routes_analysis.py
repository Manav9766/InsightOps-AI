from fastapi import APIRouter, HTTPException

from app.models.schemas import AnalysisQuestionRequest
from app.services.analysis_service import answer_dataset_question

router = APIRouter(tags=["Analysis"])


@router.post("/analysis/question")
def ask_dataset_question(request: AnalysisQuestionRequest):
    """
    Accepts a natural-language question and returns a computed pandas-based answer.
    """
    try:
        result = answer_dataset_question(
            dataset_id=request.dataset_id,
            question=request.question,
        )

        return result

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}"
        )