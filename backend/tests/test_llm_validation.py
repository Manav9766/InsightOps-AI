
import pytest

from app.models.analysis_plan import LLMAnalysisPlan
from app.services.llm_planning_service import validate_analysis_plan


@pytest.fixture
def profile():
    return {
        "identifier_columns": ["order_id"],
        "metric_columns": ["quantity", "revenue", "discount"],
        "categorical_columns": [
            "region",
            "product_category",
            "customer_segment",
        ],
        "date_like_columns": ["order_date"],
    }


def make_plan(**changes):
    data = {
        "analysis_type": "groupby_aggregation_desc",
        "metric_columns": ["revenue"],
        "group_column": "region",
        "date_column": None,
        "steps": ["Group by region", "Sum revenue"],
        "supported": True,
        "explanation": "Compare total revenue by region.",
    }

    data.update(changes)
    return LLMAnalysisPlan(**data)


def test_valid_groupby_plan(profile):
    validate_analysis_plan(make_plan(), profile)


@pytest.mark.parametrize(
    "changes",
    [
        {"metric_columns": ["invented_profit"]},
        {"metric_columns": ["order_id"]},
        {"group_column": "invented_region"},
        {"group_column": None},
        {"metric_columns": ["revenue", "quantity"]},
        {"date_column": "order_date"},
    ],
)
def test_invalid_groupby_plan(profile, changes):
    with pytest.raises(ValueError):
        validate_analysis_plan(make_plan(**changes), profile)


def test_valid_trend_plan(profile):
    plan = make_plan(
        analysis_type="time_trend",
        group_column=None,
        date_column="order_date",
    )

    validate_analysis_plan(plan, profile)


def test_trend_without_date_is_rejected(profile):
    plan = make_plan(
        analysis_type="time_trend",
        group_column=None,
        date_column=None,
    )

    with pytest.raises(ValueError, match="date column"):
        validate_analysis_plan(plan, profile)


def test_valid_correlation_plan(profile):
    plan = make_plan(
        analysis_type="correlation",
        metric_columns=["quantity", "revenue"],
        group_column=None,
    )

    validate_analysis_plan(plan, profile)


def test_correlation_with_one_metric_is_rejected(profile):
    plan = make_plan(
        analysis_type="correlation",
        metric_columns=["quantity"],
        group_column=None,
    )

    with pytest.raises(ValueError, match="two distinct"):
        validate_analysis_plan(plan, profile)


def test_duplicate_correlation_metrics_are_rejected(profile):
    plan = make_plan(
        analysis_type="correlation",
        metric_columns=["revenue", "revenue"],
        group_column=None,
    )

    with pytest.raises(ValueError):
        validate_analysis_plan(plan, profile)


def test_unsupported_question_is_rejected(profile):
    plan = make_plan(
        analysis_type="unsupported",
        metric_columns=[],
        group_column=None,
        supported=False,
    )

    with pytest.raises(ValueError, match="Unsupported"):
        validate_analysis_plan(plan, profile)


def test_summary_with_unnecessary_metric_is_rejected(profile):
    plan = make_plan(
        analysis_type="general_summary",
        group_column=None,
    )

    with pytest.raises(ValueError):
        validate_analysis_plan(plan, profile)
