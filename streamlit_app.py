"""
streamlit_app.py — Official Streamlit Cloud Web Application for NetraScreen AI.
Diabetic Retinopathy Clinical Screening Dashboard & Tele-Ophthalmology Triage Unit.

Features:
  - Tab 1: 📊 Clinical Screening Dashboard & Registry (Live KPIs, charts, searchable registry)
  - Tab 2: 👤 Patient Intake & Screening (Demographics, Fundus upload, Grad-CAM, QR Referral Slip)
  - Tab 3: 🏕️ Camp Mode — Rapid Batch Screening (Rural camp triage & CSV export)
  - Tab 4: 📜 Compliance Audit Trail & Clinician Decision Registry
  - Tab 5: 📈 Doctor + AI Evaluation & Hybrid Reader Simulation
"""

import os
import io
import time
from pathlib import Path
from PIL import Image
import pandas as pd
import streamlit as st

# Suppress TF / Hugging Face verbose logs
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# Import existing backend modules (100% untouched)
from predict import predict, CLASS_LABELS
from gradcam import (
    generate_gradcam,
    get_caption,
    compute_gradcam_components,
    blend_gradcam_overlay,
)
from languages import (
    MESSAGES,
    LANGUAGE_OPTIONS,
    LANGUAGE_CODE_MAP,
    get_language_code,
)
from referral import get_patient_message
from referral_slip import generate_referral_slip
from batch import process_batch, build_dataframe, calculate_camp_summary, export_batch_csv
import database

# --- L&T UPGRADE: Clinical Decision Support & Governance Modules ---
import quality
import confidence
import adaptive
import sarvam_client
import review
import audit
import privacy
from evaluation import evaluate
# --- END L&T UPGRADE ---

