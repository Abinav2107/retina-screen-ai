"""
test_batch.py -- Automated test suite for Camp Mode: Batch Screening.
Validates:
  1. process_batch() on 5 sample patient images
  2. Sorting by urgency (critical cases first)
  3. Dynamic summary line calculation ("X patients screened — Y flagged for referral")
  4. DataFrame generation with required columns
  5. CSV report generation and validation
  6. Multi-language support in batch mode

Run:
    python test_batch.py
"""

import os
import sys
import csv
from pathlib import Path
import pandas as pd

# Force UTF-8 encoding on Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from batch import (
    process_batch,
    build_dataframe,
    calculate_camp_summary,
    export_batch_csv,
)
from app import run_batch_camp_screening


def test_batch_screening():
    print("=" * 65)
    print("TEST 1: process_batch() with 5 sample patient fundus images")
    print("=" * 65)

    sample_files = [
        "sample_images/patient_1_normal.png",
        "sample_images/patient_2_mild.png",
        "sample_images/patient_3_moderate.png",
        "sample_images/patient_4_severe.png",
        "sample_images/patient_5_pdr.png",
    ]

    for f in sample_files:
        assert Path(f).exists(), f"Sample file not found: {f}"

    results = process_batch(sample_files, language="en")
    assert len(results) == 5, f"Expected 5 results, got {len(results)}"

    print(f"  Processed {len(results)} patients successfully:")
    for idx, r in enumerate(results):
        print(f"    [{idx+1}] {r['patient_id']:<25} | {r['severity']:<30} | {r['urgency']:<40} | Conf: {r['confidence']}")
        assert "patient_id" in r
        assert "severity" in r
        assert "urgency" in r
        assert "confidence" in r
        assert "grade" in r

    print("  ✓ All required keys present in batch results dictionary!\n")

    print("=" * 65)
    print("TEST 2: Urgency-based sorting validation")
    print("=" * 65)

    # Verify sorting: grades must be in descending order (highest severity at top)
    grades = [r["grade"] for r in results]
    assert grades == sorted(grades, reverse=True), f"Results not sorted by urgency: {grades}"
    print(f"  Grades ordered by priority: {grades}")
    print(f"  Top case priority: {results[0]['severity']} ({results[0]['urgency']})")
    print("  ✓ Critical cases prioritized at the top of the table!\n")

    print("=" * 65)
    print("TEST 3: Dynamic camp summary calculation")
    print("=" * 65)

    summary = calculate_camp_summary(results, language="en")
    assert "patients screened" in summary, "Summary missing screened count"
    assert "flagged for referral" in summary, "Summary missing referral count"
    assert "5 patients screened" in summary, "Screened count should be 5"
    print(f"  Summary generated: '{summary}'")
    print("  ✓ Dynamic summary calculation verified!\n")

    print("=" * 65)
    print("TEST 4: pandas DataFrame generation")
    print("=" * 65)

    df = build_dataframe(results)
    expected_cols = ["Patient ID", "Severity", "Urgency Level", "Confidence"]
    assert list(df.columns) == expected_cols, f"Columns mismatch: {list(df.columns)}"
    assert len(df) == 5, f"Expected 5 rows in dataframe, got {len(df)}"
    print(f"  DataFrame columns: {list(df.columns)}")
    print("  Preview:\n" + str(df[["Patient ID", "Severity", "Confidence"]]))
    print("  ✓ DataFrame structure matches specification!\n")

    print("=" * 65)
    print("TEST 5: CSV Report Export & Integrity")
    print("=" * 65)

    out_csv = "test_batch_screening_report.csv"
    csv_path = export_batch_csv(results, output_path=out_csv)
    assert Path(csv_path).exists(), "CSV report was not created"
    assert os.path.getsize(csv_path) > 100, "CSV report is empty"

    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = list(csv.reader(f))
        headers = reader[0]
        data_rows = reader[1:]

    print(f"  CSV Header: {headers}")
    print(f"  CSV Data Rows count: {len(data_rows)}")
    assert len(data_rows) == 5, f"Expected 5 data rows in CSV, got {len(data_rows)}"
    assert "Patient ID" in headers[0]
    print(f"  ✓ CSV report generated and verified ({out_csv})!\n")

    print("=" * 65)
    print("TEST 6: Multi-Language Batch Execution (Hindi)")
    print("=" * 65)

    hi_results = process_batch(sample_files, language="hi")
    assert len(hi_results) == 5
    print(f"  Hindi Top Case: {hi_results[0]['urgency']}")
    # Assert Hindi Devanagari script is present
    has_hindi = any("डॉक्टर" in r["urgency"] or "रेफरल" in r["urgency"] or "कार्रवाई" in r["urgency"] for r in hi_results)
    assert has_hindi, "Hindi translations not found in batch output"
    print("=" * 65)
    print("TEST 7: Mixed Severity Priority Sorting & Referral Flagging")
    print("=" * 65)

    mixed_batch = [
        {"patient_id": "Patient A", "severity": "No DR (Grade 0)", "urgency": "🟢 No action needed", "urgency_raw": "No action needed", "confidence": "95.0%", "confidence_float": 0.95, "grade": 0, "action_timeline": "Annual"},
        {"patient_id": "Patient B", "severity": "Proliferative DR (Grade 4)", "urgency": "🚨 Immediate referral required", "urgency_raw": "Immediate referral required", "confidence": "88.0%", "confidence_float": 0.88, "grade": 4, "action_timeline": "Immediate"},
        {"patient_id": "Patient C", "severity": "Moderate NPDR (Grade 2)", "urgency": "🟠 See a doctor within 2 weeks", "urgency_raw": "See a doctor within 2 weeks", "confidence": "76.0%", "confidence_float": 0.76, "grade": 2, "action_timeline": "2 weeks"},
        {"patient_id": "Patient D", "severity": "Severe NPDR (Grade 3)", "urgency": "🔴 Urgent — see a doctor within 3 days", "urgency_raw": "Urgent — see a doctor within 3 days", "confidence": "82.0%", "confidence_float": 0.82, "grade": 3, "action_timeline": "3 days"},
    ]

    sorted_mixed = sorted(mixed_batch, key=lambda r: (r["grade"], r["confidence_float"]), reverse=True)
    sorted_grades = [r["grade"] for r in sorted_mixed]
    assert sorted_grades == [4, 3, 2, 0], f"Expected [4, 3, 2, 0], got {sorted_grades}"
    assert sorted_mixed[0]["patient_id"] == "Patient B", "Patient with Grade 4 should be first"

    mixed_summary = calculate_camp_summary(sorted_mixed)
    assert "4 patients screened — 3 flagged for referral" in mixed_summary
    print(f"  Mixed batch summary: '{mixed_summary}'")
    print(f"  Priority list: {[r['patient_id'] + ' (Grade ' + str(r['grade']) + ')' for r in sorted_mixed]}")
    print("  ✓ Priority sorting (Grade 4 -> 3 -> 2 -> 0) and referral counts verified!\n")


if __name__ == "__main__":
    test_batch_screening()
    print("=" * 65)
    print("ALL BATCH SCREENING TESTS PASSED!")
    print("=" * 65)
