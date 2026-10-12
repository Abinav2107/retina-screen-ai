"""
test_i18n.py — Automated verification suite for NetraScreen AI Full-UI Localization (i18n).
Tests:
  1. Complete translation dictionary integrity across all 6 languages (en, hi, bn, mr, te, ta).
  2. Safe fallback to English for non-existent keys.
  3. Dynamic string interpolation (e.g. {count}, {id}, {score}).
  4. Localize dataframe functionality without in-place mutation.
  5. UI widget key presence and consistency.
"""

import sys
from pathlib import Path
import pandas as pd

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))
import i18n
from i18n import t

def test_dictionary_integrity():
    print("[TEST 1] Checking translation key parity across all 6 languages...")
    en_keys = set(i18n.TRANSLATIONS["en"].keys())
    for lang in ["hi", "bn", "mr", "te", "ta"]:
        lang_keys = set(i18n.TRANSLATIONS[lang].keys())
        missing = en_keys - lang_keys
        assert len(missing) == 0, f"Language {lang} is missing keys: {missing}"
        print(f"  [PASS] {lang}: {len(lang_keys)} keys mapped (0 missing).")

def test_safe_fallback():
    print("[TEST 2] Checking safe fallback to English on missing/unknown keys...")
    fallback_res = t("non_existent_key_xyz", lang="hi")
    assert fallback_res == "non_existent_key_xyz", f"Expected key fallback, got: {fallback_res}"
    print("  [PASS] Missing key safely returned fallback without crashing.")

def test_string_interpolation():
    print("[TEST 3] Checking parameter interpolation ({count}, {id}, {score})...")
    for lang in ["en", "hi", "bn", "mr", "te", "ta"]:
        res_count = t("msg_batch_complete", lang=lang, count=15)
        assert "15" in res_count, f"Failed interpolation for {lang}: {res_count}"
        
        res_id = t("msg_analysis_complete", lang=lang, id=42)
        assert "42" in res_id, f"Failed ID interpolation for {lang}: {res_id}"
    print("  [PASS] String interpolation verified across all 6 languages.")

def test_dataframe_localization():
    print("[TEST 4] Checking DataFrame localization and immutability...")
    df_orig = pd.DataFrame([
        {"Rec #": 1, "Patient ID": "P-1042", "Full Name": "Ramesh Kumar", "Severity Stage": "Grade 0: No DR", "Triage Urgency": "Normal (Grade 0)"}
    ])
    
    # Localize to Hindi
    df_hi = i18n.localize_dataframe(df_orig, table_type="patients", lang="hi")
    assert "रिकॉर्ड #" in df_hi.columns or "\u0930\u093f\u0915\u0949\u0930\u094d\u0921 #" in df_hi.columns
    assert "Rec #" in df_orig.columns, "Original DataFrame columns were mutated!"
    
    # Localize to Tamil
    df_ta = i18n.localize_dataframe(df_orig, table_type="patients", lang="ta")
    assert df_ta.columns[0] == t("tbl_col_rec", "ta")
    assert "Rec #" in df_orig.columns, "Original DataFrame columns were mutated!"

    # Localize batch table
    df_batch = pd.DataFrame([{"Filename": "test.jpg", "Assigned ID": "CAMP-001", "Grade": 0, "Severity": "No DR", "Confidence": "98%", "Triage Urgency": "Normal"}])
    df_batch_bn = i18n.localize_dataframe(df_batch, table_type="batch", lang="bn")
    assert df_batch_bn.columns[0] == t("batch_col_filename", "bn")
    assert "Filename" in df_batch.columns, "Original batch columns were mutated!"
    print("  [PASS] DataFrame localization correctly localized headers while preserving original dataframes.")

def test_widget_keys_in_streamlit():
    print("[TEST 5] Checking widget key preservation in streamlit_app.py...")
    app_code = Path("streamlit_app.py").read_text(encoding="utf-8")
    
    mandatory_keys = [
        'key="global_language_selector"',
        'key="support_style_selector"',
        'key="show_evidence_checkbox"',
        'key="save_scan_opt_in_cb"',
        'key="search_input"',
        'key="urgency_filter"',
        'key="btn_refresh_registry"',
        'key="p_id_input"',
        'key="p_name_input"',
        'key="p_age_input"',
        'key="p_gender_input"',
        'key="p_eye_input"',
        'key="p_contact_input"',
        'key="p_duration_input"',
        'key="p_sugar_input"',
        'key="p_hypertension_input"',
        'key="fundus_uploader"',
        'key="btn_screen_patient"',
        'key="acc_notes"',
        'key="btn_accept_act"',
        'key="corr_grade_sel"',
        'key="corr_notes"',
        'key="btn_correct_act"',
        'key="rej_notes"',
        'key="btn_reject_act"',
        'key="btn_dl_referral_slip"',
        'key="batch_files_uploader"',
        'key="btn_run_batch_screening"',
        'key="btn_dl_batch_csv"',
        'key="audit_filter_sb"',
        'key="btn_refresh_audit_log"',
        'key="btn_dl_audit_csv"',
        'key="btn_run_simulation_act"',
    ]
    
    for k in mandatory_keys:
        assert k in app_code, f"Missing required widget key: {k}"
    print(f"  [PASS] All {len(mandatory_keys)} fixed English widget keys confirmed present.")

if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING NETRASCREEN AI i18n LOCALIZATION VERIFICATION")
    print("=" * 60)
    test_dictionary_integrity()
    test_safe_fallback()
    test_string_interpolation()
    test_dataframe_localization()
    test_widget_keys_in_streamlit()
    print("=" * 60)
    print("ALL i18n LOCALIZATION TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)
