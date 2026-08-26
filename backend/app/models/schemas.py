from pydantic import BaseModel, Field


class AnalysisQuestionRequest(BaseModel):
    dataset_id: str = Field(..., description="Unique ID of the uploaded dataset")
    question: str = Field(..., min_length=3, description="Business question about the dataset")
    