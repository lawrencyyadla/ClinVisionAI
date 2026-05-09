import pytest
from fastapi import HTTPException

from app.services.storage import validate_image_bytes


def test_rejects_empty_upload():
    with pytest.raises(HTTPException):
        validate_image_bytes(b"", ".png")


def test_rejects_invalid_image_bytes():
    with pytest.raises(HTTPException):
        validate_image_bytes(b"not an image", ".png")

