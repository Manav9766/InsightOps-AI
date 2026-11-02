from fastapi import APIRouter, HTTPException

from app.models.schemas import AnalysisQuestionRequest
from app.services.analysis_service import answer_dataset_question

from openai import OpenAIError

from app.services.file_service import get_dataset_file_path
from app.services.profiling_service import profile_dataset
from app.services.llm_planning_service import create_llm_analysis_plan
from app.services.llm_execution_service import analyze_dataset_with_llm
router = APIRouter(tags=["Analysis"])


@router.post("/analysis/plan")
def preview_llm_analysis_plan(
    request: AnalysisQuestionRequest,
):
    """
    Generates a structured LLM plan without executing it.
    """
    try:
        file_path = get_dataset_file_path(request.dataset_id)
        profile = profile_dataset(file_path)

        plan = create_llm_analysis_plan(
            question=request.question,
            profile=profile,
        )

        return {
            "dataset_id": request.dataset_id,
            "question": request.question,
            "planner": "openai",
            "analysis_plan": plan,
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )

    except OpenAIError:
        raise HTTPException(
            status_code=502,
            detail="AI planning service is unavailable.",
        )

    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="AI planning service is not configured.",
        )

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


@router.post("/analysis/execute")
def execute_llm_analysis(
    request: AnalysisQuestionRequest,
):
    """
    Generates a validated LLM plan and executes it
    through the existing pandas analysis engine.
    """
    try:
        return analyze_dataset_with_llm(
            dataset_id=request.dataset_id,
            question=request.question,
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found.",
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )

    except OpenAIError:
        raise HTTPException(
            status_code=502,
            detail="AI planning service is unavailable.",
        )

    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="AI planning service is not configured.",
        )
