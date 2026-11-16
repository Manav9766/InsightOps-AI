
import copy

import pandas as pd

from app.services.evaluation_service import verify_calculation


def make_grouped_result():
    df = pd.DataFrame({
        "region": ["North", "West", "North"],
        "revenue": [49.0, 25.5, 61.25],
    })

    result = {
        "table": [
            {"region": "North", "revenue": 110.25},
            {"region": "West", "revenue": 25.5},
        ],
        "calculation_trace": {
            "operation": "groupby_sum",
            "group_by": "region",
            "metric": "revenue",
            "sort_direction": "desc",
            "rows_returned": 2,
        },
    }

    chart = {
        "type": "bar",
        "x_key": "region",
        "y_key": "revenue",
        "data": copy.deepcopy(result["table"]),
    }

    return df, result, chart


def test_correct_calculation_passes():
    df, result, chart = make_grouped_result()

    evaluation = verify_calculation(
        df, "groupby_aggregation_desc", result, chart
    )

    assert evaluation["status"] == "passed"
    assert all(evaluation["checks"].values())


def test_incorrect_revenue_fails():
    df, result, chart = make_grouped_result()
    result["table"][0]["revenue"] = 999.0

    evaluation = verify_calculation(
        df, "groupby_aggregation_desc", result, chart
    )

    assert evaluation["status"] == "failed"
    assert not evaluation["checks"]["table_matches_source_data"]


def test_incorrect_chart_fails():
    df, result, chart = make_grouped_result()
    chart["data"] = []

    evaluation = verify_calculation(
        df, "groupby_aggregation_desc", result, chart
    )

    assert evaluation["status"] == "failed"
    assert not evaluation["checks"]["chart_matches_table"]


def test_incorrect_trace_fails():
    df, result, chart = make_grouped_result()
    result["calculation_trace"]["rows_returned"] = 99

    evaluation = verify_calculation(
        df, "groupby_aggregation_desc", result, chart
    )

    assert evaluation["status"] == "failed"
    assert not evaluation["checks"][
        "calculation_trace_matches_source_data"
    ]


def test_unsupported_verification_is_not_evaluated():
    df, result, chart = make_grouped_result()

    evaluation = verify_calculation(
        df, "distribution", result, chart
    )

    assert evaluation["status"] == "not_evaluated"
