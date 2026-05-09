from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

import structlog
from billiard.exceptions import SoftTimeLimitExceeded
from celery import Celery
from celery.signals import worker_process_init
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging import configure_logging
from app.ml.gradcam import generate_gradcam
from app.ml.inference import run_inference
from app.ml.model_loader import get_model
from app.models.scan import Scan
from app.schemas.scan import PIPELINE_STAGES
from app.services.confidence import confidence_status
from app.services.dicom import dicom_to_png, standard_image_to_png
from app.services.report_generator import generate_findings
from app.services.storage import ensure_storage_dirs


logger = structlog.get_logger()
configure_logging()

celery_app = Celery("clinvision_worker", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_expires=settings.CELERY_RESULT_EXPIRES_SECONDS,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT_SECONDS,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT_SECONDS,
    worker_prefetch_multiplier=1,
    task_track_started=True,
)


@worker_process_init.connect
def load_model_on_worker_start(**_kwargs):
    get_model()


def _stage_entry(name: str, state: str) -> dict:
    return {"name": name, "state": state, "timestamp": datetime.utcnow().isoformat()}


def _update_stage(db: Session, scan: Scan, stage_name: str, status: str = "running") -> None:
    history = list(scan.stage_history or [])
    history.append(_stage_entry(stage_name, "completed" if stage_name == "Completed" else "active"))
    scan.stage_history = history
    scan.current_stage = stage_name
    scan.status = status
    db.add(scan)
    db.commit()
    db.refresh(scan)


def _mark_failed(db: Session, scan: Scan, message: str) -> None:
    history = list(scan.stage_history or [])
    history.append(_stage_entry(scan.current_stage or "Failed", "failed"))
    scan.stage_history = history
    scan.status = "failed"
    scan.error_message = message
    db.add(scan)
    db.commit()


@celery_app.task(name="app.tasks.inference_tasks.process_scan_task", bind=True)
def process_scan_task(self, scan_id: str) -> dict:
    ensure_storage_dirs()
    started = time.perf_counter()
    db = SessionLocal()
    scan = db.get(Scan, scan_id)
    if scan is None:
        db.close()
        raise ValueError("Scan record not found.")

    try:
        _update_stage(db, scan, "Validating file", status="running")

        original_path = Path(scan.original_image_path)
        converted_path = settings.CONVERTED_DIR / f"{scan.scan_id}.png"

        _update_stage(db, scan, "Sanitizing metadata", status="running")
        _update_stage(db, scan, "Converting DICOM preview", status="running")
        if scan.file_type == "dcm":
            dicom_to_png(original_path, converted_path)
        else:
            standard_image_to_png(original_path, converted_path)
        scan.converted_image_path = str(converted_path)
        db.add(scan)
        db.commit()
        db.refresh(scan)

        _update_stage(db, scan, "Running DenseNet121 inference", status="running")
        inference = run_inference(converted_path)
        status_label = confidence_status(inference["confidence"])

        _update_stage(db, scan, "Generating Grad-CAM heatmap", status="running")
        raw_heatmap_path = settings.HEATMAP_DIR / f"{scan.scan_id}_raw.png"
        overlay_path = settings.HEATMAP_DIR / f"{scan.scan_id}_overlay.png"
        gradcam = generate_gradcam(
            image_path=converted_path,
            class_index=inference["class_index"],
            raw_heatmap_path=raw_heatmap_path,
            overlay_path=overlay_path,
        )

        _update_stage(db, scan, "Generating AI findings", status="running")
        report = generate_findings(
            prediction=inference["prediction"],
            confidence=inference["confidence"],
            confidence_status=status_label,
            heatmap_region_summary=gradcam["heatmap_region_summary"],
            model_version=inference["model_version"],
        )

        latency_ms = int((time.perf_counter() - started) * 1000)
        scan.prediction = inference["prediction"]
        scan.confidence = inference["confidence"]
        scan.confidence_status = status_label
        scan.report_text = report
        scan.model_name = inference["model_name"]
        scan.model_version = inference["model_version"]
        scan.model_hash = inference["model_hash"]
        scan.heatmap_path = gradcam["heatmap_path"]
        scan.overlay_path = gradcam["overlay_path"]
        scan.latency_ms = latency_ms
        scan.error_message = None
        db.add(scan)
        db.commit()
        db.refresh(scan)
        _update_stage(db, scan, "Completed", status="completed")

        logger.info(
            "inference_complete",
            scan_id=scan.scan_id,
            confidence=round(float(scan.confidence or 0), 4),
            confidence_status=scan.confidence_status,
            latency_ms=latency_ms,
            model_version=scan.model_version,
        )
        return {"scan_id": scan.scan_id, "status": "completed"}
    except SoftTimeLimitExceeded:
        _mark_failed(db, scan, "Inference task timed out.")
        logger.error("inference_failed", scan_id=scan.scan_id, reason="timeout")
        raise
    except Exception as exc:
        _mark_failed(db, scan, "Inference task failed. Review worker logs for technical details.")
        logger.error("inference_failed", scan_id=scan.scan_id, reason=exc.__class__.__name__)
        raise
    finally:
        db.close()
