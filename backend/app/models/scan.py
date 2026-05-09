from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Scan(Base):
    __tablename__ = "scans"

    scan_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    task_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, default="queued", nullable=False)
    current_stage: Mapped[str] = mapped_column(String(128), default="Upload received", nullable=False)
    stage_history: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    file_type: Mapped[str] = mapped_column(String(16), nullable=False)
    original_image_path: Mapped[str] = mapped_column(Text, nullable=False)
    converted_image_path: Mapped[str | None] = mapped_column(Text)
    heatmap_path: Mapped[str | None] = mapped_column(Text)
    overlay_path: Mapped[str | None] = mapped_column(Text)

    prediction: Mapped[str | None] = mapped_column(String(64))
    confidence: Mapped[float | None] = mapped_column(Float)
    confidence_status: Mapped[str | None] = mapped_column(String(64))
    report_text: Mapped[str | None] = mapped_column(Text)

    model_name: Mapped[str | None] = mapped_column(String(128))
    model_version: Mapped[str | None] = mapped_column(String(128))
    model_hash: Mapped[str | None] = mapped_column(String(128))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

