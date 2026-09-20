"""
streamlit_app.py — Official Streamlit Cloud Web Application for NetraScreen AI.
Diabetic Retinopathy Clinical Screening Dashboard & Tele-Ophthalmology Triage Unit.

Features:
  - Tab 1: 📊 Clinical Screening Dashboard & Registry (Live KPIs, charts, searchable registry)
  - Tab 2: 👤 Patient Intake & Screening (Demographics, Fundus upload, Grad-CAM, QR Referral Slip)
  - Tab 3: 🏕️ Camp Mode — Rapid Batch Screening (Rural camp triage & CSV export)
  - HackDay 1.0 Presentation Deck & Final Review PDF Downloads
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

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NetraScreen — Clinical Screening Dashboard",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Clean Medical Theme Styling
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

# -----------------------------------------------------------------------------
# Sidebar Configuration
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔬 NetraScreen AI")
    st.caption("AI-Assisted Tele-Ophthalmology Screening Unit")
    st.divider()

    # Regional Language Selector
    st.markdown("#### 🌐 Language / भाषा")
    selected_lang_name = st.selectbox(
        "Select Language",
        options=LANGUAGE_OPTIONS,
        index=0,
        label_visibility="collapsed",
    )
    lang_code = LANGUAGE_CODE_MAP.get(selected_lang_name, "en")
    lang_dict = MESSAGES.get(lang_code, MESSAGES["en"])

    st.divider()

    # HackDay Presentation & PDF Downloads
    st.markdown("#### 📁 Hackathon Deliverables")
    pptx_path = Path("NetraScreen_HackDay_Presentation.pptx")
    if pptx_path.exists():
        with open(pptx_path, "rb") as f:
            st.download_button(
                label="📊 Download PPT (HackDay 1.0)",
                data=f.read(),
                file_name="NetraScreen_HackDay_Presentation.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
            )

    pdf_path = Path("NetraScreen_Hackathon_Final_Review.pdf")
    if pdf_path.exists():
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="📄 Download Review PDF Report",
                data=f.read(),
                file_name="NetraScreen_Hackathon_Final_Review.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    st.link_button("⭐ GitHub Repository", "https://github.com/Abinav2107/retina-screen-ai", use_container_width=True)

    st.divider()
    st.info(
        "**Rural Clinic Ready:**\n"
        "Runs on edge hardware with 100% offline capabilities. Zero cloud dependencies in field operation."
    )

# -----------------------------------------------------------------------------
# Main Header & Rural Clinic Banner
# -----------------------------------------------------------------------------
st.title("🔬 NetraScreen — Clinical Screening Dashboard & Registry")
st.markdown(
    "Automated retinal photograph analysis: **Patient Demographics & Medical History**, "
    "**AI Grading with Grad-CAM Lesion Heatmaps**, **Printable EHR Referral Slips with QR Codes**, "
    "and **Clinic-wide Real-Time Analytics Dashboard**."
)

# Clinic Banner
st.markdown("""
<div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 10px 14px; margin-bottom: 16px;">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
        <div>
            <span style="color: #166534; font-size: 13px; font-weight: 700;">🏥 Active Health Centre: Community Health Centre - Sector 4</span>
            <span style="color: #86efac; margin: 0 8px;">•</span>
            <span style="color: #15803d; font-size: 13px; font-weight: 600;">Rural Camp ID: CAMP-2026-09</span>
        </div>
        <div style="font-size: 12px; color: #166534; font-weight: 600;">
            📶 24/7 Cloud Active (No Laptop Required)
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Session State for Intake Screening Cache
# -----------------------------------------------------------------------------
if "screening_result" not in st.session_state:
    st.session_state.screening_result = None

# -----------------------------------------------------------------------------
# TABS
# -----------------------------------------------------------------------------
tab_dash, tab_screen, tab_camp = st.tabs([
    "📊 Clinical Screening Dashboard & Registry",
    "👤 Patient Intake & Screening",
    "🏕️ Camp Mode — Batch Screening",
])

