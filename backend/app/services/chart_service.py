def recommend_chart(
    analysis_type: str,
    table: list[dict],
    group_column: str | None = None,
    metric_column: str | None = None,
    date_column: str | None = None,
) -> dict | None:
    """Recommend a chart configuration based on the analysis result."""
    if not table:
        return None

    if analysis_type in {
        "groupby_aggregation_desc",
        "groupby_aggregation_asc",
    }:
        if not group_column or not metric_column:
            return None

        return {
            "type": "bar",
            "title": f"Total {metric_column} by {group_column}",
            "x_key": group_column,
            "y_key": metric_column,
            "data": table,
        }

    if analysis_type == "time_trend":
        if not metric_column:
            return None

        return {
            "type": "line",
            "title": f"{metric_column} trend over time",
            "x_key": "period",
            "y_key": metric_column,
            "data": table,
        }

    if analysis_type == "distribution":
        return {
            "type": "histogram",
            "title": f"Distribution of {metric_column}",
            "x_key": "range",
            "y_key": "count",
            "data": table,
        }

    return None