# --- i18n: Localization & Indic Font Engine ---
import i18n  # --- i18n ---
from i18n import t  # --- i18n ---
# --- end i18n ---

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NetraScreen — Clinical Screening Dashboard",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Clean Medical Theme Styling + Indic Font Fallback Stack
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .kpi-title { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { font-size: 28px; font-weight: 800; color: #0f172a; margin-top: 4px; }
    .stTabs [data-baseweb="tab-list"] { gap: 12px; border-bottom: 2px solid #e2e8f0; }
    .stTabs [data-baseweb="tab"] { font-size: 15px; font-weight: 600; padding: 10px 16px; color: #475569; }
    .stTabs [aria-selected="true"] { color: #0d9488 !important; border-bottom: 3px solid #0d9488 !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)
st.markdown(i18n.get_css_font_stack(), unsafe_allow_html=True)  # --- i18n ---

# Initialize global active language
if "lang" not in st.session_state:  # --- i18n ---
    st.session_state["lang"] = "en"  # --- i18n ---

# -----------------------------------------------------------------------------
# Sidebar Configuration
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(t("sidebar_title"))  # --- i18n ---
    st.caption(t("sidebar_caption"))  # --- i18n ---
    st.divider()

    # Regional Language Selector (Global Full-UI Switcher)
    st.markdown(t("sidebar_lang_heading"))  # --- i18n ---
    curr_lang = st.session_state.get("lang", "en")  # --- i18n ---
    curr_lang_name = i18n.CODE_TO_LANGUAGE_MAP.get(curr_lang, "English")  # --- i18n ---
    try:  # --- i18n ---
        lang_idx = i18n.LANGUAGE_OPTIONS.index(curr_lang_name)  # --- i18n ---
    except ValueError:  # --- i18n ---
        lang_idx = 0  # --- i18n ---

    def on_language_change():  # --- i18n ---
        sel = st.session_state.get("global_language_selector", "English")  # --- i18n ---
        st.session_state["lang"] = i18n.LANGUAGE_CODE_MAP.get(sel, "en")  # --- i18n ---

    selected_lang_name = st.selectbox(
        "Language / भाषा",  # --- i18n ---
        options=i18n.LANGUAGE_OPTIONS,  # --- i18n ---
        index=lang_idx,  # --- i18n ---
        key="global_language_selector",  # --- i18n ---
        on_change=on_language_change,  # --- i18n ---
        label_visibility="collapsed",  # --- i18n ---
    )  # --- i18n ---
    lang_code = i18n.LANGUAGE_CODE_MAP.get(selected_lang_name, "en")  # --- i18n ---
    st.session_state["lang"] = lang_code  # --- i18n ---
    lang_dict = MESSAGES.get(lang_code, MESSAGES["en"])

    st.divider()

    # HackDay Presentation & PDF Downloads
    st.markdown(t("sidebar_deliverables_heading"))  # --- i18n ---
    pptx_path = Path("NetraScreen_HackDay_Presentation.pptx")
    if pptx_path.exists():
        with open(pptx_path, "rb") as f:
            st.download_button(
                label=t("btn_download_ppt"),  # --- i18n ---
                data=f.read(),
                file_name="NetraScreen_HackDay_Presentation.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
                key="btn_dl_ppt",  # --- i18n ---
            )

    pdf_path = Path("NetraScreen_Hackathon_Final_Review.pdf")
    if pdf_path.exists():
        with open(pdf_path, "rb") as f:
            st.download_button(
                label=t("btn_download_pdf"),  # --- i18n ---
                data=f.read(),
                file_name="NetraScreen_Hackathon_Final_Review.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="btn_dl_pdf",  # --- i18n ---
            )

    st.link_button(t("btn_github_repo"), "https://github.com/Abinav2107/retina-screen-ai", use_container_width=True)  # --- i18n ---

    st.divider()
    st.info(f"**{t('sidebar_rural_ready_title')}**\n{t('sidebar_rural_ready_desc')}")  # --- i18n ---

    # --- L&T UPGRADE: Adaptive Clinical Controls & Privacy ---
    st.divider()
    st.markdown(t("sidebar_adaptive_heading"))  # --- i18n ---
    support_style = st.selectbox(
        t("lbl_support_style"),  # --- i18n ---
        options=["Detailed", "Concise"],
        index=0,
        format_func=lambda x: t("opt_style_detailed") if x == "Detailed" else t("opt_style_concise"),  # --- i18n ---
        help=t("help_support_style"),  # --- i18n ---
        key="support_style_selector",
    )
    show_evidence = st.checkbox(
        t("lbl_show_evidence"),  # --- i18n ---
        value=True,
        help=t("help_show_evidence"),  # --- i18n ---
        key="show_evidence_checkbox",
    )
    save_scan_opt_in = st.checkbox(
        t("lbl_save_scan_opt_in"),  # --- i18n ---
        value=False,
        help=t("help_save_scan"),  # --- i18n ---
        key="save_scan_opt_in_cb",
    )

    st.divider()
    st.markdown(t("sidebar_genai_heading"))  # --- i18n ---
    if sarvam_client.is_sarvam_online():
        st.success(t("badge_sarvam_online"))  # --- i18n ---
    else:
        st.info(t("badge_sarvam_offline"))  # --- i18n ---

    with st.expander(t("expander_privacy")):  # --- i18n ---
        st.markdown(privacy.PRIVACY_MANIFESTO)
    # --- END L&T UPGRADE ---

# -----------------------------------------------------------------------------
# Main Header & Rural Clinic Banner
# -----------------------------------------------------------------------------
st.title(t("header_title"))  # --- i18n ---
st.markdown(t("header_subtitle"))  # --- i18n ---

# Clinic Banner
st.markdown(f"""
<div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 10px 14px; margin-bottom: 16px;">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
        <div>
            <span style="color: #166534; font-size: 13px; font-weight: 700;">{t("banner_health_centre")}</span>
            <span style="color: #86efac; margin: 0 8px;">•</span>
            <span style="color: #15803d; font-size: 13px; font-weight: 600;">{t("banner_camp_id")}</span>
        </div>
        <div style="font-size: 12px; color: #166534; font-weight: 600;">
            {t("banner_cloud_status")}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)  # --- i18n ---

# -----------------------------------------------------------------------------
# Session State for Intake Screening Cache
# -----------------------------------------------------------------------------
if "screening_result" not in st.session_state:
    st.session_state.screening_result = None

# -----------------------------------------------------------------------------
# TABS
# -----------------------------------------------------------------------------
tab_dash, tab_screen, tab_camp, tab_audit, tab_eval = st.tabs([
    t("tab_dashboard"),  # --- i18n ---
    t("tab_intake"),  # --- i18n ---
    t("tab_camp"),  # --- i18n ---
    t("tab_audit"),  # --- i18n ---
    t("tab_eval"),  # --- i18n ---
])

# =============================================================================
# TAB 1: DASHBOARD & REGISTRY
# =============================================================================
with tab_dash:
    st.subheader(t("dash_kpi_heading"))  # --- i18n ---
    kpis = database.get_dashboard_kpis()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 4px solid #3b82f6;">
            <div class="kpi-title">{t("kpi_total_title")}</div>
            <div class="kpi-value">{kpis['total']}</div>
            <div style="font-size: 11px; color: #3b82f6; font-weight: 600; margin-top: 4px;">{t("kpi_total_sub")}</div>
        </div>
        """, unsafe_allow_html=True)  # --- i18n ---

    with col2:
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 4px solid #10b981;">
            <div class="kpi-title">{t("kpi_normal_title")}</div>
            <div class="kpi-value">{kpis['normal']}</div>
            <div style="font-size: 11px; color: #10b981; font-weight: 600; margin-top: 4px;">{t("kpi_normal_sub")}</div>
        </div>
        """, unsafe_allow_html=True)  # --- i18n ---

    with col3:
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 4px solid #f59e0b;">
            <div class="kpi-title">{t("kpi_mild_mod_title")}</div>
            <div class="kpi-value">{kpis['mild_mod']}</div>
            <div style="font-size: 11px; color: #f59e0b; font-weight: 600; margin-top: 4px;">{t("kpi_mild_mod_sub")}</div>
        </div>
        """, unsafe_allow_html=True)  # --- i18n ---

    with col4:
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 4px solid #ef4444;">
            <div class="kpi-title">{t("kpi_urgent_title")}</div>
            <div class="kpi-value">{kpis['urgent']}</div>
            <div style="font-size: 11px; color: #ef4444; font-weight: 600; margin-top: 4px;">{t("kpi_urgent_sub")}</div>
        </div>
        """, unsafe_allow_html=True)  # --- i18n ---

    with col5:
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 4px solid #8b5cf6;">
            <div class="kpi-title">{t("kpi_prevalence_title")}</div>
            <div class="kpi-value">{kpis['referral_rate']:.1f}%</div>
            <div style="font-size: 11px; color: #8b5cf6; font-weight: 600; margin-top: 4px;">{t("kpi_prevalence_sub")}</div>
        </div>
        """, unsafe_allow_html=True)  # --- i18n ---

    st.write("")
    
    # Analytics Charts
    chart_col1, chart_col2 = st.columns(2)
    fig_dist, fig_age = database.generate_dashboard_charts()
    with chart_col1:
        st.pyplot(fig_dist)
    with chart_col2:
        st.pyplot(fig_age)

    st.divider()

    # Searchable Patient Registry Table
    st.subheader(t("dash_registry_heading"))  # --- i18n ---
    c1, c2, c3 = st.columns([3, 2, 1])
    with c1:
        search_q = st.text_input(t("lbl_search_patient"), placeholder=t("ph_search_patient"), key="search_input")  # --- i18n ---
    with c2:
        urgency_filter_map = {  # --- i18n ---
            "All": t("opt_urgency_all"),
            "🚨 Urgent / Immediate (Grades 3-4)": t("opt_urgency_urgent"),
            "🟡 Follow-up / Routine (Grades 1-2)": t("opt_urgency_routine"),
            "🟢 Normal (Grade 0)": t("opt_urgency_normal"),
        }
        urgency_filter = st.selectbox(
            t("lbl_filter_urgency"),  # --- i18n ---
            ["All", "🚨 Urgent / Immediate (Grades 3-4)", "🟡 Follow-up / Routine (Grades 1-2)", "🟢 Normal (Grade 0)"],
            format_func=lambda x: urgency_filter_map.get(x, x),  # --- i18n ---
            key="urgency_filter",
        )
    with c3:
        st.write("")
        st.write("")
        if st.button(t("btn_refresh_table"), use_container_width=True, key="btn_refresh_registry"):  # --- i18n ---
            st.rerun()

    df_patients = database.get_all_patients(urgency_filter=urgency_filter, search_query=search_q)
    df_patients_disp = i18n.localize_dataframe(df_patients, "patients")  # --- i18n ---
    st.dataframe(df_patients_disp, use_container_width=True, hide_index=True)  # --- i18n ---


# =============================================================================
# TAB 2: PATIENT INTAKE & SCREENING
# =============================================================================
with tab_screen:
    st.subheader(t("intake_heading"))  # --- i18n ---

    # Demographics & Clinical Intake
    with st.expander(t("expander_demographics"), expanded=True):  # --- i18n ---
        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            p_id = st.text_input(t("lbl_patient_id"), value="P-1042", key="p_id_input")  # --- i18n ---
            p_name = st.text_input(t("lbl_patient_name"), value="Ramesh Kumar", key="p_name_input")  # --- i18n ---
            p_age = st.number_input(t("lbl_age"), min_value=1, max_value=120, value=54, key="p_age_input")  # --- i18n ---
        with fcol2:
            gender_map = {"Male": t("opt_gender_male"), "Female": t("opt_gender_female"), "Other": t("opt_gender_other")}  # --- i18n ---
            p_gender = st.selectbox(
                t("lbl_gender"),  # --- i18n ---
                ["Male", "Female", "Other"],
                format_func=lambda x: gender_map.get(x, x),  # --- i18n ---
                index=0,
                key="p_gender_input",
            )
            eye_map = {"Right Eye (OD)": t("opt_eye_od"), "Left Eye (OS)": t("opt_eye_os")}  # --- i18n ---
            p_eye = st.selectbox(
                t("lbl_eye"),  # --- i18n ---
                ["Right Eye (OD)", "Left Eye (OS)"],
                format_func=lambda x: eye_map.get(x, x),  # --- i18n ---
                index=0,
                key="p_eye_input",
            )
            p_contact = st.text_input(t("lbl_contact"), value="+91 98765 43210", key="p_contact_input")  # --- i18n ---
        with fcol3:
            dur_map = {  # --- i18n ---
                "< 1 year": t("opt_duration_lt1"),
                "1 - 5 years": t("opt_duration_1to5"),
                "5 - 10 years": t("opt_duration_5to10"),
                "> 10 years": t("opt_duration_gt10"),
            }
            p_duration = st.selectbox(
                t("lbl_diab_duration"),  # --- i18n ---
                ["< 1 year", "1 - 5 years", "5 - 10 years", "> 10 years"],
                format_func=lambda x: dur_map.get(x, x),  # --- i18n ---
                index=2,
                key="p_duration_input",
            )
            p_sugar = st.text_input(t("lbl_blood_sugar"), value="175", key="p_sugar_input")  # --- i18n ---
            htn_map = {"No": t("opt_no"), "Yes": t("opt_yes")}  # --- i18n ---
            p_hypertension = st.selectbox(
                t("lbl_hypertension"),  # --- i18n ---
                ["No", "Yes"],
                format_func=lambda x: htn_map.get(x, x),  # --- i18n ---
                index=1,
                key="p_hypertension_input",
            )

    # Fundus Image Input
    st.subheader(t("fundus_image_heading"))  # --- i18n ---
    up_col1, up_col2 = st.columns([1, 1])

    uploaded_file = None
    with up_col1:
        uploaded_file = st.file_uploader(
            t("lbl_upload_fundus"),  # --- i18n ---
            type=["jpg", "jpeg", "png"],
            help=t("help_upload_fundus"),  # --- i18n ---
            key="fundus_uploader",
        )

    # Fallback to sample if nothing uploaded
    sample_img = None
    if uploaded_file is not None:
        sample_img = Image.open(uploaded_file).convert("RGB")
    else:
        # Load local sample if available
        test_samples = list(Path(".").glob("*.png")) + list(Path(".").glob("*.jpg"))
        fundus_samples = [f for f in test_samples if "sample" in f.name.lower() or "retina" in f.name.lower() or "slip" not in f.name.lower()]
        if fundus_samples:
            sample_img = Image.open(fundus_samples[0]).convert("RGB")
        else:
            # Create standard fundus circular graphic placeholder
            sample_img = Image.new("RGB", (512, 512), color=(180, 50, 20))

    with up_col2:
        if sample_img is not None:
            st.image(sample_img, caption=t("caption_loaded_fundus"), width=280)  # --- i18n ---

    # --- L&T UPGRADE: Image Quality Gate Pre-Check ---
    q_res = quality.assess_scan_quality(sample_img)
    quality_passed = q_res["passed"]
    proceed_override = False

    if not quality_passed:
        st.markdown(f"""
        <div style="background-color: #fef2f2; border: 2px solid #ef4444; border-radius: 8px; padding: 12px 16px; margin: 12px 0;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 20px;">⚠️</span>
                <strong style="color: #991b1b; font-size: 15px;">
                    {t("msg_quality_failed_title", score=f"{q_res['quality_score']:.1f}")}
                </strong>
            </div>
            <ul style="color: #b91c1c; font-size: 13px; margin: 8px 0 4px 20px;">
                {"".join(f"<li>{r}</li>" for r in q_res['reasons'])}
            </ul>
        </div>
        """, unsafe_allow_html=True)  # --- i18n ---
        proceed_override = st.checkbox(t("lbl_proceed_override"), value=False, key="quality_override_cb")  # --- i18n ---
    else:
        st.markdown(f"""
        <div style="background-color: #f0fdf4; border: 1px solid #86efac; border-radius: 6px; padding: 6px 12px; margin: 8px 0; font-size: 13px; color: #166534;">
            ✓ <strong>{t("msg_quality_passed", score=f"{q_res['quality_score']:.1f}")}</strong>
        </div>
        """, unsafe_allow_html=True)  # --- i18n ---
    # --- END L&T UPGRADE ---

    # Screening Action Button
    st.write("")
    if st.button(t("btn_analyze_patient"), type="primary", use_container_width=True, key="btn_screen_patient"):  # --- i18n ---
        if not quality_passed and not proceed_override:
            st.error(t("msg_quality_blocked"))  # --- i18n ---
        else:
            with st.spinner(t("spinner_analyzing")):  # --- i18n ---
                # 1. Prediction
                pred_idx, pred_label, scores = predict(sample_img)
                conf_val = scores[pred_label]

                # --- L&T UPGRADE: Compute Confidence & Uncertainty Metrics ---
                conf_metrics = confidence.compute_uncertainty_metrics(scores, CLASS_LABELS)
                # --- END L&T UPGRADE ---

                # 2. Grad-CAM Components
                img_224, heatmap_rgb = compute_gradcam_components(sample_img, database.model if hasattr(database, 'model') else None or __import__('predict').model, pred_idx)
                gradcam_default = blend_gradcam_overlay(img_224, heatmap_rgb, opacity_percent=40)

                # 3. Generate Referral Slip with guaranteed QR Code
                slip_img, slip_path = generate_referral_slip(
                    patient_id=p_id,
                    original_image=sample_img,
                    gradcam_image=gradcam_default,
                    predicted_grade=pred_idx,
                    confidence_score=conf_val,
                    language=lang_code,
                    name=p_name,
                    age=p_age,
                    gender=p_gender,
                    eye_examined=p_eye,
                    diabetic_duration=p_duration,
                    blood_sugar=p_sugar,
                    hypertension=p_hypertension,
                )

                # 4. Save to Database
                record_id = database.save_patient_record(
                    patient_id=p_id,
                    name=p_name,
                    age=p_age,
                    gender=p_gender,
                    contact=p_contact,
                    eye_examined=p_eye,
                    diabetic_duration=p_duration,
                    blood_sugar=p_sugar,
                    hypertension=p_hypertension,
                    grade=pred_idx,
                    severity_label=pred_label,
                    urgency="Immediate (Grades 3-4)" if pred_idx >= 3 else ("Routine (Grades 1-2)" if pred_idx >= 1 else "Normal (Grade 0)"),
                    confidence=conf_val,
                    slip_path=slip_path,
                )

                # Cache in Session State
                st.session_state.screening_result = {
                    "pred_idx": pred_idx,
                    "pred_label": pred_label,
                    "confidence": conf_val,
                    "scores": scores,
                    "conf_metrics": conf_metrics,
                    "quality_res": q_res,
                    "proceeded_override": proceed_override,
                    "img_224": img_224,
                    "heatmap_rgb": heatmap_rgb,
                    "slip_img": slip_img,
                    "slip_path": slip_path,
                    "record_id": record_id,
                    "patient_id": p_id,
                    "patient_name": p_name,
                }
                # Reset doctor decision for fresh scan
                st.session_state.doctor_decision = None
                st.success(t("msg_analysis_complete", id=record_id))  # --- i18n ---

    # Display Results if Available
    if st.session_state.screening_result is not None:
        res = st.session_state.screening_result
        g = res["pred_idx"]
        conf = res["confidence"]

        # --- L&T UPGRADE: Mandatory Clinical Decision Support Disclaimer ---
        st.markdown(f"""
        <div style="background-color: #fffbeb; border-left: 5px solid #f59e0b; border-radius: 6px; padding: 10px 14px; margin: 10px 0;">
            <strong style="color: #92400e; font-size: 13px;">⚠️ {t("disclaimer_badge_title")}</strong>
            <span style="color: #78350f; font-size: 12.5px; margin-left: 6px;">
                {t("disclaimer_badge_text")}
            </span>
        </div>
        """, unsafe_allow_html=True)  # --- i18n ---
        # --- END L&T UPGRADE ---

        # Severity Banner (Using localized SeverityMessage)
        sev_msg = MESSAGES.get(lang_code, MESSAGES["en"]).get(g, MESSAGES["en"][g])  # --- i18n ---
        b_title = f"{sev_msg.badge_icon} Grade {g}: {sev_msg.severity_name}"  # --- i18n ---
        b_timeline = sev_msg.action_timeline  # --- i18n ---
        badge_palette = {
            0: ("#10b981", "#ecfdf5"),
            1: ("#eab308", "#fefce8"),
            2: ("#f59e0b", "#fffbeb"),
            3: ("#ea580c", "#fff7ed"),
            4: ("#e11d48", "#fff1f2"),
        }
        b_color, b_bg = badge_palette[g]

        st.markdown(f"""
        <div style="background-color: {b_bg}; border: 2px solid {b_color}; border-radius: 10px; padding: 16px 20px; margin: 12px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div>
                    <h3 style="margin: 0; color: #0f172a; font-size: 20px;">{b_title}</h3>
                    <div style="font-size: 13px; color: {b_color}; font-weight: 700; margin-top: 4px;">{t("action_window_label")}: {b_timeline}</div>
                </div>
                <div style="font-size: 24px; font-weight: 800; color: #0f172a;">
                    {conf*100:.1f}% <span style="font-size: 13px; color: #64748b; font-weight: 500;">{t("ai_confidence_label")}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)  # --- i18n ---

        # --- L&T UPGRADE: Confidence & Uncertainty Diagnostics ---
        conf_data = res.get("conf_metrics", confidence.compute_uncertainty_metrics(res.get("scores", {res["pred_label"]: conf}), CLASS_LABELS))
        q_data = res.get("quality_res", {"passed": True, "quality_score": 85.0, "reasons": []})
        proceeded_flag = res.get("proceeded_override", False)

        if conf_data.get("is_uncertain"):
            st.markdown(f"""
            <div style="background-color: #fff7ed; border-left: 4px solid #ea580c; border-radius: 6px; padding: 10px 14px; margin: 8px 0;">
                <strong style="color: #c2410c; font-size: 13px;">⚠️ {t("uncertainty_badge_title")}</strong>
                <p style="color: #9a3412; font-size: 12px; margin: 4px 0 0 0;">{conf_data.get('uncertainty_reason', '')}</p>
            </div>
            """, unsafe_allow_html=True)  # --- i18n ---

        top1_val = conf_data.get("top1_prob", conf)  # --- i18n ---
        margin_val = conf_data.get("top2_margin", conf_data.get("margin", 0.0))  # --- i18n ---
        entropy_val = conf_data.get("entropy", 0.0)  # --- i18n ---
        conf_status = conf_data.get("confidence_status", "High Confidence" if conf >= 0.8 else "Moderate")  # --- i18n ---
        q_score = q_data.get("quality_score", 85.0)  # --- i18n ---
        q_passed = q_data.get("passed", True)  # --- i18n ---

        m1, m2, m3, m4 = st.columns(4)
        m1.metric(t("metric_top1"), f"{top1_val*100:.1f}%", conf_status)  # --- i18n ---
        m2.metric(t("metric_margin"), f"{margin_val*100:.1f}%")  # --- i18n ---
        m3.metric(t("metric_entropy"), f"{entropy_val:.3f}")  # --- i18n ---
        m4.metric(t("metric_quality"), f"{q_score:.1f}/100", t("status_passed") if q_passed else t("status_flagged"))  # --- i18n ---

        st.caption(f"ℹ️ **{t('limits_note_label')}:** {confidence.LIMITS_OF_RESULT_NOTE}")  # --- i18n ---
        # --- END L&T UPGRADE ---

        # --- L&T UPGRADE: Adaptive Clinical Support Report ---
        current_mode_label = t("opt_style_detailed") if support_style == "Detailed" else t("opt_style_concise")
        st.subheader(f"📋 {t('adaptive_heading', mode=current_mode_label)}")  # --- i18n ---
        adapt_report = adaptive.format_adaptive_report(
            grade=g,
            label=res["pred_label"],
            confidence_data=conf_data,
            quality_data=q_data,
            support_mode=support_style,
            show_evidence=show_evidence,
        )
        st.markdown(adapt_report["markdown"])
        # --- END L&T UPGRADE ---

        # --- L&T UPGRADE: Sarvam GenAI Layer & Doctor Q&A ---
        st.subheader(f"🤖 {t('genai_heading')}")  # --- i18n ---
        sarvam_res = sarvam_client.generate_sarvam_explanation(
            grade=g,
            label=res["pred_label"],
            confidence_data=conf_data,
            quality_data=q_data,
            language_code=lang_code,
            support_mode=support_style,
        )
        st.markdown(f"""
        <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 16px; margin: 8px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 700; font-size: 13px; color: #1e293b;">AI Clinical Summary ({sarvam_res['provider']})</span>
                <span style="background-color: {sarvam_res['badge_color']}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;">{sarvam_res['badge_text']}</span>
            </div>
            <div style="font-size: 13px; color: #334155; line-height: 1.5;">{sarvam_res['text']}</div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"💬 {t('expander_doctor_qa')}"):  # --- i18n ---
            doc_q_input = st.text_input(t("lbl_doctor_query"), placeholder=t("ph_doctor_query"), key="doc_q_text")  # --- i18n ---
            if st.button(t("btn_submit_query"), key="submit_doc_q_btn"):  # --- i18n ---
                if doc_q_input.strip():
                    with st.spinner(t("spinner_genai_query")):  # --- i18n ---
                        q_ans = sarvam_client.generate_sarvam_explanation(
                            grade=g,
                            label=res["pred_label"],
                            confidence_data=conf_data,
                            quality_data=q_data,
                            language_code=lang_code,
                            support_mode=support_style,
                            doctor_question=doc_q_input.strip(),
                        )
                        st.info(f"**{t('ai_copilot_prefix')}:** {q_ans['text']}")  # --- i18n ---
                else:
                    st.warning(t("warn_empty_query"))  # --- i18n ---
        # --- END L&T UPGRADE ---

        # Grad-CAM Opacity & Visual Explainability
        if show_evidence:
            st.subheader(f"🔍 {t('gradcam_section_heading')}")  # --- i18n ---
            opacity_val = st.slider(t("lbl_heatmap_opacity"), min_value=0, max_value=100, value=45, step=5, key="evidence_slider")  # --- i18n ---
            gradcam_live = blend_gradcam_overlay(res["img_224"], res["heatmap_rgb"], opacity_percent=opacity_val)

            g_col1, g_col2 = st.columns(2)
            with g_col1:
                st.image(res["img_224"], caption=t("caption_raw_fundus"), use_container_width=True)  # --- i18n ---
            with g_col2:
                st.image(gradcam_live, caption=t("caption_heatmap_overlay", opacity=opacity_val), use_container_width=True)  # --- i18n ---

            st.caption(f"**{t('lesion_explanation_lbl')}:** {get_caption(g)}")  # --- i18n ---
        else:
            with st.expander(f"🔍 {t('expander_hidden_evidence')}"):  # --- i18n ---
                opacity_val = st.slider(t("lbl_heatmap_opacity"), min_value=0, max_value=100, value=45, step=5, key="hidden_slider")  # --- i18n ---
                gradcam_live = blend_gradcam_overlay(res["img_224"], res["heatmap_rgb"], opacity_percent=opacity_val)
                st.image(gradcam_live, caption=f"Grad-CAM Heatmap ({opacity_val}%)", width=350)

        st.divider()

        # --- L&T UPGRADE: Doctor-in-the-Loop Review Controls ---
        st.subheader(f"👨‍⚕️ {t('review_heading')}")  # --- i18n ---
        st.markdown(t("review_instruction"))  # --- i18n ---

        if "doctor_decision" not in st.session_state or st.session_state.doctor_decision is None:
            rev_c1, rev_c2, rev_c3 = st.columns(3)
            with rev_c1:
                st.markdown(t("col_accept_heading"))  # --- i18n ---
                accept_reason = st.text_input(t("lbl_accept_notes"), placeholder=t("ph_accept_notes"), key="acc_notes")  # --- i18n ---
                if st.button(t("btn_accept_staging"), use_container_width=True, type="primary", key="btn_accept_act"):  # --- i18n ---
                    audit_id = review.record_clinician_decision(
                        scan_id=f"SCAN-{res['record_id']:04d}",
                        patient_id=res["patient_id"],
                        ai_grade=g,
                        confidence_data=conf_data,
                        quality_data=q_data,
                        support_mode=support_style,
                        language=lang_code,
                        action="ACCEPT",
                        doctor_final_grade=g,
                        clinical_reason=accept_reason or "Clinician accepted AI diagnostic assessment.",
                        proceeded_despite_quality=proceeded_flag,
                    )
                    st.session_state.doctor_decision = {
                        "action": "ACCEPT",
                        "final_grade": g,
                        "audit_id": audit_id,
                        "notes": accept_reason or "Clinician accepted AI diagnostic assessment.",
                    }
                    st.rerun()

            with rev_c2:
                st.markdown(t("col_correct_heading"))  # --- i18n ---
                corr_grade = st.selectbox(
                    t("lbl_corrected_grade"),  # --- i18n ---
                    options=[0, 1, 2, 3, 4],
                    index=g,
                    format_func=lambda x: f"Grade {x}: {CLASS_LABELS[x]}",
                    key="corr_grade_sel",
                )
                corr_reason = st.text_input(t("lbl_correct_notes"), placeholder=t("ph_correct_notes"), key="corr_notes")  # --- i18n ---
                if st.button(t("btn_confirm_correction"), use_container_width=True, key="btn_correct_act"):  # --- i18n ---
                    if not corr_reason.strip():
                        st.error(t("err_correction_reason"))  # --- i18n ---
                    else:
                        audit_id = review.record_clinician_decision(
                            scan_id=f"SCAN-{res['record_id']:04d}",
                            patient_id=res["patient_id"],
                            ai_grade=g,
                            confidence_data=conf_data,
                            quality_data=q_data,
                            support_mode=support_style,
                            language=lang_code,
                            action="CORRECT",
                            doctor_final_grade=corr_grade,
                            clinical_reason=corr_reason.strip(),
                            proceeded_despite_quality=proceeded_flag,
                        )
                        st.session_state.doctor_decision = {
                            "action": "CORRECT",
                            "final_grade": corr_grade,
                            "audit_id": audit_id,
                            "notes": corr_reason.strip(),
                        }
                        st.rerun()

            with rev_c3:
                st.markdown(t("col_reject_heading"))  # --- i18n ---
                rej_reason = st.text_input(t("lbl_reject_notes"), placeholder=t("ph_reject_notes"), key="rej_notes")  # --- i18n ---
                if st.button(t("btn_reject_scan"), use_container_width=True, key="btn_reject_act"):  # --- i18n ---
                    if not rej_reason.strip():
                        st.error(t("err_rejection_reason"))  # --- i18n ---
                    else:
                        audit_id = review.record_clinician_decision(
                            scan_id=f"SCAN-{res['record_id']:04d}",
                            patient_id=res["patient_id"],
                            ai_grade=g,
                            confidence_data=conf_data,
                            quality_data=q_data,
                            support_mode=support_style,
                            language=lang_code,
                            action="REJECT",
                            doctor_final_grade=-1,
                            clinical_reason=rej_reason.strip(),
                            proceeded_despite_quality=proceeded_flag,
                        )
                        st.session_state.doctor_decision = {
                            "action": "REJECT",
                            "final_grade": -1,
                            "audit_id": audit_id,
                            "notes": rej_reason.strip(),
                        }
                        st.rerun()
        else:
            dec = st.session_state.doctor_decision
            action_badge = {
                "ACCEPT": ("#10b981", "#ecfdf5", "ACCEPTED", f"Grade {dec['final_grade']} ({CLASS_LABELS[dec['final_grade']]})"),
                "CORRECT": ("#f59e0b", "#fffbeb", "CORRECTED BY CLINICIAN", f"Grade {dec['final_grade']} ({CLASS_LABELS[dec['final_grade']]})"),
                "REJECT": ("#ef4444", "#fef2f2", "REJECTED (NON-DIAGNOSTIC)", "Not graded / Recapture advised"),
            }[dec["action"]]
            st.markdown(f"""
            <div style="background-color: {action_badge[1]}; border: 2px solid {action_badge[0]}; border-radius: 8px; padding: 12px 18px; margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                    <div>
                        <strong style="color: {action_badge[0]}; font-size: 14px;">✓ {t("badge_decision_recorded")}: {action_badge[2]}</strong>
                        <div style="color: #1e293b; font-size: 13px; margin-top: 4px;"><strong>{t("lbl_final_staging")}:</strong> {action_badge[3]}</div>
                        <div style="color: #64748b; font-size: 12px; margin-top: 2px;"><strong>{t("lbl_clinical_rationale")}:</strong> {dec['notes']}</div>
                    </div>
                    <div style="text-align: right; color: #64748b; font-size: 12px;">
                        {t("lbl_audit_log_id")}: <strong>#{dec['audit_id']}</strong>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)  # --- i18n ---
            if st.button(t("btn_change_decision"), key="reset_decision_btn"):  # --- i18n ---
                st.session_state.doctor_decision = None
                st.rerun()
        # --- END L&T UPGRADE ---

        st.divider()

        # Official Printable Referral Slip & QR Code
        st.subheader(f"📄 {t('slip_section_heading')}")  # --- i18n ---
        st.markdown(t("slip_section_desc"))  # --- i18n ---

        slip_col1, slip_col2 = st.columns([3, 1])
        with slip_col1:
            st.image(res["slip_img"], caption=t("caption_slip_image", pid=res["patient_id"]), use_container_width=True)  # --- i18n ---
        with slip_col2:
            st.write("")
            st.write("")
            buf = io.BytesIO()
            res["slip_img"].save(buf, format="PNG")
            st.download_button(
                label=t("btn_download_slip"),  # --- i18n ---
                data=buf.getvalue(),
                file_name=f"NetraScreen_Referral_Slip_{res['patient_id']}.png",
                mime="image/png",
                type="primary",
                use_container_width=True,
                key="btn_dl_referral_slip",  # --- i18n ---
            )
            st.info(f"📱 **{t('info_scan_mobile_title')}**\n{t('info_scan_mobile_desc')}")  # --- i18n ---


# =============================================================================
# TAB 3: CAMP MODE (BATCH SCREENING)
# =============================================================================
with tab_camp:
    st.subheader(f"🏕️ {t('camp_heading')}")  # --- i18n ---
    st.markdown(t("camp_description"))  # --- i18n ---

    batch_files = st.file_uploader(
        t("lbl_select_batch"),  # --- i18n ---
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help=t("help_select_batch"),  # --- i18n ---
        key="batch_files_uploader",
    )

    if batch_files:
        st.write(t("msg_batch_selected", count=len(batch_files)))  # --- i18n ---
        if st.button(t("btn_run_batch"), type="primary", key="btn_run_batch_screening"):  # --- i18n ---
            progress_bar = st.progress(0)
            status_text = st.empty()

            batch_results = []
            for idx, bf in enumerate(batch_files):
                img = Image.open(bf).convert("RGB")
                p_idx, p_lbl, p_scores = predict(img)
                batch_results.append({
                    "Filename": bf.name,
                    "Assigned ID": f"CAMP-{idx+1:03d}",
                    "Grade": p_idx,
                    "Severity": p_lbl,
                    "Confidence": f"{p_scores[p_lbl]*100:.1f}%",
                    "Triage Urgency": "Immediate" if p_idx >= 3 else ("Routine" if p_idx >= 1 else "Normal"),
                })
                progress_bar.progress((idx + 1) / len(batch_files))
                status_text.text(t("status_batch_processing", current=idx + 1, total=len(batch_files), name=bf.name))  # --- i18n ---

            df_batch = pd.DataFrame(batch_results)
            st.success(t("msg_batch_complete", count=len(batch_files)))  # --- i18n ---

            df_batch_disp = i18n.localize_dataframe(df_batch, "batch")  # --- i18n ---
            st.dataframe(df_batch_disp, use_container_width=True)  # --- i18n ---

            csv_data = df_batch.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=t("btn_export_batch_csv"),  # --- i18n ---
                data=csv_data,
                file_name="NetraScreen_Camp_Batch_Summary.csv",
                mime="text/csv",
                type="primary",
                key="btn_dl_batch_csv",  # --- i18n ---
            )


# =============================================================================
# TAB 4: AUDIT & REVIEW TRAIL (--- L&T UPGRADE ---)
# =============================================================================
with tab_audit:
    st.subheader(f"📜 {t('audit_heading')}")  # --- i18n ---
    st.markdown(t("audit_description"))  # --- i18n ---

    audit_summary = audit.get_audit_summary()
    a1, a2, a3, a4, a5 = st.columns(5)
    with a1:
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 4px solid #3b82f6;">
            <div class="kpi-title">{t("kpi_audit_total")}</div>
            <div class="kpi-value">{audit_summary['total']}</div>
            <div style="font-size: 11px; color: #3b82f6; font-weight: 600; margin-top: 4px;">{t("kpi_audit_total_sub")}</div>
        </div>
        """, unsafe_allow_html=True)  # --- i18n ---
    with a2:
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 4px solid #10b981;">
            <div class="kpi-title">{t("kpi_audit_accept")}</div>
            <div class="kpi-value">{audit_summary['accepted']}</div>
            <div style="font-size: 11px; color: #10b981; font-weight: 600; margin-top: 4px;">{t("kpi_audit_accept_sub")}</div>
        </div>
        """, unsafe_allow_html=True)  # --- i18n ---
    with a3:
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 4px solid #f59e0b;">
            <div class="kpi-title">{t("kpi_audit_correct")}</div>
            <div class="kpi-value">{audit_summary['corrected']}</div>
            <div style="font-size: 11px; color: #f59e0b; font-weight: 600; margin-top: 4px;">{t("kpi_audit_correct_sub")}</div>
        </div>
        """, unsafe_allow_html=True)  # --- i18n ---
    with a4:
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 4px solid #ef4444;">
            <div class="kpi-title">{t("kpi_audit_reject")}</div>
            <div class="kpi-value">{audit_summary['rejected']}</div>
            <div style="font-size: 11px; color: #ef4444; font-weight: 600; margin-top: 4px;">{t("kpi_audit_reject_sub")}</div>
        </div>
        """, unsafe_allow_html=True)  # --- i18n ---
    with a5:
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 4px solid #8b5cf6;">
            <div class="kpi-title">{t("kpi_audit_low_quality")}</div>
            <div class="kpi-value">{audit_summary['low_quality']}</div>
            <div style="font-size: 11px; color: #8b5cf6; font-weight: 600; margin-top: 4px;">{t("kpi_audit_low_sub")}</div>
        </div>
        """, unsafe_allow_html=True)  # --- i18n ---

    st.write("")
    f_col1, f_col2 = st.columns([3, 1])
    with f_col1:
        audit_act_map = {  # --- i18n ---
            "All": t("opt_urgency_all"),
            "ACCEPT": t("kpi_audit_accept"),
            "CORRECT": t("kpi_audit_correct"),
            "REJECT": t("kpi_audit_reject"),
        }
        audit_filter = st.selectbox(
            t("lbl_filter_action"),  # --- i18n ---
            ["All", "ACCEPT", "CORRECT", "REJECT"],
            format_func=lambda x: audit_act_map.get(x, x),  # --- i18n ---
            key="audit_filter_sb",
        )
    with f_col2:
        st.write("")
        st.write("")
        if st.button(t("btn_refresh_audit"), use_container_width=True, key="btn_refresh_audit_log"):  # --- i18n ---
            st.rerun()

    df_audit = audit.get_audit_records(action_filter=audit_filter)
    df_audit_disp = i18n.localize_dataframe(df_audit, "audit")  # --- i18n ---
    st.dataframe(df_audit_disp, use_container_width=True, hide_index=True)  # --- i18n ---

    if not df_audit.empty:
        csv_audit = df_audit.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=t("btn_export_audit_csv"),  # --- i18n ---
            data=csv_audit,
            file_name="NetraScreen_Audit_Trail.csv",
            mime="text/csv",
            type="primary",
            key="btn_dl_audit_csv",  # --- i18n ---
        )