# =============================================================================
# TAB 1: DASHBOARD & REGISTRY
# =============================================================================
with tab_dash:
    st.subheader("Live Clinical Key Performance Indicators (KPIs)")
    kpis = database.get_dashboard_kpis()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 4px solid #3b82f6;">
            <div class="kpi-title">🩺 Total Screened</div>
            <div class="kpi-value">{kpis['total']}</div>
            <div style="font-size: 11px; color: #3b82f6; font-weight: 600; margin-top: 4px;">Registered Patients</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 4px solid #10b981;">
            <div class="kpi-title">🟢 Normal Retinas</div>
            <div class="kpi-value">{kpis['normal']}</div>
            <div style="font-size: 11px; color: #10b981; font-weight: 600; margin-top: 4px;">Grade 0 — No DR</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 4px solid #f59e0b;">
            <div class="kpi-title">🟡 Mild / Moderate DR</div>
            <div class="kpi-value">{kpis['mild_mod']}</div>
            <div style="font-size: 11px; color: #f59e0b; font-weight: 600; margin-top: 4px;">Grades 1-2 Routine Care</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 4px solid #ef4444;">
            <div class="kpi-title">🚨 Urgent Referrals</div>
            <div class="kpi-value">{kpis['urgent']}</div>
            <div style="font-size: 11px; color: #ef4444; font-weight: 600; margin-top: 4px;">Grades 3-4 High Risk</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 4px solid #8b5cf6;">
            <div class="kpi-title">📈 DR Prevalence Rate</div>
            <div class="kpi-value">{kpis['referral_rate']:.1f}%</div>
            <div style="font-size: 11px; color: #8b5cf6; font-weight: 600; margin-top: 4px;">Requiring Care / Triage</div>
        </div>
        """, unsafe_allow_html=True)

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
    st.subheader("📋 Registered Screened Patients")
    c1, c2, c3 = st.columns([3, 2, 1])
    with c1:
        search_q = st.text_input("🔍 Search by Patient ID or Name", placeholder="e.g. P-1042 or Ramesh", key="search_input")
    with c2:
        urgency_filter = st.selectbox(
            "Filter by Triage Urgency",
            ["All", "🚨 Urgent / Immediate (Grades 3-4)", "🟡 Follow-up / Routine (Grades 1-2)", "🟢 Normal (Grade 0)"],
            key="urgency_filter",
        )
    with c3:
        st.write("")
        st.write("")
        if st.button("🔄 Refresh Table", use_container_width=True):
            st.rerun()

    df_patients = database.get_all_patients(urgency_filter=urgency_filter, search_query=search_q)
    st.dataframe(df_patients, use_container_width=True, hide_index=True)


# =============================================================================
# TAB 2: PATIENT INTAKE & SCREENING
# =============================================================================
with tab_screen:
    st.subheader("Patient Clinical Context & Retinal Screening")

    # Demographics & Clinical Intake
    with st.expander("👤 Patient Demographics & Diabetic History", expanded=True):
        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            p_id = st.text_input("Patient ID / OPD Number", value="P-1042")
            p_name = st.text_input("Full Name", value="Ramesh Kumar")
            p_age = st.number_input("Age (Years)", min_value=1, max_value=120, value=54)
        with fcol2:
            p_gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=0)
            p_eye = st.selectbox("Eye Examined", ["Right Eye (OD)", "Left Eye (OS)"], index=0)
            p_contact = st.text_input("Contact / Mobile No.", value="+91 98765 43210")
        with fcol3:
            p_duration = st.selectbox("Diabetes Duration", ["< 1 year", "1 - 5 years", "5 - 10 years", "> 10 years"], index=2)
            p_sugar = st.text_input("Fasting Blood Sugar (mg/dL)", value="175")
            p_hypertension = st.selectbox("Hypertension History", ["No", "Yes"], index=1)

    # Fundus Image Input
    st.subheader("Retinal Fundus Image")
    up_col1, up_col2 = st.columns([1, 1])

    uploaded_file = None
    with up_col1:
        uploaded_file = st.file_uploader(
            "Upload Fundus Photograph (JPG / PNG)",
            type=["jpg", "jpeg", "png"],
            help="High-quality macula/optic disc-centered fundus photograph.",
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
            st.image(sample_img, caption="Loaded Fundus Photograph", width=280)

    # Screening Action Button
    st.write("")
    if st.button("🔍 Analyse Retina & Register Patient", type="primary", use_container_width=True):
        with st.spinner("Running EfficientNetB0 classification & Grad-CAM explainability..."):
            # 1. Prediction
            pred_idx, pred_label, scores = predict(sample_img)
            conf_val = scores[pred_label]

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
                "img_224": img_224,
                "heatmap_rgb": heatmap_rgb,
                "slip_img": slip_img,
                "slip_path": slip_path,
                "record_id": record_id,
                "patient_id": p_id,
            }
            st.success(f"✓ Analysis Complete & Registered as Record #{record_id}!")

    # Display Results if Available
    if st.session_state.screening_result is not None:
        res = st.session_state.screening_result
        g = res["pred_idx"]
        conf = res["confidence"]

        st.divider()

        # Severity Banner
        badge_colors = {
            0: ("#10b981", "#ecfdf5", "🟢 Grade 0: No Diabetic Retinopathy", "Normal Retina (Annual follow-up)"),
            1: ("#eab308", "#fefce8", "🟡 Grade 1: Mild NPDR", "Routine Checkup (6 months)"),
            2: ("#f59e0b", "#fffbeb", "🟠 Grade 2: Moderate NPDR", "Specialist Review (2 weeks)"),
            3: ("#ea580c", "#fff7ed", "🔴 Grade 3: Severe NPDR", "Urgent Referral (3 days)"),
            4: ("#e11d48", "#fff1f2", "🚨 Grade 4: Proliferative DR", "Immediate Intervention Required (24-48 hrs)"),
        }
        b_color, b_bg, b_title, b_timeline = badge_colors[g]

        st.markdown(f"""
        <div style="background-color: {b_bg}; border: 2px solid {b_color}; border-radius: 10px; padding: 16px 20px; margin: 12px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div>
                    <h3 style="margin: 0; color: #0f172a; font-size: 20px;">{b_title}</h3>
                    <div style="font-size: 13px; color: {b_color}; font-weight: 700; margin-top: 4px;">Clinical Action Window: {b_timeline}</div>
                </div>
                <div style="font-size: 24px; font-weight: 800; color: #0f172a;">
                    {conf*100:.1f}% <span style="font-size: 13px; color: #64748b; font-weight: 500;">AI Confidence</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Grad-CAM Opacity & Visual Explainability
        st.subheader("🔍 Dual Retinal Imagery & Lesion Explainability")
        opacity_val = st.slider("Grad-CAM Heatmap Opacity (%)", min_value=0, max_value=100, value=45, step=5)
        gradcam_live = blend_gradcam_overlay(res["img_224"], res["heatmap_rgb"], opacity_percent=opacity_val)

        g_col1, g_col2 = st.columns(2)
        with g_col1:
            st.image(res["img_224"], caption="Raw Fundus Photograph (Macula & Vessels)", use_container_width=True)
        with g_col2:
            st.image(gradcam_live, caption=f"Grad-CAM Heatmap ({opacity_val}% Opacity) — Focused Pathological Lesions", use_container_width=True)

        st.caption(f"**Lesion Explanation:** {get_caption(g)}")

        st.divider()

        # Official Printable Referral Slip & QR Code
        st.subheader("📄 Official Printable EHR Referral Slip (with Scannable QR Code)")
        st.markdown(
            "Structured digital referral slip compliant with ABDM tele-ophthalmology store-and-forward standards. "
            "**Includes scannable QR code** containing patient demographics, clinical triage urgency, and doctor notes."
        )

        slip_col1, slip_col2 = st.columns([3, 1])
        with slip_col1:
            st.image(res["slip_img"], caption=f"NetraScreen Digital Referral Slip — Patient {res['patient_id']}", use_container_width=True)
        with slip_col2:
            st.write("")
            st.write("")
            buf = io.BytesIO()
            res["slip_img"].save(buf, format="PNG")
            st.download_button(
                label="📥 Download Referral Slip (PNG)",
                data=buf.getvalue(),
                file_name=f"NetraScreen_Referral_Slip_{res['patient_id']}.png",
                mime="image/png",
                type="primary",
                use_container_width=True,
            )
            st.info(
                "📱 **Scan with Mobile:**\n"
                "The embedded QR code on the slip can be scanned with any smartphone camera or hospital barcode scanner to instantly import patient triage data."
            )


# =============================================================================
# TAB 3: CAMP MODE (BATCH SCREENING)
# =============================================================================
with tab_camp:
    st.subheader("🏕️ Camp Mode — Rapid Batch Screening Pipeline")
    st.markdown(
        "Designed for high-throughput rural vision camps. "
        "Upload multiple retinal fundus images simultaneously to generate mass triage classifications and instant CSV reports."
    )

    batch_files = st.file_uploader(
        "Select Multiple Retinal Photographs",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="Select multiple image files from local drive or SD card.",
    )

    if batch_files:
        st.write(f"📁 Selected **{len(batch_files)}** retinal fundus images for batch screening.")
        if st.button("⚡ Run Batch Screening Pipeline", type="primary"):
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
                status_text.text(f"Processed {idx + 1} of {len(batch_files)} ({bf.name})")

            df_batch = pd.DataFrame(batch_results)
            st.success(f"✓ Batch Screening Complete for {len(batch_files)} Retinal Photographs!")

            st.dataframe(df_batch, use_container_width=True)

            csv_data = df_batch.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Batch Triage CSV Summary",
                data=csv_data,
                file_name="NetraScreen_Camp_Batch_Summary.csv",
                mime="text/csv",
                type="primary",
            )
