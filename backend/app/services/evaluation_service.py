import math

import pandas as pd


def values_match(actual, expected) -> bool:
    """
    Compares calculated values with values returned
    by the analysis engine.
    """
    if pd.isna(expected):
        return actual is None or pd.isna(actual)

    if isinstance(expected, (int, float)) and not isinstance(
        expected, bool
    ):
        try:
            return math.isclose(
                float(actual),
                round(float(expected), 2),
                rel_tol=1e-9,
                abs_tol=1e-9,
            )
        except (TypeError, ValueError):
            return False

    return actual == expected


def tables_match(
    actual: list[dict],
    expected: list[dict],
    columns: list[str],
) -> bool:
    """
    Compares actual and independently recomputed rows.
    """
    if len(actual) != len(expected):
        return False

    return all(
        all(
            values_match(row.get(column), source_row.get(column))
            for column in columns
        )
        for row, source_row in zip(actual, expected)
    )


def verify_calculation(
    df: pd.DataFrame,
    analysis_type: str,
    result: dict,
    chart: dict | None,
) -> dict:
    """
    Independently verifies supported calculations.

    Current scope:
    - Grouped sum comparisons
    - Monthly time trends
    - Pearson correlations

    Does not verify natural-language conclusions.
    """
    supported = {
        "groupby_aggregation_desc",
        "groupby_aggregation_asc",
        "time_trend",
        "correlation",
    }

    if analysis_type not in supported:
        return {
            "status": "not_evaluated",
            "checks": {},
            "limitations": [
                "Independent verification is not yet implemented "
                "for this analysis operation."
            ],
        }

    table = result["table"]
    trace = result["calculation_trace"]

    expected_chart_type = None
    expected_x = None
    expected_y = None
    table_valid = False
    trace_valid = False

    if analysis_type in {
        "groupby_aggregation_desc",
        "groupby_aggregation_asc",
    }:
        group = trace["group_by"]
        metric = trace["metric"]

        ascending = analysis_type == "groupby_aggregation_asc"
        expected_direction = "asc" if ascending else "desc"

        expected = (
            df.groupby(group, dropna=False)[metric]
            .sum()
            .reset_index()
            .sort_values(by=metric, ascending=ascending)
            .head(5)
            .to_dict(orient="records")
        )

        table_valid = tables_match(
            table, expected, [group, metric]
        )

        trace_valid = (
            trace.get("operation") == "groupby_sum"
            and trace.get("sort_direction") == expected_direction
            and trace.get("rows_returned") == len(expected)
        )

        expected_chart_type = "bar"
        expected_x = group
        expected_y = metric

    elif analysis_type == "time_trend":
        date_column = trace["date_column"]
        metric = trace["metric"]

        working_df = df.copy()
        working_df[date_column] = pd.to_datetime(
            working_df[date_column],
            errors="coerce",
        )

        working_df = working_df.dropna(subset=[date_column])

        working_df["period"] = (
            working_df[date_column]
            .dt.to_period("M")
            .astype(str)
        )

        expected = (
            working_df.groupby("period")[metric]
            .sum()
            .reset_index()
            .sort_values("period")
            .to_dict(orient="records")
        )

        table_valid = tables_match(
            table, expected, ["period", metric]
        )

        trace_valid = (
            trace.get("operation") == "monthly_trend"
            and trace.get("periods_returned") == len(expected)
        )

        expected_chart_type = "line"
        expected_x = "period"
        expected_y = metric

    elif analysis_type == "correlation":
        x = trace["x_metric"]
        y = trace["y_metric"]

        working_df = df[[x, y]].dropna()

        expected = working_df.to_dict(orient="records")

        actual_correlation = working_df[x].corr(
            working_df[y]
        )

        correlation_valid = (
            pd.notna(actual_correlation)
            and math.isclose(
                float(trace["correlation"]),
                round(float(actual_correlation), 3),
                abs_tol=1e-9,
            )
        )

        table_valid = tables_match(
            table, expected, [x, y]
        )

        trace_valid = (
            trace.get("operation") == "correlation"
            and trace.get("rows_analyzed") == len(expected)
            and correlation_valid
        )

        expected_chart_type = "scatter"
        expected_x = x
        expected_y = y

    chart_valid = (
        isinstance(chart, dict)
        and chart.get("type") == expected_chart_type
        and chart.get("x_key") == expected_x
        and chart.get("y_key") == expected_y
        and chart.get("data") == table
    )

    checks = {
        "table_matches_source_data": table_valid,
        "calculation_trace_matches_source_data": trace_valid,
        "chart_matches_table": chart_valid,
    }

    return {
        "status": (
            "passed" if all(checks.values()) else "failed"
        ),
        "checks": checks,
        "limitations": [
            "This verifies structured calculations and chart data, "
            "not the accuracy of free-text explanations, "
            "causal claims, or LLM planning intent."
        ],
    }
