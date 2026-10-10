def create_analysis_plan(question: str, profile: dict) -> dict:
    """
    Creates a simple rule-based analysis plan for Phase 1.

    Later, this will be replaced or upgraded with an LLM/LangGraph planner.
    """
    question_lower = question.lower()

    numeric_columns = profile.get("numeric_columns", [])
    metric_columns = profile.get("metric_columns", numeric_columns)
    categorical_columns = profile.get("categorical_columns", [])
    date_like_columns = profile.get("date_like_columns", [])

    base_columns = {
        "available_numeric_columns": numeric_columns,
        "available_metric_columns": metric_columns,
        "available_categorical_columns": categorical_columns,
        "available_date_columns": date_like_columns,
    }

    if "missing" in question_lower or "null" in question_lower:
        return {
            "analysis_type": "missing_value_summary",
            "steps": [
                "Inspect all columns in the dataset",
                "Count missing values for each column",
                "Calculate missing value percentages",
                "Return a data quality summary"
            ],
            "requires_grouping": False,
            "requires_metric": False,
            "available_numeric_columns": numeric_columns,
            "available_metric_columns": metric_columns,
            "available_categorical_columns": categorical_columns,
            "available_date_columns": date_like_columns,
        }

    if any(
        word in question_lower
        for word in ["trend", "over time", "monthly", "month", "timeline"]
    ):
        return {
            "analysis_type": "time_trend",
            "steps": [
                "Identify the date column",
                "Identify the numeric metric",
                "Convert the date column to datetime",
                "Aggregate the metric by month",
                "Sort the periods chronologically",
                "Return the trend table and visualization",
            ],
            "requires_grouping": True,
            "requires_metric": True,
            "available_numeric_columns": numeric_columns,
            "available_metric_columns": metric_columns,
            "available_categorical_columns": categorical_columns,
            "available_date_columns": date_like_columns,
        }

    if any(word in question_lower for word in ["highest", "top", "best", "most"]):
        return {
            "analysis_type": "groupby_aggregation_desc",
            "steps": [
                "Identify the metric column from the question",
                "Identify the grouping column from the question",
                "Group the dataset by the selected category",
                "Calculate the total value for the selected metric",
                "Sort the results from highest to lowest",
                "Return the top result and supporting table"
            ],
            "requires_grouping": True,
            "requires_metric": True,
            "available_numeric_columns": numeric_columns,
            "available_metric_columns": metric_columns,
            "available_categorical_columns": categorical_columns,
            "available_date_columns": date_like_columns,
        }

    if any(word in question_lower for word in ["lowest", "worst", "least"]):
        return {
            "analysis_type": "groupby_aggregation_asc",
            "steps": [
                "Identify the metric column from the question",
                "Identify the grouping column from the question",
                "Group the dataset by the selected category",
                "Calculate the total value for the selected metric",
                "Sort the results from lowest to highest",
                "Return the lowest result and supporting table"
            ],
            "requires_grouping": True,
            "requires_metric": True,
            "available_numeric_columns": numeric_columns,
            "available_metric_columns": metric_columns,
            "available_categorical_columns": categorical_columns,
            "available_date_columns": date_like_columns,
        }

    if any(
        phrase in question_lower
        for phrase in [
            "distribution",
            "histogram",
            "spread",
            "frequency",
            "range of",
        ]
    ):
        return {
            "analysis_type": "distribution",
            "steps": [
                "Identify the numeric metric column",
                "Remove missing values",
                "Calculate histogram bins",
                "Count values inside each range",
                "Return the distribution table and histogram",
            ],
            "requires_grouping": False,
            "requires_metric": True,
            **base_columns,
        }

    if any(word in question_lower for word in ["average", "avg", "mean"]):
        return {
            "analysis_type": "average_metric",
            "steps": [
                "Identify the numeric metric column from the question",
                "Calculate the average value",
                "Return the computed average"
            ],
            "requires_grouping": False,
            "requires_metric": True,
            "available_numeric_columns": numeric_columns,
            "available_metric_columns": metric_columns,
            "available_categorical_columns": categorical_columns,
            "available_date_columns": date_like_columns,
        }

    if any(word in question_lower for word in ["total", "sum"]):
        return {
            "analysis_type": "total_metric",
            "steps": [
                "Identify the numeric metric column from the question",
                "Calculate the total value",
                "Return the computed total"
            ],
            "requires_grouping": False,
            "requires_metric": True,
            "available_numeric_columns": numeric_columns,
            "available_metric_columns": metric_columns,
            "available_categorical_columns": categorical_columns,
            "available_date_columns": date_like_columns,
        }

    return {
        "analysis_type": "general_summary",
        "steps": [
            "Summarize dataset structure",
            "Review numeric and categorical columns",
            "Return a basic dataset overview"
        ],
        "requires_grouping": False,
        "requires_metric": False,
        "available_numeric_columns": numeric_columns,
        "available_metric_columns": metric_columns,
        "available_categorical_columns": categorical_columns,
        "available_date_columns": date_like_columns,
    }
