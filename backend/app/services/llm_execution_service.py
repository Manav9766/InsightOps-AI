
import pandas as pd

from app.services.file_service import get_dataset_file_path
from app.services.profiling_service import profile_dataset
from app.services.llm_planning_service import create_llm_analysis_plan
from app.services.chart_service import recommend_chart

from app.services.analysis_service import (
    run_groupby_analysis,
    run_trend_analysis,
    run_distribution_analysis,
    run_correlation_analysis,
    run_average_analysis,
    run_total_analysis,
    run_missing_value_analysis,
    run_general_summary,
)


def analyze_dataset_with_llm(
    dataset_id: str,
    question: str,
) -> dict:
    """
    Runs a validated LLM analysis plan using existing
    deterministic pandas analysis functions.
    """
    file_path = get_dataset_file_path(dataset_id)

    profile = profile_dataset(file_path)

    # Generate and validate the LLM plan first.
    plan = create_llm_analysis_plan(question, profile)

    analysis_type = plan["analysis_type"]
    metrics = plan["metric_columns"]

    df = pd.read_csv(file_path)

    # Execute only supported, predefined operations.
    if analysis_type in {
        "groupby_aggregation_desc",
        "groupby_aggregation_asc",
    }:
        direction = (
            "desc"
            if analysis_type == "groupby_aggregation_desc"
            else "asc"
        )

        result = run_groupby_analysis(
            df=df,
            question=question,
            sort_direction=direction,
            metric_column=metrics[0],
            group_column=plan["group_column"],
        )

    elif analysis_type == "time_trend":
        result = run_trend_analysis(
            df=df,
            question=question,
            profile=profile,
            date_column=plan["date_column"],
            metric_column=metrics[0],
        )

    elif analysis_type == "distribution":
        result = run_distribution_analysis(
            df=df,
            question=question,
            metric_column=metrics[0],
        )

    elif analysis_type == "correlation":
        result = run_correlation_analysis(
            df=df,
            question=question,
            x_column=metrics[0],
            y_column=metrics[1],
        )

    elif analysis_type == "average_metric":
        result = run_average_analysis(
            df=df,
            question=question,
            metric_column=metrics[0],
        )

    elif analysis_type == "total_metric":
        result = run_total_analysis(
            df=df,
            question=question,
            metric_column=metrics[0],
        )

    elif analysis_type == "missing_value_summary":
        result = run_missing_value_analysis(profile)

    elif analysis_type == "general_summary":
        result = run_general_summary(profile)

    else:
        raise ValueError(
            f"Unsupported analysis type: {analysis_type}"
        )

    # Reuse the chart recommendation layer from Phase 2.
    metadata = result.get("metadata", {})

    chart = recommend_chart(
        analysis_type=analysis_type,
        table=result["table"],
        group_column=metadata.get("group_column"),
        metric_column=metadata.get("metric_column"),
        date_column=metadata.get("date_column"),
        x_column=metadata.get("x_column"),
        y_column=metadata.get("y_column"),
    )

    return {
        "dataset_id": dataset_id,
        "question": question,
        "planner": "openai",
        "analysis_plan": plan,
        "answer": result["answer"],
        "table": result["table"],
        "chart": chart,
        "calculation_trace": result["calculation_trace"],
    }
