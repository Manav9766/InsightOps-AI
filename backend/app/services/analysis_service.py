import pandas as pd
import numpy as np

from app.services.chart_service import recommend_chart
from app.services.file_service import get_dataset_file_path
from app.services.profiling_service import profile_dataset
from app.services.planning_service import create_analysis_plan


def is_identifier_column(column_name: str) -> bool:
    """
    Detects columns that are probably IDs, not useful numeric metrics.
    """
    lowered = column_name.lower()
    return lowered == "id" or lowered.endswith("_id") or "id" in lowered

def format_number(value: float) -> int | float:
    """
    Formats numbers for cleaner display.
    Converts 25.0 to 25, keeps 24.47 as 24.47.
    """
    rounded = round(float(value), 2)

    if rounded.is_integer():
        return int(rounded)

    return rounded
def make_json_safe(value):
    """
    Converts pandas/numpy values into JSON-safe Python values.
    Rounds floating-point values for cleaner API output.
    """
    if pd.isna(value):
        return None

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating, float)):
        return round(float(value), 2)

    if isinstance(value, (np.bool_,)):
        return bool(value)

    return value

def records_to_json_safe(records: list[dict]) -> list[dict]:
    """
    Converts list of pandas records into JSON-safe records.
    """
    safe_records = []

    for record in records:
        safe_record = {
            key: make_json_safe(value)
            for key, value in record.items()
        }
        safe_records.append(safe_record)

    return safe_records


def infer_metric_column(df: pd.DataFrame, question: str) -> str | None:
    """
    Infers the best numeric column to use as the metric.
    Excludes identifier columns like order_id.
    """
    question_lower = question.lower()

    numeric_columns = [
        column
        for column in df.select_dtypes(include=["number"]).columns.tolist()
        if not is_identifier_column(column)
    ]

    if not numeric_columns:
        return None

    # First priority: exact column name mentioned in question.
    for column in numeric_columns:
        if column.lower() in question_lower:
            return column

    # Second priority: common business metric keywords.
    metric_keywords = {
        "revenue": ["revenue", "sales", "income", "amount"],
        "quantity": ["quantity", "units", "volume", "orders"],
        "discount": ["discount"],
        "profit": ["profit", "margin"],
        "price": ["price", "cost"],
    }

    for column in numeric_columns:
        column_lower = column.lower()

        for canonical_metric, keywords in metric_keywords.items():
            if column_lower == canonical_metric or canonical_metric in column_lower:
                for keyword in keywords:
                    if keyword in question_lower:
                        return column

    # Fallback: use first non-ID numeric column.
    return numeric_columns[0]

def infer_group_column(df: pd.DataFrame, question: str) -> str | None:
    """
    Infers the best categorical/date column to group by.
    """
    question_lower = question.lower()

    candidate_columns = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if not candidate_columns:
        return None

    # Exact column name mentioned in question.
    for column in candidate_columns:
        if column.lower() in question_lower:
            return column

    # Handle human-friendly words.
    group_keywords = {
        "region": ["region", "area", "location"],
        "product_category": ["product", "category", "item"],
        "customer_segment": ["customer", "segment"],
        "order_date": ["date", "month", "day", "time"],
    }

    for column in candidate_columns:
        column_lower = column.lower()

        for canonical_name, keywords in group_keywords.items():
            if column_lower == canonical_name or canonical_name in column_lower:
                for keyword in keywords:
                    if keyword in question_lower:
                        return column

    # Fallback: use first categorical column.
    return candidate_columns[0]


