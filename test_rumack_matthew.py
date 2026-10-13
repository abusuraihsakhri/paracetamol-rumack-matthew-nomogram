import csv
import math
import pytest

from rumack_matthew import calculate_metrics, treatment_line, process_batch, main


@pytest.mark.parametrize("hour, expected", [
    (4, 150.0), (8, 75.0), (12, 37.5), (16, 18.75),
    (20, 9.375), (24, 4.6875),
])
def test_nomogram_line(hour, expected):
    assert treatment_line(hour) == pytest.approx(expected)


def test_on_line_triggers_treatment_classification():
    result = calculate_metrics(8, 75)
    assert result["status"] == "at_or_above_treatment_line"
    assert result["ratio_to_treatment_line"] == 1.0


def test_above_and_below_line():
    assert calculate_metrics(4, 151)["status"] == "at_or_above_treatment_line"
    assert calculate_metrics(12, 20)["status"] == "below_treatment_line"


@pytest.mark.parametrize("time, pattern, known", [
    (3.999, "acute", True),
    (24.001, "acute", True),
    (8, "repeated", True),
    (8, "unknown", True),
    (8, "modified_release", True),
    (8, "acute", False),
])
def test_not_applicable(time, pattern, known):
    result = calculate_metrics(time, 200, ingestion_pattern=pattern, time_known=known)
    assert result["status"] == "not_applicable"
    assert result["treatment_line_mcg_ml"] is None


@pytest.mark.parametrize("time, concentration", [
    (-1, 10), (8, -0.01), (math.nan, 10), (8, math.inf),
    (float("-inf"), 3), ("", 8), (True, 3), (8, False),
])
def test_bad_numbers_rejected(time, concentration):
    with pytest.raises(ValueError):
        calculate_metrics(time, concentration)


def test_flags_are_type_checked():
    with pytest.raises(ValueError):
        calculate_metrics(8, 70, time_known="false")
    with pytest.raises(ValueError):
        calculate_metrics(8, 70, ingestion_pattern="something_else")


def test_delayed_absorption_warning():
    result = calculate_metrics(8, 25, delayed_absorption=True)
    assert result["status"] == "below_treatment_line"
    assert result["cautions"]


def test_batch_roundtrip(tmp_path):
    input_path, output_path = tmp_path / "in.csv", tmp_path / "out.csv"
    input_path.write_text(
        "case,hours_post_ingestion,concentration_mcg_ml,ingestion_pattern\n"
        "A,4,150,acute\nB,8,20,repeated\n", encoding="utf-8"
    )
    process_batch(str(input_path), str(output_path))
    with output_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["status"] == "at_or_above_treatment_line"
    assert rows[1]["status"] == "not_applicable"
    assert rows[0]["case"] == "A"


def test_invalid_batch_keeps_original_output(tmp_path):
    input_path, output_path = tmp_path / "in.csv", tmp_path / "out.csv"
    input_path.write_text(
        "hours_post_ingestion,concentration_mcg_ml\n4,150\n8,NaN\n", encoding="utf-8"
    )
    output_path.write_text("previous", encoding="utf-8")
    with pytest.raises(ValueError, match="row 3"):
        process_batch(str(input_path), str(output_path))
    assert output_path.read_text() == "previous"


def test_missing_fields_and_same_file(tmp_path):
    path = tmp_path / "in.csv"
    path.write_text("v1,v2\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="required fields"):
        process_batch(str(path), str(tmp_path / "out.csv"))
    with pytest.raises(ValueError, match="differ"):
        process_batch(str(path), str(path))


def test_cli(capsys):
    assert main(["single", "--hours", "8", "--concentration", "75"]) == 0
    assert "at_or_above_treatment_line" in capsys.readouterr().out

def test_rejects_invalid_boolean_in_csv(tmp_path):
    source = tmp_path / "cases.csv"
    source.write_text(
        "hours_post_ingestion,concentration_mcg_ml,delayed_absorption\\n"
        "8,75,unsure\\n".replace("\\\\n", "\\n"), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="delayed_absorption"):
        process_batch(source, tmp_path / "out.csv")


def test_csv_spreadsheet_injection_escaped(tmp_path):
    source = tmp_path / "cases.csv"
    source.write_text(
        "case,hours_post_ingestion,concentration_mcg_ml\\n"
        "=HYPERLINK(A1),8,75\\n".replace("\\\\n", "\\n"), encoding="utf-8"
    )
    output = tmp_path / "out.csv"
    process_batch(source, output)
    with output.open(encoding="utf-8", newline="") as f:
        row = next(csv.DictReader(f))
    assert row["case"].startswith("'=")
