from __future__ import annotations

from pathlib import Path

import torch

from app.ml.model_loader import CLASS_NAMES, get_model
from app.ml.preprocess import preprocess_image


def run_inference(image_path: Path) -> dict:
    loaded = get_model()
    tensor = preprocess_image(image_path).to(loaded.device)

    with torch.no_grad():
        logits = loaded.model(tensor)
        probabilities = torch.softmax(logits, dim=1)[0]
        confidence, class_index = torch.max(probabilities, dim=0)

    return {
        "prediction": CLASS_NAMES[int(class_index.item())],
        "confidence": float(confidence.item()),
        "class_index": int(class_index.item()),
        "model_name": loaded.model_name,
        "model_version": loaded.model_version,
        "model_hash": loaded.model_hash,
        "checkpoint_configured": loaded.checkpoint_configured,
    }

