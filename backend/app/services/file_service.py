import os
import uuid
from pathlib import Path
from fastapi import UploadFile

# Author: Manav


UPLOAD_DIR = Path("app/storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def validate_csv_file(file: UploadFile) -> None:
    """
    Validates that the uploaded file is a CSV.
    Raises ValueError if file is invalid.
    """
    if not file.filename:
        raise ValueError("No file name provided.")

    if not file.filename.lower().endswith(".csv"):
        raise ValueError("Only CSV files are supported in Phase 1.")


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
    Finds the stored file path for a dataset_id.
    """
    matches = list(UPLOAD_DIR.glob(f"{dataset_id}_*"))

    if not matches:
        raise FileNotFoundError(f"No dataset found for dataset_id: {dataset_id}")

    return str(matches[0])
