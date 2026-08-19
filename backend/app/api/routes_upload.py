from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.file_service import save_uploaded_file, get_dataset_file_path
from app.services.profiling_service import profile_dataset

router = APIRouter(tags=["Upload"])


@router.post("/upload/csv")
def upload_csv(file: UploadFile = File(...)):
    """
    Uploads a CSV file, saves it locally, and returns a dataset profile.
    """
    try:
        file_metadata = save_uploaded_file(file)
        dataset_profile = profile_dataset(file_metadata["file_path"])

        return {
            "message": "CSV uploaded and profiled successfully.",
            "dataset": {
                "dataset_id": file_metadata["dataset_id"],
                "original_filename": file_metadata["original_filename"],
                "stored_filename": file_metadata["stored_filename"],
                "file_path": file_metadata["file_path"],
            },
            "profile": dataset_profile,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}"
        )


@router.get("/datasets/{dataset_id}/profile")
def get_dataset_profile(dataset_id: str):
    """
    Returns the profile for an already uploaded dataset.
    """
    try:
        file_path = get_dataset_file_path(dataset_id)
        dataset_profile = profile_dataset(file_path)

        return {
            "dataset_id": dataset_id,
            "profile": dataset_profile,
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}"
        )


@router.get("/datasets/{dataset_id}/preview")
def get_dataset_preview(dataset_id: str):
    """
    Returns the first 10 rows of an uploaded dataset.
    """
    try:
        file_path = get_dataset_file_path(dataset_id)
        dataset_profile = profile_dataset(file_path)

        return {
            "dataset_id": dataset_id,
            "preview_rows": dataset_profile["preview_rows"],
        }

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}"
        )