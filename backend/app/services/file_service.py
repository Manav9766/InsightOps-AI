import os
import re
import uuid
from pathlib import Path

from fastapi import UploadFile


APP_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = APP_DIR / "storage" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}$"
)


def validate_csv_file(file: UploadFile) -> None:
    """
    Validates that the uploaded file is a CSV.
    """
    if not file.filename:
        raise ValueError("No file name provided.")

    if not file.filename.lower().endswith(".csv"):
        raise ValueError("Only CSV files are supported in Phase 1.")


def validate_dataset_id(dataset_id: str) -> str:
    """
    Validates and normalizes a dataset UUID.
    """
    clean_id = str(dataset_id).strip().lower()

    if not UUID_PATTERN.match(clean_id):
        raise ValueError(f"Invalid dataset_id format: {dataset_id}")

    return clean_id


def save_uploaded_file(file: UploadFile) -> dict:
    """
    Saves an uploaded CSV file locally and returns file metadata.
    """
    validate_csv_file(file)

    dataset_id = str(uuid.uuid4())
    safe_filename = os.path.basename(file.filename)
    stored_filename = f"{dataset_id}_{safe_filename}"
    file_path = UPLOAD_DIR / stored_filename

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    return {
        "dataset_id": dataset_id,
        "original_filename": safe_filename,
        "stored_filename": stored_filename,
        "file_path": str(file_path),
    }


def get_dataset_file_path(dataset_id: str) -> str:
    """
    Finds the stored CSV file path for a dataset_id.
    """
    clean_id = validate_dataset_id(dataset_id)

    matching_files = list(UPLOAD_DIR.glob(f"{clean_id}_*.csv"))

    if not matching_files:
        existing_files = [file.name for file in UPLOAD_DIR.glob("*.csv")]

        raise FileNotFoundError(
            f"No dataset found for dataset_id: {clean_id}. "
            f"Available uploaded files: {existing_files}"
        )

    return str(matching_files[0])