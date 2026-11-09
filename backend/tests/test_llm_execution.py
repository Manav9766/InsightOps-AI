
import pytest

from app.services import llm_execution_service as execution


@pytest.fixture
def sample_csv(tmp_path):
    """
    Creates a temporary CSV for testing.
    Does not modify actual uploaded datasets.
    """
    csv_content = """order_id,order_date,region,product_category,customer_segment,quantity,revenue,discount
1,2026-01-05,East,Burgers,Student,2,24.50,0
2,2026-01-06,West,Drinks,Worker,1,5.99,0
3,2026-01-07,East,Sides,Student,3,12.75,0.1
4,2026-02-01,North,Burgers,Family,4,49.00,0.05
5,2026-02-03,West,Burgers,Worker,2,25.50,0
6,2026-02-04,South,Drinks,Student,2,11.98,0
7,2026-03-01,East,Sides,Family,1,4.25,0
8,2026-03-04,North,Burgers,Worker,5,61.25,0.15
9,2026-03-07,South,Drinks,Student,2,11.98,0
10,2026-03-09,West,Burgers,Family,3,37.50,0.05
"""

    file_path = tmp_path / "sample_sales.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    return file_path


@pytest.mark.parametrize(
    "analysis_type,metrics,group,date,chart_type,operation",
    [
        (
            "groupby_aggregation_desc",
            ["revenue"],
            "region",
            None,
            "bar",
            "groupby_sum",
        ),
        (
            "time_trend",
            ["revenue"],
            None,
            "order_date",
            "line",
            "monthly_trend",
        ),
        (
            "correlation",
            ["quantity", "revenue"],
            None,
            None,
            "scatter",
            "correlation",
        ),
    ],
)
def test_llm_plan_executes_with_pandas(
    monkeypatch,
    sample_csv,
    analysis_type,
    metrics,
    group,
    date,
    chart_type,
    operation,
):
    """
    Tests pandas execution with a predefined LLM plan.
    No OpenAI request is made.
    """

    fake_plan = {
        "analysis_type": analysis_type,
        "metric_columns": metrics,
        "group_column": group,
        "date_column": date,
        "steps": ["Execute selected calculation"],
        "supported": True,
        "explanation": "Valid test analysis plan.",
    }

    monkeypatch.setattr(
        execution,
        "get_dataset_file_path",
        lambda dataset_id: str(sample_csv),
    )

    monkeypatch.setattr(
        execution,
        "create_llm_analysis_plan",
        lambda question, profile: fake_plan,
    )

    result = execution.analyze_dataset_with_llm(
        dataset_id="test-dataset",
        question="Test question",
    )

    assert result["planner"] == "openai"
    assert result["analysis_plan"]["analysis_type"] == analysis_type
    assert result["chart"]["type"] == chart_type
    assert result["calculation_trace"]["operation"] == operation
    assert len(result["table"]) > 0

    if analysis_type == "groupby_aggregation_desc":
        assert result["table"][0]["region"] == "North"
        assert result["table"][0]["revenue"] == pytest.approx(110.25)

    elif analysis_type == "time_trend":
        assert result["table"] == [
            {"period": "2026-01", "revenue": 43.24},
            {"period": "2026-02", "revenue": 86.48},
            {"period": "2026-03", "revenue": 114.98},
        ]

    elif analysis_type == "correlation":
        coefficient = result["calculation_trace"]["correlation"]
        assert coefficient == pytest.approx(0.908, abs=0.001)
        assert result["calculation_trace"]["rows_analyzed"] == 10
