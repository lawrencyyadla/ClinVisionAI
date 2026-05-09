from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from PIL import Image

from app.ml.model_loader import get_model
from app.ml.preprocess import preprocess_image


def _colormap(gray: np.ndarray) -> np.ndarray:
    x = np.clip(gray.astype(np.float32), 0, 1)
    red = np.clip(1.5 - np.abs(4 * x - 3), 0, 1)
    green = np.clip(1.5 - np.abs(4 * x - 2), 0, 1)
    blue = np.clip(1.5 - np.abs(4 * x - 1), 0, 1)
    return (np.stack([red, green, blue], axis=-1) * 255).astype(np.uint8)


def _region_summary(heatmap: np.ndarray) -> str:
    rows = np.array_split(heatmap, 3, axis=0)
    labels_y = ["upper", "middle", "lower"]
    labels_x = ["left", "central", "right"]
    best_score = -1.0
    best_label = "central lung region"

    for y_index, row in enumerate(rows):
        for x_index, cell in enumerate(np.array_split(row, 3, axis=1)):
            score = float(cell.mean())
            if score > best_score:
                best_score = score
                best_label = f"{labels_y[y_index]} {labels_x[x_index]} lung region"
    return best_label


def generate_gradcam(
    image_path: Path,
    class_index: int,
    raw_heatmap_path: Path,
    overlay_path: Path,
) -> dict:
    loaded = get_model()
    model = loaded.model
    device = loaded.device
    target_layer = model.features.denseblock4
    activations = {}
    gradients = {}

    def forward_hook(_module, _inputs, output):
        activations["value"] = output.detach()

    def backward_hook(_module, _grad_input, grad_output):
        gradients["value"] = grad_output[0].detach()

    forward_handle = target_layer.register_forward_hook(forward_hook)
    backward_handle = target_layer.register_full_backward_hook(backward_hook)

    try:
        tensor = preprocess_image(image_path).to(device)
        model.zero_grad(set_to_none=True)
        logits = model(tensor)
        score = logits[:, class_index].sum()
        score.backward()

        activation = activations["value"]
        gradient = gradients["value"]
        weights = gradient.mean(dim=(2, 3), keepdim=True)
        cam = torch.relu((weights * activation).sum(dim=1, keepdim=True))
        cam = torch.nn.functional.interpolate(cam, size=(224, 224), mode="bilinear", align_corners=False)
        cam = cam.squeeze().detach().cpu().numpy()
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
    finally:
        forward_handle.remove()
        backward_handle.remove()

    with Image.open(image_path) as original:
        original_rgb = original.convert("RGB")
        original_size = original_rgb.size
        resized_cam = Image.fromarray((cam * 255).astype(np.uint8), mode="L").resize(original_size, Image.BILINEAR)
        heatmap = np.asarray(resized_cam).astype(np.float32) / 255.0

        color = Image.fromarray(_colormap(heatmap), mode="RGB")
        overlay = Image.blend(original_rgb, color, alpha=0.40)

    raw_heatmap_path.parent.mkdir(parents=True, exist_ok=True)
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    resized_cam.save(raw_heatmap_path)
    overlay.save(overlay_path)

    return {
        "heatmap_region_summary": _region_summary(heatmap),
        "heatmap_path": str(raw_heatmap_path),
        "overlay_path": str(overlay_path),
    }

