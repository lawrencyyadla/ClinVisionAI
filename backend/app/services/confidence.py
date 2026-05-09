def confidence_status(confidence: float) -> str:
    if confidence >= 0.75:
        return "High Confidence"
    if confidence >= 0.60:
        return "Moderate Confidence"
    return "Inconclusive - Requires Manual Review"