def run_groupby_analysis(
    df: pd.DataFrame,
    question: str,
    sort_direction: str
) -> dict:
    """
    Runs groupby aggregation for highest/top/best or lowest/worst/least questions.
    """
    metric_column = infer_metric_column(df, question)
    group_column = infer_group_column(df, question)

    if metric_column is None:
        raise ValueError("No valid numeric metric column found for this question.")

    if group_column is None:
        raise ValueError("No valid categorical grouping column found for this question.")

    ascending = sort_direction == "asc"

    result_df = (
        df.groupby(group_column, dropna=False)[metric_column]
        .sum()
        .reset_index()
        .sort_values(by=metric_column, ascending=ascending)
    )

    top_rows = result_df.head(5)
    records = records_to_json_safe(top_rows.to_dict(orient="records"))

    top_result = records[0]
    top_group_value = top_result[group_column]
    top_metric_value = format_number(top_result[metric_column])

    if ascending:
        answer = (
            f"{top_group_value} has the lowest total {metric_column} "
            f"with {top_metric_value}."
        )
    else:
        answer = (
            f"{top_group_value} has the highest total {metric_column} "
            f"with {top_metric_value}."
        )

    return {
        "answer": answer,
        "table": records,
        "metadata": {
            "group_column": group_column,
            "metric_column": metric_column,
        },
        "calculation_trace": {
            "operation": "groupby_sum",
            "group_by": group_column,
            "metric": metric_column,
            "sort_direction": sort_direction,
            "rows_returned": len(records),
        },
    }


def run_average_analysis(df: pd.DataFrame, question: str) -> dict:
    """
    Calculates the average of a numeric metric.
    """
    metric_column = infer_metric_column(df, question)

    if metric_column is None:
        raise ValueError("No valid numeric metric column found for this question.")

    average_value = format_number(df[metric_column].mean())

    return {
        "answer": f"The average {metric_column} is {average_value}.",
        "table": [
            {
                "metric": metric_column,
                "average": average_value,
            }
        ],
        "calculation_trace": {
            "operation": "mean",
            "metric": metric_column,
        }
    }


def run_total_analysis(df: pd.DataFrame, question: str) -> dict:
    """
    Calculates the total of a numeric metric.
    """
    metric_column = infer_metric_column(df, question)

    if metric_column is None:
        raise ValueError("No valid numeric metric column found for this question.")

    total_value = format_number(df[metric_column].sum())

    return {
        "answer": f"The total {metric_column} is {total_value}.",
        "table": [
            {
                "metric": metric_column,
                "total": total_value,
            }
        ],
        "calculation_trace": {
            "operation": "sum",
            "metric": metric_column,
        }
    }


def run_missing_value_analysis(profile: dict) -> dict:
    """
    Returns missing value summary from the dataset profile.
    """
    missing_values = profile.get("missing_values", {})
    missing_percentages = profile.get("missing_percentages", {})

    rows = []

    for column, missing_count in missing_values.items():
        rows.append({
            "column": column,
            "missing_count": missing_count,
            "missing_percentage": missing_percentages.get(column, 0),
        })

    rows = sorted(rows, key=lambda item: item["missing_count"], reverse=True)

    total_missing = sum(missing_values.values())

    return {
        "answer": f"The dataset contains {total_missing} missing values in total.",
        "table": rows,
        "calculation_trace": {
            "operation": "missing_value_summary",
            "columns_checked": len(rows),
        }
    }


def run_general_summary(profile: dict) -> dict:
    """
    Returns a basic dataset overview.
    """
    rows = profile.get("rows", 0)
    columns = profile.get("columns", 0)
    numeric_columns = profile.get("numeric_columns", [])
    identifier_columns = profile.get("identifier_columns", [])
    metric_columns = profile.get("metric_columns", [])
    categorical_columns = profile.get("categorical_columns", [])
    date_like_columns = profile.get("date_like_columns", [])

    return {
        "answer": (
            f"This dataset has {rows} rows and {columns} columns. "
            f"It contains {len(metric_columns)} metric columns, "
            f"{len(identifier_columns)} identifier columns, "
            f"{len(categorical_columns)} categorical columns, and "
            f"{len(date_like_columns)} date-like columns."
        ),
        "table": [
            {
                "rows": rows,
                "columns": columns,
                "numeric_columns": numeric_columns,
                "identifier_columns": identifier_columns,
                "metric_columns": metric_columns,
                "categorical_columns": categorical_columns,
                "date_like_columns": date_like_columns,
            }
        ],
        "calculation_trace": {
            "operation": "dataset_summary",
        }
    }


