
import pytest

from app.models.insight_schema import FactualClaim
from app.services.claim_verification_service import (
    verify_factual_claims,
)


@pytest.fixture
def grouped_analysis():
    return {
        "analysis_plan": {
            "analysis_type": "groupby_aggregation_desc",
        },
        "calculation_trace": {
            "operation": "groupby_sum",
            "group_by": "region",
            "metric": "revenue",
            "sort_direction": "desc",
            "rows_returned": 2,
        },
        "evaluation": {
            "status": "passed",
        },
    }


@pytest.fixture
def grouped_evidence():
    return {
        "E1": {
            "type": "verified_calculation_trace",
        },
        "E2": {
            "type": "verified_supporting_table",
            "rows": [
                {"region": "North", "revenue": 110.25},
                {"region": "West", "revenue": 68.99},
            ],
        },
    }


def make_group_claim(**changes):
    data = {
        "kind": "group_extreme",
        "metric": "revenue",
        "dimension": "region",
        "member": "North",
        "rank": "highest",
        "value": 110.25,
        "evidence_id": "E2",
    }

    data.update(changes)
    return FactualClaim(**data)


def test_correct_group_claim_passes(
    grouped_analysis,
    grouped_evidence,
):
    result = verify_factual_claims(
        grouped_analysis,
        grouped_evidence,
        [make_group_claim()],
    )

    assert result["status"] == "passed"
    assert len(result["verified_facts"]) == 1
    assert result["narrative_status"] == "not_verified"


@pytest.mark.parametrize(
    "change",
    [
        {"value": 999},
        {"metric": "profit"},
        {"member": "South"},
        {"rank": "lowest"},
        {"evidence_id": "E999"},
    ],
)
def test_incorrect_group_claim_is_rejected(
    grouped_analysis,
    grouped_evidence,
    change,
):
    result = verify_factual_claims(
        grouped_analysis,
        grouped_evidence,
        [make_group_claim(**change)],
    )

    assert result["status"] == "failed"
    assert len(result["rejected_claims"]) == 1


def test_monthly_total_passes():
    analysis = {
        "analysis_plan": {
            "analysis_type": "time_trend",
        },
        "calculation_trace": {
            "metric": "revenue",
        },
        "evaluation": {
            "status": "passed",
        },
    }

    evidence = {
        "E2": {
            "rows": [
                {"period": "2026-03", "revenue": 114.98},
            ],
        },
    }

    claim = FactualClaim(
        kind="monthly_total",
        metric="revenue",
        dimension="period",
        member="2026-03",
        rank=None,
        value=114.98,
        evidence_id="E2",
    )

    result = verify_factual_claims(
        analysis, evidence, [claim]
    )

    assert result["status"] == "passed"


def test_correlation_claim_passes():
    analysis = {
        "analysis_plan": {
            "analysis_type": "correlation",
        },
        "calculation_trace": {
            "x_metric": "quantity",
            "y_metric": "revenue",
            "correlation": 0.908,
            "rows_analyzed": 10,
        },
        "evaluation": {
            "status": "passed",
        },
    }

    evidence = {
        "E1": {
            "type": "verified_calculation_trace",
        },
    }

    claim = FactualClaim(
        kind="correlation",
        metric="revenue",
        dimension="quantity",
        member=None,
        rank=None,
        value=0.908,
        evidence_id="E1",
    )

    result = verify_factual_claims(
        analysis, evidence, [claim]
    )

    assert result["status"] == "passed"


def test_unverified_calculation_is_rejected(
    grouped_analysis,
    grouped_evidence,
):
    grouped_analysis["evaluation"]["status"] = "failed"

    with pytest.raises(ValueError):
        verify_factual_claims(
            grouped_analysis,
            grouped_evidence,
            [make_group_claim()],
        )
