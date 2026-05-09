from app.services.report_generator import build_safe_prompt


def test_safe_prompt_excludes_patient_and_file_fields():
    prompt = build_safe_prompt(
        prediction="Pneumonia",
        confidence=0.92,
        confidence_status="High Confidence",
        heatmap_region_summary="lower right lung region",
        model_version="densenet121-v1.0.0-demo",
    )

    assert "Pneumonia" in prompt
    assert "PatientName" not in prompt
    assert "PatientID" not in prompt
    assert "filename" not in prompt.lower()
    assert "not a diagnosis" in prompt

