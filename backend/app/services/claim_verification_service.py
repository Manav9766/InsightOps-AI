
import math

from app.models.insight_schema import FactualClaim


def numbers_match(actual, expected) -> bool:
    """
    Compare numeric values with a small tolerance
    for floating-point representation differences.
    """
    try:
        a = float(actual)
        b = float(expected)

        return (
            math.isfinite(a)
            and math.isfinite(b)
            and math.isclose(
                a,
                b,
                rel_tol=0,
                abs_tol=1e-6,
            )
        )

    except (TypeError, ValueError, OverflowError):
        return False


def check_single_claim(
    claim: FactualClaim,
    analysis: dict,
    evidence: dict,
) -> str | None:
    """
    Verifies one structured claim.

    Returns a fact statement constructed by Python
    when the claim is supported.

    Returns None when unsupported.
    """

    if claim.evidence_id not in evidence:
        return None

    analysis_type = analysis["analysis_plan"]["analysis_type"]
    trace = analysis["calculation_trace"]

    # -----------------------------------------
    # 1. Grouped highest / lowest totals
    # -----------------------------------------

    if claim.kind == "group_extreme":

        expected_rank = {
            "groupby_aggregation_desc": "highest",
            "groupby_aggregation_asc": "lowest",
        }.get(analysis_type)

        if expected_rank is None:
            return None

        if claim.evidence_id != "E2":
            return None

        rows = evidence.get("E2", {}).get("rows", [])

        if not rows:
            return None

        top_row = rows[0]

        group_column = trace.get("group_by")
        metric_column = trace.get("metric")

        if not group_column or not metric_column:
            return None

        if (
            claim.metric != metric_column
            or claim.dimension != group_column
            or claim.member != str(top_row.get(group_column))
            or claim.rank != expected_rank
        ):
            return None

        expected_value = top_row.get(metric_column)

        if not numbers_match(claim.value, expected_value):
            return None

        return (
            f"{top_row[group_column]} has the "
            f"{expected_rank} total {metric_column} "
            f"among the analyzed groups: "
            f"{float(expected_value):g}."
        )

    # -----------------------------------------
    # 2. Monthly totals
    # -----------------------------------------

    if claim.kind == "monthly_total":

        if analysis_type != "time_trend":
            return None

        if claim.evidence_id != "E2":
            return None

        if (
            claim.metric != trace.get("metric")
            or claim.dimension != "period"
            or claim.rank is not None
            or claim.member is None
        ):
            return None

        rows = evidence.get("E2", {}).get("rows", [])

        matching_row = next(
            (
                row
                for row in rows
                if str(row.get("period")) == claim.member
            ),
            None,
        )

        if matching_row is None:
            return None

        expected_value = matching_row.get(claim.metric)

        if not numbers_match(claim.value, expected_value):
            return None

        return (
            f"Total {claim.metric} for {claim.member} "
            f"is {float(expected_value):g}."
        )

    # -----------------------------------------
    # 3. Pearson correlation
    # -----------------------------------------

    if claim.kind == "correlation":

        if analysis_type != "correlation":
            return None

        if claim.evidence_id != "E1":
            return None

        if (
            claim.metric != trace.get("y_metric")
            or claim.dimension != trace.get("x_metric")
            or claim.member is not None
            or claim.rank is not None
        ):
            return None

        expected_value = trace.get("correlation")

        if not numbers_match(claim.value, expected_value):
            return None

        rows_analyzed = trace.get("rows_analyzed")

        return (
            f"Pearson correlation between "
            f"{claim.dimension} and {claim.metric} "
            f"is {float(expected_value):g}, "
            f"based on {rows_analyzed} paired observations."
        )

    return None



def verify_factual_claims(
    analysis: dict,
    evidence: dict,
    claims: list[FactualClaim],
) -> dict:
    """
    Evaluates structured factual claims against
    previously verified calculation evidence.
    """

    evaluation = analysis.get("evaluation", {})

    if evaluation.get("status") != "passed":
        raise ValueError(
            "Calculation verification must pass "
            "before factual claims can be checked."
        )

    verified_facts = []
    rejected_claims = []

    for index, claim in enumerate(claims):

        verified_statement = check_single_claim(
            claim=claim,
            analysis=analysis,
            evidence=evidence,
        )

        if verified_statement is not None:
            verified_facts.append({
                "claim_index": index,
                "status": "supported",
                "statement": verified_statement,
                "evidence_id": claim.evidence_id,
            })

        else:
            rejected_claims.append({
                "claim_index": index,
                "status": "unsupported",
                "claim": claim.model_dump(),
                "reason": (
                    "The structured claim does not match "
                    "the verified calculation evidence."
                ),
            })

    passed = bool(verified_facts) and not rejected_claims

    return {
        "status": "passed" if passed else "failed",
        "verified_facts": verified_facts,
        "rejected_claims": rejected_claims,
        "narrative_status": "not_verified",
        "limitations": [
            "Only structured factual claims have been checked.",
            "The headline, observation and business implication "
            "have not yet passed free-text claim review.",
        ],
    }

