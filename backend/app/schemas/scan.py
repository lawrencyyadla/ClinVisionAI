from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


PIPELINE_STAGES = [
    "Upload received",
    "Validating file",
    "Sanitizing metadata",
    "Converting DICOM preview",
    "Running DenseNet121 inference",
    "Generating Grad-CAM heatmap",
    "Generating AI findings",
    "Completed",
]


class PipelineStage(BaseModel):
    name: str
    state: Literal["pending", "active", "completed", "failed"]
    timestamp: datetime | None = None


class ScanUploadResponse(BaseModel):
    scan_id: str
    task_id: str
    status: str
    current_stage: str


class ScanStatusResponse(BaseModel):
    scan_id: str
    task_id: str
    status: str
    current_stage: str
    stages: list[PipelineStage]
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class ScanResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_id: str
    task_id: str
    status: str
    file_type: str
    converted_image_url: str | None
    heatmap_url: str | None
    overlay_url: str | None
    prediction: str | None
    confidence: float | None
    confidence_status: str | None
    report_text: str | None
    model_name: str | None
    model_version: str | None
    model_hash: str | None
    latency_ms: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class ScanHistoryItem(BaseModel):
    scan_id: str
    task_id: str
    status: str
    file_type: str
    prediction: str | None
    confidence: float | None
    confidence_status: str | None
    latency_ms: int | None
    created_at: datetime
    updated_at: datetime


class HealthCheckResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    api: Literal["healthy"]
    postgres: Literal["healthy", "unhealthy"]
    redis: Literal["healthy", "unhealthy"]


class VersionResponse(BaseModel):
    app_name: str
    api_version: str
    model_name: str
    model_version: str
    model_hash: str
    checkpoint_configured: bool
    clinical_use: Literal["not_validated_for_clinical_use"]

