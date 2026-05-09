from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.scan import Scan
from app.schemas.scan import PIPELINE_STAGES, PipelineStage, ScanHistoryItem, ScanResultResponse, ScanStatusResponse, ScanUploadResponse
from app.services.storage import save_validated_upload
from app.tasks.inference_tasks import process_scan_task


router = APIRouter(prefix="/api/scans", tags=["scans"])


def _public_url(path_value: str | None) -> str | None:
    if not path_value:
        return None
    path = Path(path_value)
    if "converted" in path.parts:
        return f"/data/converted/{path.name}"
    if "heatmaps" in path.parts:
        return f"/data/heatmaps/{path.name}"
    return None


def _stage_map(scan: Scan) -> list[PipelineStage]:
    history = scan.stage_history or []
    seen: dict[str, dict] = {}
    for entry in history:
        name = entry.get("name")
        if name:
            seen[name] = entry

    stages: list[PipelineStage] = []
    failed = scan.status == "failed"
    for stage in PIPELINE_STAGES:
        entry = seen.get(stage)
        if failed and stage == scan.current_stage:
            state = "failed"
        elif entry:
            state = "completed" if scan.status == "completed" or stage != scan.current_stage else "active"
        elif stage == scan.current_stage and not failed:
            state = "active"
        else:
            state = "pending"
        stages.append(PipelineStage(name=stage, state=state, timestamp=entry.get("timestamp") if entry else None))
    return stages


def _result_response(scan: Scan) -> ScanResultResponse:
    return ScanResultResponse(
        scan_id=scan.scan_id,
        task_id=scan.task_id,
        status=scan.status,
        file_type=scan.file_type,
        converted_image_url=_public_url(scan.converted_image_path),
        heatmap_url=_public_url(scan.heatmap_path),
        overlay_url=_public_url(scan.overlay_path),
        prediction=scan.prediction,
        confidence=scan.confidence,
        confidence_status=scan.confidence_status,
        report_text=scan.report_text,
        model_name=scan.model_name,
        model_version=scan.model_version,
        model_hash=scan.model_hash,
        latency_ms=scan.latency_ms,
        error_message=scan.error_message,
        created_at=scan.created_at,
        updated_at=scan.updated_at,
    )


@router.post("", response_model=ScanUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_scan(upload: UploadFile = File(...), db: Session = Depends(get_db)) -> ScanUploadResponse:
    scan_id = str(uuid4())
    task_id = str(uuid4())
    path, file_type = await save_validated_upload(upload, scan_id)

    scan = Scan(
        scan_id=scan_id,
        task_id=task_id,
        status="queued",
        current_stage="Upload received",
        stage_history=[{"name": "Upload received", "state": "completed"}],
        file_type=file_type,
        original_image_path=str(path),
    )
    db.add(scan)
    db.commit()

    try:
        process_scan_task.apply_async(args=[scan_id], task_id=task_id)
    except Exception as exc:
        scan.status = "failed"
        scan.error_message = "Unable to enqueue inference task."
        db.add(scan)
        db.commit()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Inference queue is unavailable.") from exc

    return ScanUploadResponse(scan_id=scan_id, task_id=task_id, status=scan.status, current_stage=scan.current_stage)


@router.get("/{task_id}/status", response_model=ScanStatusResponse)
def get_status(task_id: str, db: Session = Depends(get_db)) -> ScanStatusResponse:
    scan = db.query(Scan).filter(Scan.task_id == task_id).first()
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return ScanStatusResponse(
        scan_id=scan.scan_id,
        task_id=scan.task_id,
        status=scan.status,
        current_stage=scan.current_stage,
        stages=_stage_map(scan),
        error_message=scan.error_message,
        created_at=scan.created_at,
        updated_at=scan.updated_at,
    )


@router.get("/result/{scan_id}", response_model=ScanResultResponse)
def get_result(scan_id: str, db: Session = Depends(get_db)) -> ScanResultResponse:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")
    if scan.status not in {"completed", "failed"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Scan processing is not complete.")
    return _result_response(scan)


@router.get("", response_model=list[ScanHistoryItem])
def list_scans(db: Session = Depends(get_db)) -> list[ScanHistoryItem]:
    scans = db.query(Scan).order_by(desc(Scan.created_at)).limit(50).all()
    return [
        ScanHistoryItem(
            scan_id=scan.scan_id,
            task_id=scan.task_id,
            status=scan.status,
            file_type=scan.file_type,
            prediction=scan.prediction,
            confidence=scan.confidence,
            confidence_status=scan.confidence_status,
            latency_ms=scan.latency_ms,
            created_at=scan.created_at,
            updated_at=scan.updated_at,
        )
        for scan in scans
    ]