# =============================================================================
# TAB 5: DOCTOR + AI EVALUATION (--- L&T UPGRADE ---)
# =============================================================================
with tab_eval:
    st.subheader(f"📈 {t('eval_heading')}")  # --- i18n ---
    st.info(t("eval_academic_notice"))  # --- i18n ---

    if st.button(t("btn_run_simulation"), type="primary", key="btn_run_simulation_act"):  # --- i18n ---
        with st.spinner(t("spinner_running_sim")):  # --- i18n ---
            df_sim, fig_sim = evaluate.run_hybrid_reader_simulation()
            st.session_state.sim_results = (df_sim, fig_sim)

    if "sim_results" not in st.session_state:
        df_sim, fig_sim = evaluate.run_hybrid_reader_simulation()
        st.session_state.sim_results = (df_sim, fig_sim)

    df_sim, fig_sim = st.session_state.sim_results

    st.markdown(f"#### {t('sim_table_heading')}")  # --- i18n ---
    df_sim_disp = i18n.localize_dataframe(df_sim, "simulation")  # --- i18n ---
    st.dataframe(df_sim_disp, use_container_width=True, hide_index=True)  # --- i18n ---

    st.pyplot(fig_sim)

    st.divider()
    st.markdown(f"#### ⚖️ {t('fairness_heading')}")  # --- i18n ---
    st.caption(t("fairness_caption"))  # --- i18n ---

    demo_cohort = [
        {"age": 38, "gender": "Male", "true_grade": 0, "pred_grade": 0},
        {"age": 42, "gender": "Female", "true_grade": 1, "pred_grade": 1},
        {"age": 55, "gender": "Male", "true_grade": 2, "pred_grade": 2},
        {"age": 58, "gender": "Female", "true_grade": 3, "pred_grade": 3},
        {"age": 67, "gender": "Male", "true_grade": 4, "pred_grade": 4},
        {"age": 71, "gender": "Female", "true_grade": 2, "pred_grade": 2},
        {"age": 49, "gender": "Female", "true_grade": 0, "pred_grade": 0},
        {"age": 62, "gender": "Male", "true_grade": 1, "pred_grade": 1},
        {"age": 35, "gender": "Female", "true_grade": 0, "pred_grade": 0},
        {"age": 64, "gender": "Male", "true_grade": 3, "pred_grade": 3},
    ]
    df_bias = privacy.evaluate_subgroup_bias(demo_cohort)
    df_bias_disp = i18n.localize_dataframe(df_bias, "bias")  # --- i18n ---
    st.dataframe(df_bias_disp, use_container_width=True, hide_index=True)  # --- i18n ---
# --- END L&T UPGRADE ---
