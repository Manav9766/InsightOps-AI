import pandas as pd


def is_identifier_column(column_name: str, series: pd.Series) -> bool:
    """
    Detects columns that are likely identifiers, not analytical metrics.
    Examples: order_id, customer_id, transaction_id.
    """
    column_lower = column_name.lower()

    if column_lower == "id" or column_lower.endswith("_id") or column_lower.endswith("id"):
        return True

    uniqueness_ratio = series.nunique(dropna=True) / max(len(series), 1)

    if "id" in column_lower and uniqueness_ratio > 0.8:
        return True

    return False


def detect_date_like_columns(df: pd.DataFrame) -> list[str]:
    """
    Detects columns that are likely dates.

    Important:
    Numeric columns should not be treated as dates, because pandas can
    incorrectly parse numbers as timestamps.
    """
    date_like_columns = []

    for column in df.columns:
        column_lower = column.lower()

        has_date_name = any(
            keyword in column_lower
            for keyword in ["date", "time", "created_at", "updated_at", "timestamp"]
        )

        # Strong rule:
        # In Phase 1, only try date parsing if the column name suggests date/time
        # OR the dtype is already datetime.
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            date_like_columns.append(column)
            continue

        if not has_date_name:
            continue

        # Do not parse pure numeric columns as dates.
        if pd.api.types.is_numeric_dtype(df[column]):
            continue

        sample = df[column].dropna().astype(str).head(50)

        if sample.empty:
            continue

        try:
            parsed = pd.to_datetime(sample, errors="coerce")
            valid_ratio = parsed.notna().mean()

            if valid_ratio >= 0.7:
                date_like_columns.append(column)

        except Exception:
            continue

    return date_like_columns


def profile_dataset(file_path: str) -> dict:
    """
    Reads a CSV file and returns a dataset profile.
    """
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {str(e)}")

    rows, columns = df.shape

    data_types = {
        column: str(dtype)
        for column, dtype in df.dtypes.items()
    }

    missing_values = {
        column: int(count)
        for column, count in df.isnull().sum().items()
    }

    missing_percentages = {
        column: round(float(df[column].isnull().mean() * 100), 2)
        for column in df.columns
    }

    duplicate_rows = int(df.duplicated().sum())

    date_like_columns = detect_date_like_columns(df)

    identifier_columns = [
        column
        for column in df.columns
        if is_identifier_column(column, df[column])
    ]

    numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()

    metric_columns = [
        column
        for column in numeric_columns
        if column not in identifier_columns
    ]

    categorical_columns = df.select_dtypes(include=["object", "category"]).columns.tolist()

    categorical_columns = [
        column
        for column in categorical_columns
        if column not in date_like_columns
    ]

    summary_statistics = {}

    if metric_columns:
        summary_statistics = (
            df[metric_columns]
            .describe()
            .round(2)
            .fillna("")
            .to_dict()
        )

    preview_rows = df.head(10).fillna("").to_dict(orient="records")

    return {
        "rows": rows,
        "columns": columns,
        "column_names": df.columns.tolist(),
        "data_types": data_types,
        "missing_values": missing_values,
        "missing_percentages": missing_percentages,
        "duplicate_rows": duplicate_rows,
        "numeric_columns": numeric_columns,
        "identifier_columns": identifier_columns,
        "metric_columns": metric_columns,
        "categorical_columns": categorical_columns,
        "date_like_columns": date_like_columns,
        "summary_statistics": summary_statistics,
        "preview_rows": preview_rows,
    }