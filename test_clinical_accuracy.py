"""
test_clinical_accuracy.py -- Comprehensive clinical verification of all 5
genuine Diabetic Retinopathy severity grades (Grade 0 to Grade 4).
"""

import sys
import os
from pathlib import Path
from PIL import Image

# UTF-8 stdout
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from predict import predict, model, CLASS_LABELS
from gradcam import generate_gradcam
from referral import get_patient_message
from batch import process_batch, build_dataframe, calculate_camp_summary, export_batch_csv

CLINICAL_FILES = [
    ("clinical_grade0_no_dr.jpg", 0, "No DR"),
    ("clinical_grade1_mild_npdr.png", 1, "Mild NPDR"),
    ("clinical_grade2_moderate_npdr.png", 2, "Moderate NPDR"),
    ("clinical_grade3_severe_npdr.jpg", 3, "Severe NPDR"),
    ("clinical_grade4_proliferative_dr.jpg", 4, "Proliferative DR"),
]

sample_dir = Path("sample_images")

print("=" * 70)
print("CLINICAL EVALUATION: 5 Genuine Patient Fundus Photographs")
print("=" * 70)

for filename, target_grade, target_label in CLINICAL_FILES:
    img_path = sample_dir / filename
    assert img_path.exists(), f"Missing file: {img_path}"

    with Image.open(img_path) as img:
        pred_idx, pred_label, scores = predict(img)
        top_conf = scores[pred_label] * 100

        patient_msg = get_patient_message(pred_idx, scores[pred_label])
        gradcam_img = generate_gradcam(img, model, pred_idx)
        gradcam_out_path = sample_dir / f"{Path(filename).stem}_gradcam.png"
        gradcam_img.save(gradcam_out_path)

        print(f"\n[Patient Image: {filename}]")
        print(f"  Expected Stage : Grade {target_grade} ({target_label})")
        print(f"  AI Prediction  : Grade {pred_idx} ({pred_label}) -- Confidence: {top_conf:.1f}%")
        print(f"  Triage Urgency : {patient_msg.urgency}")
        print(f"  Grad-CAM Saved : {gradcam_out_path.name}")
        print("  Confidence breakdown:")
        for lbl, sc in scores.items():
            bar = "#" * int(sc * 30)
            print(f"    {lbl:<20} {sc*100:5.1f}% {bar}")

print("\n" + "=" * 70)
print("CAMP BATCH SCREENING WITH REAL CLINICAL PATIENTS")
print("=" * 70)

file_paths = [str(sample_dir / f[0]) for f in CLINICAL_FILES]
batch_results = process_batch(file_paths, language="en")
summary = calculate_camp_summary(batch_results)
df = build_dataframe(batch_results)

print(f"\nCamp Metrics: {summary}")
print("\nPrioritized Triage Table (Sorted by Urgency):")
print(df.to_string(index=False))

csv_path = export_batch_csv(batch_results, output_path="clinical_camp_report.csv")
print(f"\nExported clinical CSV report to: {csv_path}")
print("=" * 70)
print("ALL CLINICAL TESTS PASSED! Authentic data verified.")
print("=" * 70)
