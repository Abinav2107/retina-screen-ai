"""
test_referral.py -- Comprehensive verification for referral triage,
patient messaging, and the full end-to-end screening pipeline.

Run:
    python test_referral.py
"""

import os
import sys
from pathlib import Path
from PIL import Image

# Force UTF-8 encoding on Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from referral import get_patient_message, PATIENT_GUIDANCE, PatientMessage
from app import run_screening_pipeline, OFFLINE_RURAL_NOTE, DISCLAIMER_NOTE


def test_referral_messages():
    print("=" * 65)
    print("TEST 1: get_patient_message() mapping and structure across all 5 classes")
    print("=" * 65)

    expected_urgencies = {
        0: "No action needed",
        1: "Routine checkup recommended within 6 months",
        2: "See a doctor within 2 weeks",
        3: "Urgent — see a doctor within 3 days",
        4: "Immediate referral required — risk of vision loss",
    }

    expected_colors = {
        0: "green",
        1: "yellow",
        2: "orange",
        3: "red",
        4: "red",
    }

    for grade in range(5):
        msg = get_patient_message(grade, 0.85)

        # Check tuple unpacking
        explanation, urgency = get_patient_message(grade, 0.85)
        assert explanation == msg.explanation, f"Tuple unpacking failed for grade {grade}"
        assert urgency == msg.urgency, f"Tuple unpacking failed for grade {grade}"

        # Check dict access
        assert msg["explanation"] == msg.explanation
        assert msg["urgency"] == msg.urgency
        assert msg["color"] == expected_colors[grade]
        assert msg.urgency == expected_urgencies[grade], (
            f"Grade {grade} urgency mismatch: expected '{expected_urgencies[grade]}', got '{msg.urgency}'"
        )
        assert len(msg.badge_html) > 50, "Badge HTML should not be empty"

        print(f"  [Grade {grade}] Color: {msg['color']:<6} | Urgency: {msg.urgency}")
        print(f"             Explanation: {msg.explanation[:70]}...")

    # Check string input handling
    str_test = get_patient_message("Moderate NPDR", 0.75)
    assert str_test.urgency == "See a doctor within 2 weeks", "String conversion failed"
    print("\n  ✓ String class name input handled correctly: 'Moderate NPDR' -> Grade 2")
    print("  ✓ All 5 severity class mappings verified successfully!\n")


def test_disclaimer_and_offline_notes():
    print("=" * 65)
    print("TEST 2: Offline / low-bandwidth framing & Medical disclaimer text")
    print("=" * 65)

    required_offline_phrase = "This tool runs locally and does not require continuous internet access"
    required_disclaimer_phrase = "This is a screening aid, not a medical diagnosis. All flagged cases should be confirmed by a qualified ophthalmologist."

    assert required_offline_phrase in OFFLINE_RURAL_NOTE, "Offline rural note missing required text"
    assert required_disclaimer_phrase in DISCLAIMER_NOTE, "Disclaimer note missing required text"

    print(f"  ✓ Offline low-connectivity note present: '{required_offline_phrase[:55]}...'")
    print(f"  ✓ Medical disclaimer present: '{required_disclaimer_phrase[:55]}...'")
    print("  ✓ UI framing verified successfully!\n")


def test_full_pipeline():
    print("=" * 65)
    print("TEST 3: Full end-to-end pipeline execution (Image -> Prediction -> Grad-CAM -> Triage)")
    print("=" * 65)

    sample_img_path = Path("sample_images/synthetic_fundus.png")
    if not sample_img_path.exists():
        # Create fallback test image
        img = Image.new("RGB", (224, 224), color=(170, 50, 40))
        img.save(sample_img_path)

    test_img = Image.open(sample_img_path)
    print(f"  Running full pipeline on {sample_img_path} ...")

    result = run_screening_pipeline(test_img)
    gradcam_img, badge_html, summary, explanation_md, scores, caption, *rest = result

    assert isinstance(gradcam_img, Image.Image), "Grad-CAM output must be a PIL Image"
    assert gradcam_img.size == (224, 224), f"Expected 224x224 Grad-CAM overlay, got {gradcam_img.size}"
    assert "RECOMMENDED ACTION TIMELINE" in badge_html, "Urgency badge missing header"
    assert ("Predicted Severity" in summary or "Stage" in summary), "Summary missing prediction text"
    assert len(scores) == 5, f"Expected 5 confidence scores, got {len(scores)}"
    assert len(caption) > 10, "Caption should not be empty"

    print("  ✓ Grad-CAM Image generated successfully (224x224 overlay)")
    print("  ✓ Urgency badge HTML generated with high-contrast color scheme")
    print(f"  ✓ Clinical Summary: {summary.replace(chr(10), ' | ')}")
    print(f"  ✓ Caption: {caption[:60]}...")
    print("  ✓ Full pipeline executed successfully!\n")


if __name__ == "__main__":
    test_referral_messages()
    test_disclaimer_and_offline_notes()
    test_full_pipeline()
    print("=" * 65)
    print("ALL TESTS PASSED! Project is ready for demo.")
    print("=" * 65)
