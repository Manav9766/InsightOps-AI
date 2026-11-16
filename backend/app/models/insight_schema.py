
from pydantic import BaseModel


class InsightDraft(BaseModel):
    """
    Structured AI-generated business insight.

    Narrative claims remain unverified until
    the claim evaluator reviews them.
    """

    headline: str

    observation: str

    business_implication: str

    evidence_ids: list[str]

    limitations: list[str]

    follow_up_questions: list[str]
