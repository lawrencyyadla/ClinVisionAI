from __future__ import annotations

import requests

from app.core.config import settings


DISCLAIMER = "This is educational decision support for radiologist review and is not a diagnosis."


def build_safe_prompt(
    prediction: str,
    confidence: float,
    confidence_status: str,
    heatmap_region_summary: str,
    model_version: str,
) -> str:
    return (
        f"The AI model predicted {prediction} with {confidence:.2f} confidence and "
        f"{confidence_status} status. The Grad-CAM heatmap shows strongest activation in the "
        f"{heatmap_region_summary}. Model version: {model_version}. "
        "Write a concise 2-sentence educational finding for radiologist review. "
        "State that this is not a diagnosis."
    )


def template_findings(
    prediction: str,
    confidence: float,
    confidence_status: str,
    heatmap_region_summary: str,
) -> str:
    return (
        f"The model output is {prediction} with {confidence:.2f} confidence "
        f"({confidence_status}), with Grad-CAM activation strongest in the {heatmap_region_summary}. "
        f"{DISCLAIMER}"
    )


def generate_findings(
    prediction: str,
    confidence: float,
    confidence_status: str,
    heatmap_region_summary: str,
    model_version: str,
) -> str:
    prompt = build_safe_prompt(
        prediction=prediction,
        confidence=confidence,
        confidence_status=confidence_status,
        heatmap_region_summary=heatmap_region_summary,
        model_version=model_version,
    )
    fallback = template_findings(prediction, confidence, confidence_status, heatmap_region_summary)

    try:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
            json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=settings.OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        text = response.json().get("response", "").strip()
        return text or fallback
    except requests.RequestException:
        return fallback

