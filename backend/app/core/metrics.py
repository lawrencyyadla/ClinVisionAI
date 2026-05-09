from __future__ import annotations

import math
from collections import Counter as PyCounter

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.responses import Response

from app.core.config import settings
from app.models.scan import Scan


HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests.",
    ["method", "path", "status"],
)

SCAN_TASKS_TOTAL = Gauge("scan_tasks_total", "Scan tasks by status.", ["status"])
SCAN_TASKS_FAILED_TOTAL = Gauge("scan_tasks_failed_total", "Failed scan tasks.")
INFERENCE_LATENCY_MS = Gauge("inference_latency_ms", "Inference latency in milliseconds.", ["stat"])
CONFIDENCE_SCORE_DISTRIBUTION = Gauge(
    "confidence_score_distribution",
    "Confidence score distribution.",
    ["bucket"],
)
INCONCLUSIVE_RATE = Gauge("inconclusive_rate", "Fraction of completed scans marked inconclusive.")
FILE_TYPE_COUNT = Gauge("file_type_count", "Uploaded file type count.", ["file_type"])
MODEL_VERSION_INFO = Gauge(
    "model_version_info",
    "Model version metadata.",
    ["model_name", "model_version", "model_hash"],
)


def sync_scan_metrics(db: Session) -> None:
    status_counts = dict(db.query(Scan.status, func.count(Scan.scan_id)).group_by(Scan.status).all())
    for status in ["queued", "running", "completed", "failed"]:
        SCAN_TASKS_TOTAL.labels(status=status).set(status_counts.get(status, 0))

    SCAN_TASKS_FAILED_TOTAL.set(status_counts.get("failed", 0))

    latencies = [
        row[0]
        for row in db.query(Scan.latency_ms).filter(Scan.latency_ms.is_not(None)).all()
        if row[0] is not None
    ]
    if latencies:
        ordered = sorted(latencies)
        p95_index = max(0, math.ceil(len(ordered) * 0.95) - 1)
        INFERENCE_LATENCY_MS.labels(stat="avg").set(sum(ordered) / len(ordered))
        INFERENCE_LATENCY_MS.labels(stat="p95").set(ordered[p95_index])
    else:
        INFERENCE_LATENCY_MS.labels(stat="avg").set(0)
        INFERENCE_LATENCY_MS.labels(stat="p95").set(0)

    confidences = [
        row[0]
        for row in db.query(Scan.confidence).filter(Scan.confidence.is_not(None)).all()
        if row[0] is not None
    ]
    buckets = PyCounter({"lt_0_60": 0, "0_60_to_0_74": 0, "gte_0_75": 0})
    for confidence in confidences:
        if confidence < 0.60:
            buckets["lt_0_60"] += 1
        elif confidence < 0.75:
            buckets["0_60_to_0_74"] += 1
        else:
            buckets["gte_0_75"] += 1
    for bucket, count in buckets.items():
        CONFIDENCE_SCORE_DISTRIBUTION.labels(bucket=bucket).set(count)

    completed_count = status_counts.get("completed", 0)
    inconclusive_count = (
        db.query(func.count(Scan.scan_id))
        .filter(Scan.confidence_status == "Inconclusive - Requires Manual Review")
        .scalar()
        or 0
    )
    INCONCLUSIVE_RATE.set(inconclusive_count / completed_count if completed_count else 0)

    file_counts = dict(db.query(Scan.file_type, func.count(Scan.scan_id)).group_by(Scan.file_type).all())
    for file_type in ["jpg", "jpeg", "png", "dcm"]:
        FILE_TYPE_COUNT.labels(file_type=file_type).set(file_counts.get(file_type, 0))

    MODEL_VERSION_INFO.labels(
        model_name=settings.MODEL_NAME,
        model_version=settings.MODEL_VERSION,
        model_hash=settings.MODEL_HASH,
    ).set(1)


def metrics_response(db: Session) -> Response:
    sync_scan_metrics(db)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
