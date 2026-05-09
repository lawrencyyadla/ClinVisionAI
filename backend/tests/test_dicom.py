from pathlib import Path

import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage, generate_uid
from PIL import Image

from app.services.dicom import sanitize_metadata, dicom_to_png


def _synthetic_dicom(path: Path) -> None:
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    dataset = FileDataset(str(path), {}, file_meta=file_meta, preamble=b"\0" * 128)
    dataset.PatientName = "Sensitive^Patient"
    dataset.PatientID = "12345"
    dataset.PatientBirthDate = "19700101"
    dataset.Modality = "DX"
    dataset.SOPClassUID = SecondaryCaptureImageStorage
    dataset.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    dataset.Rows = 64
    dataset.Columns = 64
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = 16
    dataset.BitsStored = 12
    dataset.HighBit = 11
    dataset.PixelRepresentation = 0
    pixels = np.linspace(0, 4095, 64 * 64, dtype=np.uint16).reshape(64, 64)
    dataset.PixelData = pixels.tobytes()
    dataset.save_as(path)


def test_sanitize_metadata_removes_sensitive_tags(tmp_path):
    source = tmp_path / "scan.dcm"
    _synthetic_dicom(source)
    dataset = pydicom.dcmread(source)

    sanitized = sanitize_metadata(dataset)

    assert "PatientName" not in sanitized
    assert "PatientID" not in sanitized
    assert "PatientBirthDate" not in sanitized


def test_dicom_to_png_is_not_blank(tmp_path):
    source = tmp_path / "scan.dcm"
    output = tmp_path / "converted.png"
    _synthetic_dicom(source)

    dicom_to_png(source, output)

    with Image.open(output) as image:
        values = np.asarray(image)
    assert values.min() < values.max()
    assert values.std() > 1

