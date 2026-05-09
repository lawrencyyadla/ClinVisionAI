from __future__ import annotations

from pathlib import Path

import numpy as np
import pydicom
from PIL import Image
from pydicom.dataset import Dataset
from pydicom.pixels import apply_voi_lut


SENSITIVE_DICOM_KEYWORDS = {
    "PatientName",
    "PatientID",
    "PatientBirthDate",
    "PatientSex",
    "PatientAddress",
    "InstitutionName",
    "ReferringPhysicianName",
    "AccessionNumber",
    "StudyID",
    "StudyDate",
    "SeriesDate",
    "ContentDate",
}


def sanitize_metadata(dataset: Dataset) -> Dataset:
    for keyword in SENSITIVE_DICOM_KEYWORDS:
        if hasattr(dataset, keyword):
            delattr(dataset, keyword)
    return dataset


def _select_frame(pixel_array: np.ndarray) -> np.ndarray:
    if pixel_array.ndim == 3:
        return pixel_array[0]
    if pixel_array.ndim > 3:
        return pixel_array.reshape((-1,) + pixel_array.shape[-2:])[0]
    return pixel_array


def _normalize_to_uint8(array: np.ndarray) -> np.ndarray:
    pixels = array.astype(np.float32)
    if not np.isfinite(pixels).all():
        pixels = np.nan_to_num(pixels)

    low, high = np.percentile(pixels, [0.5, 99.5])
    if high <= low:
        low = float(np.min(pixels))
        high = float(np.max(pixels))
    if high <= low:
        raise ValueError("DICOM pixel data has no usable intensity range.")

    pixels = np.clip(pixels, low, high)
    pixels = (pixels - low) / (high - low)
    output = (pixels * 255).astype(np.uint8)

    if output.std() < 1:
        min_value = float(np.min(array))
        max_value = float(np.max(array))
        if max_value <= min_value:
            raise ValueError("DICOM conversion produced a blank preview.")
        output = (((array.astype(np.float32) - min_value) / (max_value - min_value)) * 255).astype(np.uint8)

    return output


def dicom_to_png(input_path: Path, output_path: Path) -> Path:
    dataset = pydicom.dcmread(str(input_path), force=False)
    sanitize_metadata(dataset)

    try:
        pixels = apply_voi_lut(dataset.pixel_array, dataset)
    except Exception:
        pixels = dataset.pixel_array

    pixels = _select_frame(np.asarray(pixels))
    image_array = _normalize_to_uint8(pixels)

    if getattr(dataset, "PhotometricInterpretation", "").upper() == "MONOCHROME1":
        image_array = 255 - image_array

    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(image_array, mode="L").save(output_path)
    return output_path


def standard_image_to_png(input_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(input_path) as image:
        image.convert("L").save(output_path)
    return output_path