def answer_dataset_question(dataset_id: str, question: str) -> dict:
    """
    Main Phase 1 analysis function.

    Loads dataset, creates analysis plan, runs pandas calculation,
    and returns a grounded answer.
    """
    file_path = get_dataset_file_path(dataset_id)
    df = pd.read_csv(file_path)
    profile = profile_dataset(file_path)

    analysis_plan = create_analysis_plan(question, profile)
    analysis_type = analysis_plan["analysis_type"]

    if analysis_type == "groupby_aggregation_desc":
        result = run_groupby_analysis(df, question, sort_direction="desc")

    elif analysis_type == "groupby_aggregation_asc":
        result = run_groupby_analysis(df, question, sort_direction="asc")

    elif analysis_type == "average_metric":
        result = run_average_analysis(df, question)

    elif analysis_type == "total_metric":
        result = run_total_analysis(df, question)

    elif analysis_type == "missing_value_summary":
        result = run_missing_value_analysis(profile)

    elif analysis_type == "time_trend":
        result = run_trend_analysis(
            df=df,
            question=question,
            profile=profile,
        )

    elif analysis_type == "distribution":
        result = run_distribution_analysis(df, question)

    else:
        result = run_general_summary(profile)

    metadata = result.get("metadata", {})
    chart = recommend_chart(
        analysis_type=analysis_type,
        table=result["table"],
        group_column=metadata.get("group_column"),
        metric_column=metadata.get("metric_column"),
        date_column=metadata.get("date_column"),
    )

    return {
        "dataset_id": dataset_id,
        "question": question,
        "analysis_plan": analysis_plan,
        "answer": result["answer"],
        "table": result["table"],
        "chart": chart,
        "calculation_trace": result["calculation_trace"],
    }



def run_trend_analysis(
    df: pd.DataFrame,
    question: str,
    profile: dict,
) -> dict:
    """
    Runs a time-based trend analysis using a detected date column.
    """
    date_columns = profile.get("date_like_columns", [])

    if not date_columns:
        raise ValueError("No date-like column found for trend analysis.")

    date_column = date_columns[0]
    metric_column = infer_metric_column(df, question)

    if metric_column is None:
        raise ValueError("No valid numeric metric column found for trend analysis.")

    working_df = df.copy()

    working_df[date_column] = pd.to_datetime(
        working_df[date_column],
        errors="coerce",
    )

    working_df = working_df.dropna(subset=[date_column])

    working_df["period"] = working_df[date_column].dt.to_period("M").astype(str)

    result_df = (
        working_df.groupby("period")[metric_column]
        .sum()
        .reset_index()
        .sort_values("period")
    )

    records = records_to_json_safe(
        result_df.to_dict(orient="records")
    )

    return {
        "answer": (
            f"Calculated the monthly {metric_column} trend "
            f"across {len(records)} periods."
        ),
        "table": records,
        "metadata": {
            "metric_column": metric_column,
            "date_column": date_column,
        },
        "calculation_trace": {
            "operation": "monthly_trend",
            "date_column": date_column,
            "metric": metric_column,
            "periods_returned": len(records),
        },
    }
def run_distribution_analysis(
    df: pd.DataFrame,
    question: str,
) -> dict:
    """
    Creates a histogram-style distribution analysis
    for a numeric metric column.
    """
    metric_column = infer_metric_column(df, question)

    if metric_column is None:
        raise ValueError(
            "No valid numeric metric column found for distribution analysis."
        )

    series = df[metric_column].dropna()

    if series.empty:
        raise ValueError(
            f"No valid values found in metric column: {metric_column}"
        )

    counts, bin_edges = np.histogram(series, bins="auto")

    records = []

    for index, count in enumerate(counts):
        bin_start = round(float(bin_edges[index]), 2)
        bin_end = round(float(bin_edges[index + 1]), 2)

        records.append({
            "range": f"{bin_start} - {bin_end}",
            "count": int(count),
        })

    return {
        "answer": (
            f"Calculated the distribution of {metric_column} "
            f"across {len(records)} value ranges."
        ),
        "table": records,
        "metadata": {
            "metric_column": metric_column,
        },
        "calculation_trace": {
            "operation": "histogram",
            "metric": metric_column,
            "bins": len(records),
            "values_analyzed": int(series.count()),
        },
    }
