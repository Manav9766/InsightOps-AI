from pydantic import BaseModel, Field


class AnalysisQuestionRequest(BaseModel):
    dataset_id: str = Field(..., description="Unique ID of the uploaded dataset")
    question: str = Field(..., min_length=3, description="Business question about the dataset")


class InsightReviewRequest(AnalysisQuestionRequest):
    analysis_id: str | None = Field(
        default=None,
        min_length=32,
        max_length=32,
        description=(
            "Optional ID returned by /analysis/execute. "
            "Reuses the same verified analysis."
        ),
    )
