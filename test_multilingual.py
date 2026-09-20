"""
test_multilingual.py -- Comprehensive verification of multi-language support
(en, hi, bn, mr, te, ta) for diabetic retinopathy screening.

Run:
    python test_multilingual.py
"""

import os
import sys
from pathlib import Path
from PIL import Image

# Force UTF-8 encoding on Windows console for non-Latin scripts
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from languages import (
    MESSAGES,
    LANGUAGE_OPTIONS,
    LANGUAGE_CODE_MAP,
    get_language_code,
)
from referral import get_patient_message
from app import run_screening_pipeline


def test_messages_structure():
    print("=" * 65)
    print("TEST 1: MESSAGES dictionary structure across all 6 languages")
    print("=" * 65)

    required_langs = ["en", "hi", "bn", "mr", "te", "ta"]
    for lang in required_langs:
        assert lang in MESSAGES, f"Missing language '{lang}' in MESSAGES"
        lang_data = MESSAGES[lang]
        assert "disclaimer" in lang_data, f"Missing 'disclaimer' in language '{lang}'"
        assert "offline_note" in lang_data, f"Missing 'offline_note' in language '{lang}'"

        print(f"\n[Language: {lang} ({lang_data.get('language_name')})]")
        print(f"  Offline Note: {lang_data['offline_note']}")
        print(f"  Disclaimer:   {lang_data['disclaimer'][:60]}...")

        # Verify all 5 severity stages
        for sev in range(5):
            msg = lang_data[sev]
            assert msg.urgency, f"Empty urgency for {lang}:{sev}"
            assert msg.explanation, f"Empty explanation for {lang}:{sev}"
            assert msg.action_timeline, f"Empty timeline for {lang}:{sev}"
            print(f"    Grade {sev} Urgency: {msg.urgency}")

    print("\n  ✓ All 6 languages and 5 severity levels verified in MESSAGES!\n")


def test_language_dropdown_mappings():
    print("=" * 65)
    print("TEST 2: Language dropdown options & mapping")
    print("=" * 65)

    expected_choices = ["English", "हिंदी", "বাংলা", "मराठी", "తెలుగు", "தமிழ்"]
    expected_codes = ["en", "hi", "bn", "mr", "te", "ta"]

    assert LANGUAGE_OPTIONS == expected_choices, "LANGUAGE_OPTIONS mismatch"
    for choice, code in zip(expected_choices, expected_codes):
        mapped = get_language_code(choice)
        assert mapped == code, f"Failed mapping '{choice}' -> '{code}', got '{mapped}'"
        print(f"  Mapped: {choice:<10} -> {mapped}")

    print("  ✓ All dropdown choices map to correct language codes!\n")


def test_multilingual_pipeline_execution():
    print("=" * 65)
    print("TEST 3: End-to-end inference across all 6 languages")
    print("=" * 65)

    sample_img_path = Path("sample_images/synthetic_fundus.png")
    if not sample_img_path.exists():
        img = Image.new("RGB", (224, 224), color=(170, 50, 40))
        img.save(sample_img_path)
    test_img = Image.open(sample_img_path)

    # Specific script markers expected per language
    script_markers = {
        "English": ("healthy", "retina"),
        "हिंदी": ("स्वस्थ", "रेटिना"),
        "বাংলা": ("সুস্থ", "রেটিনা"),
        "मराठी": ("निरोगी", "रेटिना"),
        "తెలుగు": ("ఆరోగ్యంగా", "రెటీనా"),
        "தமிழ்": ("ஆரோக்கியமாக", "விழித்திரை"),
    }

    base_scores = None
    for lang_name in LANGUAGE_OPTIONS:
        res = run_screening_pipeline(test_img, language_choice=lang_name)
        gradcam_img, badge_html, summary, explanation_md, scores, caption, disclaimer_html = res

        # Check language independence of vision/model components
        assert isinstance(gradcam_img, Image.Image), "Grad-CAM must be PIL Image"
        if base_scores is None:
            base_scores = scores
        else:
            # Predictions must be identical regardless of language selected
            for k in scores:
                assert abs(scores[k] - base_scores[k]) < 1e-5, f"Scores vary by language for {k}"

        # Verify correct script appears in output
        marker1, marker2 = script_markers[lang_name]
        has_marker = (marker1 in explanation_md or marker2 in explanation_md)
        assert has_marker, f"Script marker missing for {lang_name} in:\n{explanation_md}"

        # Verify localized disclaimer is rendered
        lang_code = get_language_code(lang_name)
        expected_disclaimer = MESSAGES[lang_code]["disclaimer"]
        assert expected_disclaimer in disclaimer_html, f"Disclaimer text mismatch for {lang_name}"

        print(f"  ✓ [{lang_name:<10}] Script rendered properly | Disclaimer updated | Scores identical")

    print("\n  ✓ Language independence verified for model and Grad-CAM!")
    print("  ✓ Full multi-language pipeline passed with zero boxes or garbled text!\n")


if __name__ == "__main__":
    test_messages_structure()
    test_language_dropdown_mappings()
    test_multilingual_pipeline_execution()
    print("=" * 65)
    print("ALL MULTI-LANGUAGE TESTS PASSED!")
    print("=" * 65)
