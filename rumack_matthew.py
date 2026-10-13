#!/usr/bin/env python3
"""150-line Rumack–Matthew nomogram (US/Canada), for educational decision support.

Applies to reliably timed acute acetaminophen ingestion assessed 4–24 h after
the start of ingestion. Not valid for repeated supratherapeutic ingestion (>24 h),
unreliable timing or modified-release products. Does not replace toxicology advice.
"""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import tempfile


VALID_PATTERNS = ("acute", "repeated", "unknown", "modified_release")
DISCLAIMER = (
    "Decision support only. Consult a poison center or clinical toxicologist; "
    "do not delay assessment or N-acetylcysteine while awaiting this calculation."
)


def _finite_nonnegative(value, field):
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite nonnegative number")
    try:
        number = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{field} must be a finite nonnegative number") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{field} must be a finite nonnegative number")
    return number


def treatment_line(hours_post_ingestion):
    """150 µg/mL at 4 h, falling with an assumed 4-hour half-life."""
    hours = _finite_nonnegative(hours_post_ingestion, "hours_post_ingestion")
    if not 4 <= hours <= 24:
        raise ValueError("Treatment line is defined only from 4 to 24 hours")
    return 150.0 * 2 ** (-(hours - 4.0) / 4.0)


def calculate_metrics(
    hours_post_ingestion,
    concentration_mcg_ml,
    *,
    ingestion_pattern="acute",
    time_known=True,
    delayed_absorption=False,
):
    """Compare an acetaminophen level with the 150-line when applicable.

    µg/mL is numerically identical to mg/L. Values on the line count as above.
    A below-line result is not a stand-alone decision to withhold treatment.
    """
    hours = _finite_nonnegative(hours_post_ingestion, "hours_post_ingestion")
    concentration = _finite_nonnegative(concentration_mcg_ml, "concentration_mcg_ml")
    if ingestion_pattern not in VALID_PATTERNS:
        raise ValueError("ingestion_pattern must be one of: " + ", ".join(VALID_PATTERNS))
    if not isinstance(time_known, bool) or not isinstance(delayed_absorption, bool):
        raise ValueError("time_known and delayed_absorption must be booleans")

    reasons = []
    if not time_known:
        reasons.append("Ingestion timing is unknown or unreliable.")
    if ingestion_pattern != "acute":
        reasons.append("Nomogram is not validated for this ingestion pattern/formulation.")
    if hours < 4:
        reasons.append("A level before 4 hours cannot be interpreted on the nomogram.")
    elif hours > 24:
        reasons.append("The nomogram is not applicable after 24 hours.")

    cautions = []
    if delayed_absorption:
        cautions.append(
            "Delayed absorption is possible (e.g. extended-release product or "
            "anticholinergic/opioid coingestion); repeat levels may be required."
        )
    if reasons:
        status = "not_applicable"
        line = None
        recommendation = "Do not use the nomogram: " + " ".join(reasons) + " Seek urgent toxicology advice."
    else:
        line = treatment_line(hours)
        if concentration >= line:
            status = "at_or_above_treatment_line"
            recommendation = (
                "At or above the 150-line. Promptly assess for N-acetylcysteine "
                "using local poisoning protocols and toxicology consultation."
            )
        else:
            status = "below_treatment_line"
            recommendation = (
                "Below the 150-line at this time point; this does not independently "
                "exclude toxicity or eliminate the need for further testing/treatment."
            )

    return {
        "hours_post_ingestion": hours,
        "concentration_mcg_ml": concentration,
        "ingestion_pattern": ingestion_pattern,
        "status": status,
        "treatment_line_mcg_ml": round(line, 4) if line is not None else None,
        "ratio_to_treatment_line": round(concentration / line, 4) if line else None,
        "cautions": cautions,
        "clinical_recommendation": recommendation,
        "disclaimer": DISCLAIMER,
    }


def _csv_bool(value, field, default):
    if value is None or str(value).strip() == "":
        return default
    normalized = str(value).strip().lower()
    if normalized in ("true", "1"):
        return True
    if normalized in ("false", "0"):
        return False
    raise ValueError(f"{field} must be true/false or 1/0")


def _safe_csv_cell(value):
    """Prevent exported user-supplied strings from becoming spreadsheet formulas."""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def process_batch(input_csv, output_csv):
    """Evaluate CSV rows; a malformed row aborts without replacing the output."""
    in_path = Path(input_csv).expanduser().resolve()
    out_path = Path(output_csv).expanduser().resolve()
    if in_path == out_path:
        raise ValueError("Input and output paths must differ")
    required = {"hours_post_ingestion", "concentration_mcg_ml"}
    count = 0
    temp_path = None
    try:
        with in_path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            fields = list(reader.fieldnames or [])
            missing = required.difference(fields)
            if len(fields) != len(set(fields)):
                raise ValueError("CSV contains duplicate column names")
            if missing:
                raise ValueError("CSV missing required fields: " + ", ".join(sorted(missing)))
            out_fields = fields + [
                key for key in ("status", "treatment_line_mcg_ml", "clinical_recommendation")
                if key not in fields
            ]
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="", dir=out_path.parent,
                prefix=".nomogram-", suffix=".csv", delete=False
            ) as dest:
                temp_path = Path(dest.name)
                writer = csv.DictWriter(dest, fieldnames=out_fields)
                writer.writeheader()
                for index, row in enumerate(reader, start=2):
                    try:
                        result = calculate_metrics(
                            row["hours_post_ingestion"], row["concentration_mcg_ml"],
                            ingestion_pattern=row.get("ingestion_pattern") or "acute",
                            time_known=_csv_bool(row.get("time_known"), "time_known", True),
                            delayed_absorption=_csv_bool(row.get("delayed_absorption"), "delayed_absorption", False),
                        )
                    except (ValueError, TypeError) as exc:
                        raise ValueError(f"CSV row {index}: {exc}") from exc
                    writer.writerow({k: _safe_csv_cell(v) for k, v in {
                        **row,
                        "status": result["status"],
                        "treatment_line_mcg_ml": result["treatment_line_mcg_ml"],
                        "clinical_recommendation": result["clinical_recommendation"],
                    }.items()})
                    count += 1
        os.replace(temp_path, out_path)
        temp_path = None
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
    print(f"Processed {count} rows -> {output_csv}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Acetaminophen 150-line nomogram (4–24 h)")
    commands = parser.add_subparsers(dest="command", required=True)
    single = commands.add_parser("single", help="Evaluate one acute ingestion")
    single.add_argument("--hours", type=float, required=True, help="Hours from start of ingestion")
    single.add_argument("--concentration", type=float, required=True, help="Serum acetaminophen in µg/mL (= mg/L)")
    single.add_argument("--pattern", choices=VALID_PATTERNS, default="acute")
    single.add_argument("--time-unknown", action="store_true")
    single.add_argument("--delayed-absorption", action="store_true")
    batch = commands.add_parser("batch", help="Process CSV with hours_post_ingestion and concentration_mcg_ml")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "batch":
            process_batch(args.input, args.output)
        else:
            print(json.dumps(calculate_metrics(
                args.hours, args.concentration, ingestion_pattern=args.pattern,
                time_known=not args.time_unknown, delayed_absorption=args.delayed_absorption
            ), indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
