
from typing import Literal

from pydantic import BaseModel


class FactualClaim(BaseModel):
    """
    A structured factual assertion produced by the LLM.

    The evaluator checks these fields against
    independently verified calculation evidence.
    """

    kind: Literal[
        "group_extreme",
        "monthly_total",
        "correlation",
    ]

    metric: str

    dimension: str | None

    member: str | None

    rank: Literal["highest", "lowest"] | None

    value: float

    evidence_id: str


class InsightDraft(BaseModel):
    """
    AI-generated business insight.

    Structured factual claims can be checked
    deterministically. The free-text narrative
    remains unverified.
    """

    headline: str

    observation: str

    business_implication: str

    evidence_ids: list[str]

    limitations: list[str]

    follow_up_questions: list[str]

    factual_claims: list[FactualClaim]
