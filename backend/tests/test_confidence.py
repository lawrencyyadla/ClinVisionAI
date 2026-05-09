from app.services.confidence import confidence_status


def test_confidence_status_high():
    assert confidence_status(0.75) == "High Confidence"
    assert confidence_status(0.91) == "High Confidence"


def test_confidence_status_moderate():
    assert confidence_status(0.60) == "Moderate Confidence"
    assert confidence_status(0.749) == "Moderate Confidence"


def test_confidence_status_inconclusive():
    assert confidence_status(0.59) == "Inconclusive - Requires Manual Review"

