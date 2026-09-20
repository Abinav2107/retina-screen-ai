"""
batch.py -- Camp Mode: Batch screening processor and triage report generator
for rural health camps and mass screening sessions.
"""

import os
import csv
import pandas as pd
from typing import List, Dict, Any, Union
from pathlib import Path
from PIL import Image

from predict import predict, CLASS_LABELS
from languages import MESSAGES, get_language_code
from referral import get_patient_message


# ------------------------------------------------------------------
# Batch Processor
# ------------------------------------------------------------------
def _load_image(img_input: Any) -> Image.Image:
    """Load image whether passed as file path string, file object, or PIL Image."""
    if isinstance(img_input, Image.Image):
        return img_input
    if isinstance(img_input, (str, Path)):
        return Image.open(str(img_input))
    if hasattr(img_input, "name") and isinstance(img_input.name, str):
        # Gradio UploadedFile or NamedTemporaryFile
        return Image.open(img_input.name)
    if hasattr(img_input, "path") and isinstance(img_input.path, str):
        return Image.open(img_input.path)
    raise ValueError(f"Unsupported image input type: {type(img_input)}")


def _get_filename_id(img_input: Any, index: int) -> str:
    """Derive a friendly patient ID using the file name or patient index."""
    name = None
    if isinstance(img_input, (str, Path)):
        name = Path(img_input).stem
    elif hasattr(img_input, "name") and isinstance(img_input.name, str):
        name = Path(img_input.name).stem
    elif hasattr(img_input, "path") and isinstance(img_input.path, str):
        name = Path(img_input.path).stem

    # Filter out random temporary file hashes (e.g. Gradio temp files like /tmp/abc1234/xyz.png)
    if name and not name.startswith("tmp") and len(name) < 25 and not name.isalnum():
        return f"Patient {index+1} ({name})"
    return f"Patient {index+1}"


def process_batch(
    image_list: List[Any],
    language: str = "en",
) -> List[Dict[str, Any]]:
    """
    Runs each fundus image through the EfficientNetB0 classification pipeline.
    (Grad-CAM is skipped during mass screening for ultra-fast throughput).

    Parameters
    ----------
    image_list : list
        List of image filepaths, file objects, or PIL Images.
    language : str
        Language code or display name for localized urgency text.

    Returns
    -------
    list of dict
        [{"patient_id": "Patient 1", "severity": "...", "urgency": "...", "confidence": "..."}]
        Sorted by urgency descending so critical cases (Proliferative DR, Severe NPDR) appear at the top.
    """
    if not image_list:
        return []

    lang_code = get_language_code(language)
    raw_results = []

    for idx, item in enumerate(image_list):
        try:
            img = _load_image(item)
            pred_idx, pred_label, scores = predict(img)
            conf_val = scores[pred_label]

            # Get localized triage guidance
            patient_msg = get_patient_message(pred_idx, conf_val, language=lang_code)

            # Icon visual tag for immediate scanning
            urgency_icon = {
                0: "🟢",
                1: "🟡",
                2: "🟠",
                3: "🔴",
                4: "🚨",
            }.get(pred_idx, "⚪")

            patient_id = _get_filename_id(item, idx)
            urgency_text = f"{urgency_icon} {patient_msg.urgency}"

            raw_results.append({
                "patient_id": patient_id,
                "severity": f"{pred_label} (Grade {pred_idx})",
                "severity_name": patient_msg.severity_name,
                "urgency": urgency_text,
                "urgency_raw": patient_msg.urgency,
                "confidence": f"{conf_val * 100:.1f}%",
                "confidence_float": conf_val,
                "grade": pred_idx,
                "action_timeline": patient_msg.action_timeline,
            })
        except Exception as err:
            print(f"[batch.py] Error processing image {idx+1}: {err}")
            raw_results.append({
                "patient_id": f"Patient {idx+1} (Error)",
                "severity": "Processing Failed",
                "severity_name": "Error",
                "urgency": "⚠️ Retest Required",
                "urgency_raw": "Retest Required",
                "confidence": "N/A",
                "confidence_float": 0.0,
                "grade": -1,
                "action_timeline": "Retake photo",
            })

    # Sort primarily by severity grade descending (Grade 4 first, Grade 0 last),
    # secondarily by confidence descending
    sorted_results = sorted(
        raw_results,
        key=lambda r: (r["grade"], r["confidence_float"]),
        reverse=True,
    )

    return sorted_results


def build_dataframe(batch_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """Build a pandas DataFrame with standard columns for the Gradio interface."""
    if not batch_results:
        return pd.DataFrame(columns=["Patient ID", "Severity", "Urgency Level", "Confidence"])

    rows = []
    for r in batch_results:
        rows.append({
            "Patient ID": r["patient_id"],
            "Severity": r["severity"],
            "Urgency Level": r["urgency"],
            "Confidence": r["confidence"],
        })

    return pd.DataFrame(rows)


def calculate_camp_summary(batch_results: List[Dict[str, Any]], language: str = "en") -> str:
    """
    Calculate dynamic summary: 'X patients screened — Y flagged for referral'
    Flagged cases are those with detected DR (Grade >= 1).
    """
    total = len(batch_results)
    if total == 0:
        return "No patients screened yet."

    # Patients with retinopathy (Grade 1-4) need doctor checkup/referral
    flagged = sum(1 for r in batch_results if r["grade"] > 0)
    urgent_referrals = sum(1 for r in batch_results if r["grade"] >= 3)

    urgent_note = f" (🚨 {urgent_referrals} urgent / sight-threatening)" if urgent_referrals > 0 else ""

    return f"{total} patients screened — {flagged} flagged for referral{urgent_note}"


def export_batch_csv(batch_results: List[Dict[str, Any]], output_path: str = "batch_screening_report.csv") -> str:
    """
    Export batch results to a CSV report suitable for health center records.
    Returns the absolute path to the generated CSV.
    """
    out_file = Path(output_path).resolve()

    fieldnames = [
        "Patient ID",
        "Severity Grade",
        "Clinical Classification",
        "Urgency Level",
        "Action Timeline",
        "Confidence Score",
    ]

    with open(out_file, mode="w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for r in batch_results:
            writer.writerow({
                "Patient ID": r["patient_id"],
                "Severity Grade": r["grade"] if r["grade"] >= 0 else "Error",
                "Clinical Classification": r["severity"],
                "Urgency Level": r["urgency_raw"],
                "Action Timeline": r.get("action_timeline", ""),
                "Confidence Score": r["confidence"],
            })

    print(f"[batch.py] Report exported to: {out_file}")
    return str(out_file)
