from typing import Literal

from pydantic import BaseModel


class NarrativeSectionReview(BaseModel):
    """
    Review result for one section of an AI insight.
    """

    section: Literal[
        "headline",
        "observation",
        "business_implication",
    ]

    verdict: Literal[
        "supported",
        "hypothesis",
        "unsupported",
    ]

    reason: str

    evidence_ids: list[str]

    suggested_rewrite: str


class NarrativeReviewResult(BaseModel):
    """
    Structured response from the narrative reviewer.

    The overall status is calculated by Python,
    not trusted directly from the LLM.
    """

    sections: list[NarrativeSectionReview]