from __future__ import annotations

import io
from pathlib import Path

import pydicom
from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.core.config import settings


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".dcm"}


def ensure_storage_dirs() -> None:
    for directory in [settings.UPLOAD_DIR, settings.CONVERTED_DIR, settings.HEATMAP_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def _extension(filename: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Use JPG, PNG, or DICOM.",
        )
    return suffix


def validate_image_bytes(file_bytes: bytes, extension: str) -> None:
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty uploads are not allowed.")

    if len(file_bytes) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Uploaded file is too large.")

    try:
        if extension == ".dcm":
            dataset = pydicom.dcmread(io.BytesIO(file_bytes), stop_before_pixels=False, force=False)
            if "PixelData" not in dataset:
                raise ValueError("DICOM file does not contain pixel data.")
        else:
            with Image.open(io.BytesIO(file_bytes)) as image:
                image.verify()
    except (UnidentifiedImageError, Exception) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is corrupt or invalid.") from exc


async def save_validated_upload(upload: UploadFile, scan_id: str) -> tuple[Path, str]:
    ensure_storage_dirs()
    extension = _extension(upload.filename)
    file_bytes = await upload.read()
    validate_image_bytes(file_bytes, extension)

    destination = settings.UPLOAD_DIR / f"{scan_id}{extension}"
    destination.write_bytes(file_bytes)
    return destination, extension.lstrip(".")

