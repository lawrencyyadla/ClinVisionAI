from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import torch
from torch import nn
from torchvision import models

from app.core.config import settings


CLASS_NAMES = ["Normal", "Pneumonia"]
_MODEL_CACHE: "LoadedModel | None" = None


@dataclass
class LoadedModel:
    model: nn.Module
    device: torch.device
    model_name: str
    model_version: str
    model_hash: str
    checkpoint_configured: bool


def _checkpoint_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:16]


def _build_model() -> nn.Module:
    torch.manual_seed(2026)
    model = models.densenet121(weights=None)
    in_features = model.classifier.in_features
    model.classifier = nn.Linear(in_features, len(CLASS_NAMES))
    return model


def _load_state_dict(model: nn.Module, checkpoint_path: Path) -> None:
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    if isinstance(checkpoint, dict):
        state_dict = checkpoint.get("model_state_dict") or checkpoint.get("state_dict") or checkpoint
    else:
        state_dict = checkpoint
    cleaned = {key.replace("module.", ""): value for key, value in state_dict.items()}
    model.load_state_dict(cleaned, strict=False)


def get_model() -> LoadedModel:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    model = _build_model()
    checkpoint_configured = bool(settings.MODEL_CHECKPOINT_PATH)
    model_hash = settings.MODEL_HASH

    if checkpoint_configured:
        checkpoint_path = Path(settings.MODEL_CHECKPOINT_PATH)
        if checkpoint_path.exists():
            _load_state_dict(model, checkpoint_path)
            model_hash = _checkpoint_hash(checkpoint_path)
        else:
            checkpoint_configured = False

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    _MODEL_CACHE = LoadedModel(
        model=model,
        device=device,
        model_name=settings.MODEL_NAME,
        model_version=settings.MODEL_VERSION,
        model_hash=model_hash,
        checkpoint_configured=checkpoint_configured,
    )
    return _MODEL_CACHE

