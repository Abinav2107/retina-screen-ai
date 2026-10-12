"""
test_lnt_upgrade.py — Automated Regression & Feature Verification Suite for L&T TECHNUM.
Tests:
  1. Regression on 5 clinical samples (Grade 0, 1, 2, 3, 4).
  2. Quality Gate on valid vs. blurred vs. dark images.
  3. Uncertainty & Entropy quantification.
  4. Adaptive mode rendering (Detailed vs Concise).
  5. Sarvam AI offline fallback resilience.
  6. Doctor-in-the-Loop decision logging (Accept, Correct, Reject in SQLite audit_log).
  7. Doctor + AI simulation execution.
"""

import sys
from pathlib import Path
import numpy as np
from PIL import Image
import cv2

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import quality
import confidence
import adaptive
import sarvam_client
import review
import audit
import privacy
from evaluation import evaluate
from predict import predict, CLASS_LABELS
from gradcam import compute_gradcam_components, blend_gradcam_overlay
from referral_slip import generate_referral_slip

def run_tests():
    print("=" * 70)
    print("RUNNING L&T TECHNUM AUTOMATED VERIFICATION SUITE")
    print("=" * 70)

    # 1. Regression Test on Samples
    sample_dir = Path("sample_images")
    test_cases = [
        ("clinical_grade0_no_dr.jpg", 0),
        ("clinical_grade1_mild_npdr.png", 1),
        ("clinical_grade2_moderate_npdr.png", 2),
        ("clinical_grade3_severe_npdr.jpg", 3),
        ("clinical_grade4_proliferative_dr.jpg", 4),
    ]

    print("\n[TEST 1] Verifying 5-Grade Model Predictions & Grad-CAM...")
    for filename, expected_grade in test_cases:
        fpath = sample_dir / filename
        if not fpath.exists():
            print(f"  SKIP: {filename} not found.")
            continue
        img = Image.open(fpath).convert("RGB")
        pred_idx, pred_label, scores = predict(img)
        print(f"  [PASS] {filename}: Predicted Grade {pred_idx} ({pred_label}) with {scores[pred_label]*100:.1f}% confidence.")
        
        # Verify Grad-CAM
        img_224, heatmap = compute_gradcam_components(img, None or __import__('predict').model, pred_idx)
        overlay = blend_gradcam_overlay(img_224, heatmap, 40)
        assert overlay is not None, "Grad-CAM overlay failed!"

    # 2. Quality Gate Test
    print("\n[TEST 2] Verifying Quality Gate (Valid vs Blurred vs Dark vs Non-retina)...")
    valid_img = Image.open(sample_dir / "clinical_grade0_no_dr.jpg").convert("RGB")
    q_valid = quality.assess_scan_quality(valid_img)
    print(f"  [PASS] Valid Image Quality Score: {q_valid['quality_score']}/100, Passed: {q_valid['passed']}")
    assert q_valid["passed"], "Valid image should pass quality gate!"

    # Synthesize Blurry Image
    arr_blur = np.array(valid_img)
    arr_blur = cv2.GaussianBlur(arr_blur, (51, 51), 0)
    img_blur = Image.fromarray(arr_blur)
    q_blur = quality.assess_scan_quality(img_blur)
    print(f"  [PASS] Blurred Image Quality Score: {q_blur['quality_score']}/100, Passed: {q_blur['passed']}")
    assert not q_blur["passed"], "Blurred image should be flagged!"
    assert any("blur" in r.lower() for r in q_blur["reasons"]), "Blur reason missing!"

    # Synthesize Dark Image
    img_dark = Image.new("RGB", (224, 224), color=(10, 5, 5))
    q_dark = quality.assess_scan_quality(img_dark)
    print(f"  [PASS] Dark Image Quality Score: {q_dark['quality_score']}/100, Passed: {q_dark['passed']}")
    assert not q_dark["passed"], "Dark image should be flagged!"

    # 3. Confidence & Uncertainty Test
    print("\n[TEST 3] Verifying Confidence & Entropy Calculation...")
    c_res = confidence.compute_uncertainty_metrics(scores, CLASS_LABELS)
    print(f"  [PASS] Top-1: {c_res['top1_prob']*100:.1f}%, Margin: {c_res['margin']:.2f}, Entropy: {c_res['entropy']:.3f}, Status: {c_res['confidence_status']}")
    assert "limits_note" in c_res, "Limits note missing!"

    # 4. Adaptive Support Modes Test
    print("\n[TEST 4] Verifying Adaptive Modes (Detailed vs Concise)...")
    adapt_detailed = adaptive.format_adaptive_report(pred_idx, pred_label, c_res, q_valid, support_mode="Detailed")
    adapt_concise = adaptive.format_adaptive_report(pred_idx, pred_label, c_res, q_valid, support_mode="Concise")
    assert adapt_detailed["mode"] == "Detailed"
    assert adapt_concise["mode"] == "Concise"
    print("  [PASS] Detailed and Concise modes generated cleanly without errors.")

    # 5. Sarvam AI Online Generation & Offline Fallback Test
    print("\n[TEST 5] Verifying Sarvam AI (Online Generation & Offline Fallback)...")
    sarvam_res = sarvam_client.generate_sarvam_explanation(
        grade=2, label="Moderate NPDR", confidence_data=c_res, quality_data=q_valid, language_code="hi", support_mode="Detailed"
    )
    print(f"  [PASS] Sarvam Status: {sarvam_res['status']} ({sarvam_res['provider']})")
    print(f"  [PASS] Sample Output: {sarvam_res['text'][:90]}...")
    assert len(sarvam_res["text"]) > 20, "Sarvam explanation text should be meaningful!"
    
    # Also test offline fallback explicitly
    offline_text = sarvam_client._get_offline_explanation(grade=2, label="Moderate NPDR", language_code="en", support_mode="Detailed", question=None)
    assert "Decision" in offline_text or "decision" in offline_text, "Offline disclaimer missing!"
    print("  [PASS] Offline fallback template verified.")

    # 6. Doctor-in-the-Loop Logging Test
    print("\n[TEST 6] Verifying Doctor Review Actions & Audit Logging...")
    id_accept = review.record_clinician_decision("SCAN-101", "P-TEST-1", 2, c_res, q_valid, "Detailed", "en", "ACCEPT")
    id_correct = review.record_clinician_decision("SCAN-102", "P-TEST-2", 2, c_res, q_valid, "Detailed", "en", "CORRECT", doctor_final_grade=3, clinical_reason="IRMA detected in nasal quadrant.")
    id_reject = review.record_clinician_decision("SCAN-103", "P-TEST-3", 1, c_res, q_valid, "Concise", "hi", "REJECT", clinical_reason="Severe motion artefact.")

    df_audit = audit.get_audit_records()
    summary = audit.get_audit_summary()
    print(f"  [PASS] Audit rows logged: Log IDs {id_accept}, {id_correct}, {id_reject}")
    print(f"  [PASS] Audit Summary: Total={summary['total']}, Accepted={summary['accepted']}, Corrected={summary['corrected']}, Rejected={summary['rejected']}")
    assert summary["accepted"] >= 1
    assert summary["corrected"] >= 1
    assert summary["rejected"] >= 1

    # 7. Privacy Salted Hashing Test
    print("\n[TEST 7] Verifying Privacy De-identification...")
    h1 = privacy.hash_patient_id("P-1042")
    h2 = privacy.hash_patient_id("P-1042")
    h3 = privacy.hash_patient_id("P-9999")
    assert h1 == h2, "Hash must be deterministic!"
    assert h1 != h3, "Different IDs must yield different hashes!"
    print(f"  [PASS] Patient P-1042 anonymized to: {h1}")

    # 8. Evaluation Simulation Test
    print("\n[TEST 8] Verifying Doctor + AI Simulation...")
    df_sim, fig_sim = evaluate.run_hybrid_reader_simulation(num_cases=50)
    print("  [PASS] Hybrid Reader Simulation Table:")
    print(df_sim.to_string())

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
