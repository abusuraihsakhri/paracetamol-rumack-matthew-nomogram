import math
import pytest
from rumack_matthew import calculate_metrics, process_batch


def test_rumack_matthew_single():
    res = calculate_metrics(v1=12.0, v2=4.0)
    assert "score" in res
    assert "classification" in res
    assert res["score"] > 0


def test_rumack_matthew_batch(tmp_path):
    csv_in = tmp_path / "in.csv"
    csv_out = tmp_path / "out.csv"
    csv_in.write_text("Patient,v1,v2\nPat_001,15.0,3.0\nPat_002,5.0,1.0\n", encoding="utf-8")

    process_batch(str(csv_in), str(csv_out))
    assert csv_out.exists()
    content = csv_out.read_text(encoding="utf-8")
    assert "Pat_001" in content
    assert "score" in content


def test_calculate_metrics_rejects_nan():
    """NaN values must be rejected and not corrupt scoring."""
    res = calculate_metrics(v1=10.0, v2=float("nan"), v3=5.0)
    assert math.isfinite(res["score"])
    # Only v1 and v3 should contribute (v2 is NaN, rejected)
    assert res["score"] == round(10.0 + 5.0 * (1.0 / 2), 2)


def test_calculate_metrics_rejects_infinity():
    """Infinity values must be rejected."""
    res = calculate_metrics(v1=10.0, v2=float("inf"), v3=float("-inf"))
    assert math.isfinite(res["score"])
    assert res["score"] == 10.0


def test_calculate_metrics_rejects_empty_strings():
    """Empty/whitespace-only string values should be ignored."""
    res = calculate_metrics(v1=10.0, v2="", v3="   ")
    assert res["score"] == 10.0
    assert res["inputs_evaluated"] == 1


def test_calculate_metrics_classification_tiers():
    """Verify classification boundaries."""
    low = calculate_metrics(v1=5.0)
    assert low["classification"] == "Low / Standard"

    moderate = calculate_metrics(v1=15.0)
    assert moderate["classification"] == "Moderate / Intermediate"

    high = calculate_metrics(v1=30.0)
    assert high["classification"] == "High / Severe"


def test_process_batch_missing_file(tmp_path):
    """process_batch raises FileNotFoundError for missing input."""
    csv_out = tmp_path / "out.csv"
    with pytest.raises(FileNotFoundError):
        process_batch(str(tmp_path / "nonexistent.csv"), str(csv_out))


def test_process_batch_null_byte_rejection(tmp_path):
    """Paths with null bytes must be rejected."""
    with pytest.raises(ValueError, match="null bytes"):
        process_batch("foo\x00bar.csv", str(tmp_path / "out.csv"))
