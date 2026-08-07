import pandas as pd

def detect_date_like_columns(df: pd.DataFrame) -> list[str]:
    """
    Detects columns that can likely be parsed as dates.
    """
    date_like_columns = []

    for column in df.columns:
        if df[column].dtype == "object":
            sample = df[column].dropna().head(20)

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
        column: round(float((df[column].isnull().mean()) * 100), 2)
        for column in df.columns
    }

    duplicate_rows = int(df.duplicated().sum())

    numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_columns = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date_like_columns = detect_date_like_columns(df)

    summary_statistics = {}

    if numeric_columns:
        summary_statistics = (
            df[numeric_columns]
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
        "categorical_columns": categorical_columns,
        "date_like_columns": date_like_columns,
        "summary_statistics": summary_statistics,
        "preview_rows": preview_rows,
    }