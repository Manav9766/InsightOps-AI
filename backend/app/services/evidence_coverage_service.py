from collections import Counter


REQUIRED_SECTIONS = {
    "headline",
    "observation",
    "business_implication",
}

VALID_VERDICTS = {
    "supported",
    "hypothesis",
    "unsupported",
}


def build_evidence_coverage(result: dict) -> dict:
    """
    Summarize how much verified evidence supports
    an AI-generated business insight.

    Uses existing calculation, claim verification,
    and narrative review results.

    Does not calculate a model confidence score.
    """

    evaluation = result.get(
        "calculation_evaluation"
    ) or {}

    claim_verification = result.get(
        "claim_verification"
    ) or {}

    narrative_review = result.get(
        "narrative_review"
    ) or {}

    draft = result.get("insight_draft") or {}
    evidence = result.get("evidence") or {}

    gaps = []

    # ------------------------------------
    # 1. Calculation verification
    # ------------------------------------

    calculation_passed = (
        evaluation.get("status") == "passed"
    )

    if not calculation_passed:
        gaps.append(
            "Independent calculation verification "
            "has not passed."
        )

    # ------------------------------------
    # 2. Structured factual claims
    # ------------------------------------

    factual_claims = draft.get(
        "factual_claims"
    ) or []

    verified_facts = claim_verification.get(
        "verified_facts"
    ) or []

    rejected_claims = claim_verification.get(
        "rejected_claims"
    ) or []

    total_claims = len(factual_claims)

    supported_indices = {
        fact["claim_index"]
        for fact in verified_facts
        if (
            isinstance(fact, dict)
            and type(fact.get("claim_index")) is int
            and fact.get("status") == "supported"
            and 0 <= fact["claim_index"] < total_claims
        )
    }

    supported_claims = len(supported_indices)
    rejected_count = len(rejected_claims)

    claims_complete = (
        total_claims > 0
        and claim_verification.get("status") == "passed"
        and supported_claims == total_claims
        and rejected_count == 0
    )

    if not claims_complete:
        gaps.append(
            "Not all structured factual claims "
            "have passed verification."
        )

    # ------------------------------------
    # 3. Narrative section coverage
    # ------------------------------------

    sections = narrative_review.get(
        "sections"
    ) or []

    valid_sections = [
        section
        for section in sections
        if (
            isinstance(section, dict)
            and section.get("section")
            in REQUIRED_SECTIONS
        )
    ]

    section_names = [
        section["section"]
        for section in valid_sections
    ]

    verdict_counts = Counter(
        section.get("verdict")
        for section in valid_sections
        if section.get("verdict")
        in VALID_VERDICTS
    )

    supported_sections = verdict_counts["supported"]
    hypothesis_sections = verdict_counts["hypothesis"]
    unsupported_sections = verdict_counts["unsupported"]

    reviewed_sections = (
        supported_sections
        + hypothesis_sections
        + unsupported_sections
    )

    review_complete = (
        len(sections) == len(REQUIRED_SECTIONS)
        and set(section_names) == REQUIRED_SECTIONS
        and len(set(section_names)) == len(section_names)
        and reviewed_sections == len(REQUIRED_SECTIONS)
        and narrative_review.get("status")
        in {"supported", "qualified", "flagged"}
    )

    if not review_complete:
        gaps.append(
            "Narrative review is missing "
            "or incomplete."
        )

    if unsupported_sections:
        gaps.append(
            f"{unsupported_sections} narrative section(s) "
            "were classified as unsupported."
        )

    if hypothesis_sections:
        gaps.append(
            f"{hypothesis_sections} narrative section(s) "
            "contain hypotheses rather than "
            "directly supported conclusions."
        )

    # ------------------------------------
    # 4. Supporting table coverage
    # ------------------------------------

    table_coverage = None
    table_invalid = False
    table_truncated = False

    supporting_table = evidence.get("E2")

    if supporting_table is not None:
        total_rows = supporting_table.get(
            "rows_in_result"
        )

        included_rows = supporting_table.get(
            "rows_included"
        )

        valid_counts = (
            type(total_rows) is int
            and type(included_rows) is int
            and total_rows >= 0
            and 0 <= included_rows <= total_rows
        )

        if not valid_counts:
            table_invalid = True

            gaps.append(
                "Supporting table row coverage "
                "could not be established."
            )

        else:
            table_truncated = (
                included_rows < total_rows
            )

            table_coverage = {
                "included_rows": included_rows,
                "total_rows": total_rows,
                "truncated": table_truncated,
            }

            if table_truncated:
                gaps.append(
                    f"Only {included_rows} of "
                    f"{total_rows} supporting table "
                    "rows were included in the "
                    "AI evidence packet."
                )

    # ------------------------------------
    # 5. Determine overall coverage
    # ------------------------------------

    has_insufficient_coverage = (
        not calculation_passed
        or not claims_complete
        or not review_complete
        or unsupported_sections > 0
        or table_invalid
    )

    if has_insufficient_coverage:
        status = "insufficient"

    elif hypothesis_sections > 0 or table_truncated:
        status = "qualified"

    else:
        status = "direct_support"

    # ------------------------------------
    # 6. Return transparent indicators
    # ------------------------------------

    return {
        "status": status,
        "calculation_verified": calculation_passed,
        "structured_claims": {
            "total": total_claims,
            "supported": supported_claims,
            "rejected": rejected_count,
        },
        "narrative_sections": {
            "total": len(REQUIRED_SECTIONS),
            "reviewed": reviewed_sections,
            "supported": supported_sections,
            "hypothesis": hypothesis_sections,
            "unsupported": unsupported_sections,
        },
        "supporting_table": table_coverage,
        "available_evidence_ids": sorted(
            evidence.keys()
        ),
        "gaps": gaps,
        "limitations": [
            (
                "Evidence coverage counts are not "
                "statistical confidence scores."
            ),
            (
                "Narrative support classifications "
                "are AI-assisted assessments, "
                "not mathematical proof."
            ),
            (
                "Evidence coverage does not establish "
                "that the underlying dataset is "
                "representative or complete."
            ),
        ],
    }