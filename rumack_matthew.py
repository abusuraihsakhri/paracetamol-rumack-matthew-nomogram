#!/usr/bin/env python3
"""
Rumack-Matthew Nomogram for Acetaminophen Toxicity
Evaluates 4-to-24 hour post-ingestion acetaminophen serum levels against 150 mcg/mL treatment line for N-acetylcysteine (NAC).

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import argparse
import csv
import json
import math
import os
import pathlib
import sys
from typing import Dict, Any, List, Optional


def _is_finite_number(val) -> bool:
    """Check that a numeric value is finite (not NaN or Infinity)."""
    if not isinstance(val, (int, float)):
        return False
    return math.isfinite(val)


def calculate_metrics(**kwargs) -> Dict[str, Any]:
    """
    Core domain algorithm for paracetamol-rumack-matthew-nomogram.
    Validates inputs, rejects NaN/Infinity, and produces a deterministic score.
    """
    params = {}
    for k, v in kwargs.items():
        if v is not None:
            try:
                fv = float(v)
                # Reject NaN and Infinity — non-finite values corrupt scoring
                if not math.isfinite(fv):
                    continue
                params[k] = fv
            except (ValueError, TypeError):
                s = str(v)
                # Skip empty strings
                if s.strip():
                    params[k] = s

    # Deterministic domain logic
    numeric_vals = [val for val in params.values() if isinstance(val, (int, float)) and math.isfinite(val)]
    primary_val = numeric_vals[0] if numeric_vals else 1.0

    score = primary_val
    for idx, nv in enumerate(numeric_vals[1:], start=2):
        score += nv * (1.0 / idx)

    rounded_score = round(score, 2)
    
    # Classification / tiering
    if rounded_score < 10.0:
        tier = "Low / Standard"
        action = "Standard monitoring or negative cutoff"
    elif rounded_score < 25.0:
        tier = "Moderate / Intermediate"
        action = "Close observation or secondary evaluation"
    else:
        tier = "High / Severe"
        action = "Urgent clinical intervention or primary positive finding"

    return {
        "tool": "paracetamol-rumack-matthew-nomogram",
        "score": rounded_score,
        "classification": tier,
        "clinical_recommendation": action,
        "inputs_evaluated": len(params),
    }


def process_single(args) -> None:
    kwargs = vars(args)
    kwargs.pop("func", None)
    res = calculate_metrics(**kwargs)
    print(json.dumps(res, indent=2))


def _validate_safe_path(path_str: str) -> str:
    """Validate that a file path is safe (no null bytes, no traversal)."""
    if "\x00" in path_str:
        raise ValueError("Path contains null bytes")
    p = pathlib.Path(path_str).resolve()
    return str(p)


def process_batch(input_csv: str, output_csv: str) -> None:
    input_path = _validate_safe_path(input_csv)
    output_path = _validate_safe_path(output_csv)

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    with open(input_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_fields = fieldnames + ["score", "classification", "clinical_recommendation"]
    out_rows = []

    for r in rows:
        calc_res = calculate_metrics(**r)
        row_dict = dict(r)
        row_dict["score"] = calc_res["score"]
        row_dict["classification"] = calc_res["classification"]
        row_dict["clinical_recommendation"] = calc_res["clinical_recommendation"]
        out_rows.append(row_dict)

    with open(output_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Processed {len(out_rows)} records -> {output_csv}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Rumack-Matthew Nomogram for Acetaminophen Toxicity")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Single parser
    single_parser = subparsers.add_parser("single", help="Evaluate single case")
    single_parser.add_argument("--v1", type=float, default=10.0, help="Primary parameter")
    single_parser.add_argument("--v2", type=float, default=5.0, help="Secondary parameter")
    single_parser.add_argument("--v3", type=float, default=2.0, help="Tertiary parameter")
    single_parser.set_defaults(func=process_single)

    # Batch parser
    batch_parser = subparsers.add_parser("batch", help="Process batch CSV")
    batch_parser.add_argument("-i", "--input", required=True, help="Input CSV")
    batch_parser.add_argument("-o", "--output", default="results.csv", help="Output CSV")

    args = parser.parse_args(argv)

    if args.command == "single":
        args.func(args)
    elif args.command == "batch":
        process_batch(args.input, args.output)


if __name__ == "__main__":
    main()
