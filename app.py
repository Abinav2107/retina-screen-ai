"""
app.py -- Clinical Screening Dashboard & Patient Registry for Diabetic Retinopathy:
  Tab 1: 📊 Clinical Screening Dashboard & Registry (Live KPIs, Matplotlib charts, searchable database)
  Tab 2: 👤 Patient Intake & Screening (Demographics, diabetic history, eye OD/OS, Grad-CAM, QR slip)
  Tab 3: 🏕️ Camp Mode -- Rapid Batch Screening (Mass camp triage & CSV export)

Run:
    python app.py
Then open http://localhost:7860 in your browser.
"""

import os
from pathlib import Path
from PIL import Image
import pandas as pd

# Suppress verbose TF / oneDNN logs
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import gradio as gr
from predict import predict, model, CLASS_LABELS
from gradcam import (
    generate_gradcam,
    get_caption,
    compute_gradcam_components,
    blend_gradcam_overlay,
    adjust_cached_opacity,
)
from languages import (
    MESSAGES,
    LANGUAGE_OPTIONS,
    LANGUAGE_CODE_MAP,
    get_language_code,
)
from referral import get_patient_message
from referral_slip import generate_referral_slip
from batch import (
    process_batch,
    build_dataframe,
    calculate_camp_summary,
    export_batch_csv,
)
import database


# ------------------------------------------------------------------
# HTML Rendering Helpers (Pure English by default, dynamic per chosen language)
# ------------------------------------------------------------------
def render_disclaimer_html(disclaimer_text: str, title: str = "Medical Screening Disclaimer") -> str:
    """Renders the medical screening disclaimer banner in the active language."""
    return f"""
    <div style="background-color: #fffbeb; border: 1px solid #fef3c7; border-left: 5px solid #f59e0b; border-radius: 8px; padding: 10px 14px; margin: 8px 0;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 20px;">⚠️</span>
            <div>
                <span style="color: #92400e; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">
                    {title}
                </span>
                <p style="color: #78350f; font-size: 12px; margin: 2px 0 0 0; line-height: 1.35;">
                    {disclaimer_text}
                </p>
            </div>
        </div>
    </div>
    """


def render_rural_banner_html(
    title: str = "Rural Clinic Ready (100% Offline Edge Operation)",
    note: str = "Runs locally on edge hardware with zero external cloud connectivity required. Multi-language translation & patient database remain fully accessible offline.",
) -> str:
    """Renders the offline clinic readiness banner dynamically in the active language."""
    return f"""
    <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 10px 14px; margin-bottom: 10px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 20px;">📶</span>
            <div>
                <span style="color: #166534; font-size: 13px; font-weight: 700;">
                    {title}
                </span>
                <p style="color: #15803d; font-size: 12px; margin: 2px 0 0 0;">
                    {note}
                </p>
            </div>
        </div>
    </div>
    """


def render_summary_banner_html(summary_text: str) -> str:
    return f"""
    <div style="
        background: linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 100%);
        border: 1px solid #38bdf8;
        border-radius: 8px;
        padding: 12px 18px;
        margin: 10px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    ">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 24px;">📊</span>
            <div>
                <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #0369a1;">
                    CAMP SCREENING METRICS
                </div>
                <div style="font-size: 18px; font-weight: 800; color: #0f172a; margin-top: 1px;">
                    {summary_text}
                </div>
            </div>
        </div>
    </div>
    """


SEVERITY_REFERENCE_MD = """
### 📚 Diabetic Retinopathy Severity Grading Reference
| Grade | Severity Stage | Primary Clinical Features | Rural Triage Recommendation |
|:---:|:---|:---|:---|
| **0** | **No DR** | Clear retina, healthy vessel network | 🟢 No action needed (annual screening) |
| **1** | **Mild NPDR** | Microaneurysms only (isolated tiny spots) | 🟡 Routine checkup within 6 months |
| **2** | **Moderate NPDR** | Microaneurysms, blot haemorrhages, venous beading | 🟠 See a doctor within 2 weeks |
| **3** | **Severe NPDR** | >20 intraretinal haemorrhages, venous beading, IRMA | 🔴 Urgent — see a doctor within 3 days |
| **4** | **Proliferative DR** | Neovascularisation, vitreous haemorrhage, risk of retinal detachment | 🚨 Immediate referral required — risk of vision loss |
"""


# ------------------------------------------------------------------
# In-Memory Cache for Current Patient Analysis
# ------------------------------------------------------------------
_CURRENT_PATIENT_CACHE = {
    "image": None,
    "gradcam": None,
    "grade": 0,
    "label": "No DR",
    "confidence": 0.0,
    "patient_id": "P-1042",
    "name": "Patient",
    "age": 50,
    "gender": "Male",
    "eye": "Right Eye (OD)",
    "diabetic_duration": "5 - 10 years",
    "blood_sugar": "160",
    "hypertension": "No",
    "slip_path": "",
}


# ------------------------------------------------------------------
# Tab 1: Dashboard Callbacks
# ------------------------------------------------------------------
def update_dashboard_view(urgency_filter="All", search_query=""):
    """Refreshes KPI metric cards, charts, and patient registry table."""
    kpi_html = database.render_kpi_cards_html()
    fig_dist, fig_age = database.generate_dashboard_charts()
    df_patients = database.get_all_patients(urgency_filter=urgency_filter, search_query=search_query)
    return kpi_html, fig_dist, fig_age, df_patients


def export_dashboard_csv_action():
    """Generates and returns the registry CSV export path."""
    csv_path = database.export_registry_csv("clinic_patient_registry.csv")
    return csv_path


def load_demo_patients_action():
    """Seeds 5 clinical demo records and refreshes the dashboard view."""
    database.seed_demo_patients()
    kpi_html, fig_dist, fig_age, df_patients = update_dashboard_view("All", "")
    return kpi_html, fig_dist, fig_age, df_patients, "✅ Loaded 5 clinical patient records into the registry."


# ------------------------------------------------------------------
# Tab 2: Individual Patient Intake & Screening Pipeline
# ------------------------------------------------------------------
def run_patient_intake_screening(
    patient_name,
    patient_id,
    age,
    gender,
    contact,
    eye_examined,
    diabetic_duration,
    blood_sugar,
    hypertension,
    pil_image,
    language_choice="English",
    opacity=40,
):
    """
    Executes individual patient intake and AI screening:
      1. AI inference (DR severity classification).
      2. Grad-CAM visual attention overlay with custom opacity.
      3. Plain-language patient advisory in the chosen preferred language.
      4. Printable referral slip with patient demographics and scannable EHR QR code.
      5. Commits record to local SQLite patient database.
    """
    global _CURRENT_PATIENT_CACHE

    lang_code = get_language_code(language_choice)
    lang_dict = MESSAGES.get(lang_code, MESSAGES["en"])
    ui_strings = lang_dict.get("ui", {})
    disclaimer_text = lang_dict.get("disclaimer", MESSAGES["en"]["disclaimer"])
    disclaimer_title = ui_strings.get("disclaimer_title", "Medical Screening Disclaimer")

    if pil_image is None:
        placeholder_badge = """
        <div style="background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 10px; padding: 18px; text-align: center; color: #64748b;">
            <p style="font-size: 15px; margin: 0; font-weight: 600;">📷 Upload a retinal fundus photo to start screening.</p>
        </div>
        """
        return (
            None,
            placeholder_badge,
            "No image uploaded.",
            "",
            {},
            "",
            render_disclaimer_html(disclaimer_text, title=disclaimer_title),
            None,
            None,
            "",
        )

    clean_name = str(patient_name).strip() if patient_name else "Unnamed Patient"
    clean_id = str(patient_id).strip() if patient_id else "P-1042"
    clean_age = int(age) if age else 50
    clean_gender = str(gender).strip() if gender else "Unspecified"
    clean_eye = str(eye_examined).strip() if eye_examined else "Right Eye (OD)"
    clean_sugar = str(blood_sugar).strip() if blood_sugar else ""
    clean_htn = str(hypertension).strip() if hypertension else "No"
    clean_diab = str(diabetic_duration).strip() if diabetic_duration else "Unknown"

    # 1. AI Prediction
    predicted_index, predicted_label, scores = predict(pil_image)
    top_conf = scores[predicted_label] * 100

    # 2. Grad-CAM overlay with customizable opacity
    gradcam_image = generate_gradcam(pil_image, model, predicted_index, opacity_percent=opacity)

    # Caption in chosen language
    if predicted_index == 0:
        gradcam_caption = ui_strings.get("caption_normal", get_caption(0))
    elif predicted_index in (1, 2):
        gradcam_caption = ui_strings.get("caption_mild_mod", get_caption(1))
    else:
        gradcam_caption = ui_strings.get("caption_severe_pdr", get_caption(4))

    # 3. Patient message & urgency badge in chosen language
    patient_msg = get_patient_message(predicted_index, scores[predicted_label], language=lang_code)

    # Localized labels (single language only, no dual-language slashes)
    p_lbl = ui_strings.get("patient_label", "Patient")
    eye_lbl = ui_strings.get("eye_label", "Eye Examined")
    stage_lbl = ui_strings.get("stage_label", "Stage")
    conf_lbl = ui_strings.get("confidence_label", "Confidence")
    triage_lbl = ui_strings.get("triage_label", "Recommended Triage")
    urg_lbl = ui_strings.get("urgency_label", "Urgency")
    time_lbl = ui_strings.get("timeline_label", "Recommended Timeline")
    hist_lbl = ui_strings.get("history_label", "Clinical History")

    # 4. Summary card in chosen language
    summary_text = (
        f"{p_lbl}: {clean_name} ({clean_id})  •  {eye_lbl}: {clean_eye}\n"
        f"{stage_lbl}: {patient_msg.severity_name} (Grade {predicted_index})  •  {conf_lbl}: {top_conf:.1f}%\n"
        f"{triage_lbl}: {patient_msg.urgency}"
    )

    # 5. Formatted patient explanation in Markdown
    patient_explanation_md = f"""
### 💬 {ui_strings.get('explanation_header', 'Patient-Friendly Explanation')}
> {patient_msg.explanation}

**{ui_strings.get('urgency_header', 'Patient Profile & Recommendations')}:**
- 👤 **{p_lbl}:** {clean_name} ({clean_age} yrs, {clean_gender}) • **{eye_lbl}:** {clean_eye}
- ⏱️ **{urg_lbl}:** **{patient_msg.urgency}**
- 🏥 **{time_lbl}:** {patient_msg.action_timeline}
- 🩺 **{hist_lbl}:** Diabetes ({clean_diab}), Sugar ({clean_sugar or 'N/A'}), HTN ({clean_htn})
"""

    # 6. Generate official printable referral slip with QR Code
    slip_filename = f"referral_slip_{clean_id.replace(' ', '_')}.png"
    slip_img, slip_path = generate_referral_slip(
        patient_id=clean_id,
        name=clean_name,
        age=clean_age,
        gender=clean_gender,
        eye_examined=clean_eye,
        diabetic_duration=clean_diab,
        blood_sugar=clean_sugar,
        hypertension=clean_htn,
        original_image=pil_image,
        gradcam_image=gradcam_image,
        predicted_grade=predicted_index,
        confidence_score=scores[predicted_label],
        language=lang_code,
        output_filename=slip_filename,
    )

    # 7. Commit record to SQLite Database
    rec_id = database.save_patient_record(
        patient_id=clean_id,
        name=clean_name,
        age=clean_age,
        gender=clean_gender,
        contact=str(contact).strip(),
        eye_examined=clean_eye,
        diabetic_duration=clean_diab,
        blood_sugar=clean_sugar,
        hypertension=clean_htn,
        grade=predicted_index,
        severity_label=predicted_label,
        urgency=patient_msg.urgency,
        confidence=scores[predicted_label],
        slip_path=slip_path,
    )

    status_alert = f"""
    <div style="background-color: #f0fdf4; border-left: 4px solid #16a34a; padding: 8px 12px; border-radius: 6px; margin: 6px 0;">
        <span style="color: #15803d; font-weight: 700; font-size: 13px;">
            ✅ Patient {clean_name} successfully screened and registered in clinic database (Record #{rec_id})
        </span>
    </div>
    """

    # Cache state
    _CURRENT_PATIENT_CACHE = {
        "image": pil_image,
        "gradcam": gradcam_image,
        "grade": predicted_index,
        "label": predicted_label,
        "confidence": scores[predicted_label],
        "patient_id": clean_id,
        "name": clean_name,
        "age": clean_age,
        "gender": clean_gender,
        "eye": clean_eye,
        "diabetic_duration": clean_diab,
        "blood_sugar": clean_sugar,
        "hypertension": clean_htn,
        "slip_path": slip_path,
    }

    return (
        gradcam_image,
        patient_msg.badge_html,
        summary_text,
        patient_explanation_md,
        scores,
        gradcam_caption,
        render_disclaimer_html(disclaimer_text, title=disclaimer_title),
        slip_img,
        slip_path,
        status_alert,
    )


def on_opacity_change(opacity_value):
    """Instantaneous pure-numpy array blending (<1ms)."""
    updated_img = adjust_cached_opacity(opacity_percent=int(opacity_value))
    if updated_img is not None:
        _CURRENT_PATIENT_CACHE["gradcam"] = updated_img
    return updated_img


def on_generate_slip_click(
    patient_name, patient_id, age, gender, eye, diab, sugar, htn, language_choice
):
    """Regenerates the referral slip with updated details or language."""
    global _CURRENT_PATIENT_CACHE
    img = _CURRENT_PATIENT_CACHE.get("image")
    grad = _CURRENT_PATIENT_CACHE.get("gradcam")
    grade = _CURRENT_PATIENT_CACHE.get("grade", 0)
    conf = _CURRENT_PATIENT_CACHE.get("confidence", 0.0)

    if img is None or grad is None:
        return None, None

    clean_id = patient_id.strip() if patient_id and patient_id.strip() else "P-1042"
    clean_name = patient_name.strip() if patient_name and patient_name.strip() else "Patient"
    lang_code = get_language_code(language_choice)

    slip_img, slip_path = generate_referral_slip(
        patient_id=clean_id,
        name=clean_name,
        age=int(age) if age else 50,
        gender=gender,
        eye_examined=eye,
        diabetic_duration=diab,
        blood_sugar=sugar,
        hypertension=htn,
        original_image=img,
        gradcam_image=grad,
        predicted_grade=grade,
        confidence_score=conf,
        language=lang_code,
        output_filename=f"referral_slip_{clean_id.replace(' ', '_')}.png",
    )
    return slip_img, slip_path


def on_language_change_global(
    language_choice,
    patient_name,
    patient_id,
    age,
    gender,
    contact,
    eye,
    diab,
    sugar,
    htn,
    image,
    opacity,
):
    """
    Updates the top rural banner, medical disclaimer, and active screening findings
    dynamically when the user changes their preferred language.
    """
    lang_code = get_language_code(language_choice)
    lang_dict = MESSAGES.get(lang_code, MESSAGES["en"])
    ui_strings = lang_dict.get("ui", {})

    # Top banner & disclaimer update
    banner_html = render_rural_banner_html(
        title=ui_strings.get("rural_banner_title", "Rural Clinic Ready (100% Offline Edge Operation)"),
        note=lang_dict.get("rural_note", ""),
    )
    disclaimer_html = render_disclaimer_html(
        disclaimer_text=lang_dict.get("disclaimer", MESSAGES["en"]["disclaimer"]),
        title=ui_strings.get("disclaimer_title", "Medical Screening Disclaimer"),
    )

    # If an image is currently loaded, re-run localized summary & slip
    if image is not None:
        intake_res = run_patient_intake_screening(
            patient_name,
            patient_id,
            age,
            gender,
            contact,
            eye,
            diab,
            sugar,
            htn,
            image,
            language_choice=language_choice,
            opacity=opacity,
        )
        return (
            banner_html,
            intake_res[0],
            intake_res[1],
            intake_res[2],
            intake_res[3],
            intake_res[4],
            intake_res[5],
            disclaimer_html,
            intake_res[7],
            intake_res[8],
            intake_res[9],
        )

    return (
        banner_html,
        None,
        """
        <div style="background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 10px; padding: 18px; text-align: center; color: #64748b;">
            <p style="font-size: 15px; margin: 0; font-weight: 600;">📷 Complete patient details and upload fundus photograph to begin screening.</p>
        </div>
        """,
        "",
        "*Patient-friendly explanation will appear here after screening.*",
        {},
        "",
        disclaimer_html,
        None,
        None,
        "",
    )


# ------------------------------------------------------------------
# Tab 3: Camp Mode -- Rapid Batch Screening
# ------------------------------------------------------------------
def run_batch_camp_screening(files_list, language_choice="English"):
    if not files_list:
        empty_df = pd.DataFrame(columns=["Patient ID", "Severity", "Urgency Level", "Confidence"])
        empty_banner = render_summary_banner_html("0 patients screened — Please select or upload images above")
        return empty_banner, empty_df, None

    lang_code = get_language_code(language_choice)
    batch_results = process_batch(files_list, language=lang_code)
    summary_text = calculate_camp_summary(batch_results, language=lang_code)
    summary_banner_html = render_summary_banner_html(summary_text)
    df = build_dataframe(batch_results)
    csv_path = export_batch_csv(batch_results, output_path="batch_screening_report.csv")
    return summary_banner_html, df, csv_path


def load_5_sample_patients():
    demo_files = [
        "sample_images/clinical_grade4_proliferative_dr.jpg",
        "sample_images/clinical_grade3_severe_npdr.jpg",
        "sample_images/clinical_grade2_moderate_npdr.png",
        "sample_images/clinical_grade1_mild_npdr.png",
        "sample_images/clinical_grade0_no_dr.jpg",
    ]
    return [f for f in demo_files if Path(f).exists()]


# Clinical sample images for single-patient test
sample_dir = Path("sample_images")
available_single_examples = []
if sample_dir.exists():
    for f in [
        "clinical_grade0_no_dr.jpg",
        "clinical_grade1_mild_npdr.png",
        "clinical_grade2_moderate_npdr.png",
        "clinical_grade3_severe_npdr.jpg",
        "clinical_grade4_proliferative_dr.jpg",
    ]:
        p = sample_dir / f
        if p.exists():
            available_single_examples.append([str(p)])


# ------------------------------------------------------------------
# Gradio UI Layout (Clean English by default, dynamic on language selection)
# ------------------------------------------------------------------
custom_css = """
.badge-container { margin: 6px 0; }
.output-image { border-radius: 8px; overflow: hidden; }
.dataframe table { width: 100%; border-collapse: collapse; font-size: 13px; }
.dataframe th { background-color: #f8fafc; font-weight: 700; color: #334155; }
.dataframe td { padding: 8px 10px; }
"""

with gr.Blocks(title="NetraScreen - Clinical Screening Dashboard") as demo:

    gr.Markdown("# 🔬 NetraScreen — Diabetic Retinopathy Clinical Dashboard & Screening Unit")
    gr.Markdown(
        "Automated retinal photograph analysis: **Patient Demographics & Medical History**, **AI Grading with Grad-CAM Lesion Heatmaps**, "
        "**Printable EHR Referral Slips with QR Codes**, and **Clinic-wide Real-Time Analytics Dashboard**."
    )

    # Dynamic Rural Clinic Banner
    rural_banner_display = gr.HTML(value=render_rural_banner_html())

    # Global Language Selection Row
    with gr.Row():
        with gr.Column(scale=2):
            language_dropdown = gr.Dropdown(
                choices=LANGUAGE_OPTIONS,
                value="English",
                label="Select Language",
                interactive=True,
            )
        with gr.Column(scale=3):
            gr.Markdown(
                """
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 12px; margin-top: 4px;">
                    <span style="font-size: 14px;">🔒</span>
                    <strong style="color: #0f172a; font-size: 13px;">Works fully offline — no internet required</strong>
                    <p style="color: #64748b; font-size: 12px; margin: 2px 0 0 0;">All 6 regional languages (English, हिंदी, বাংলা, मराठी, తెలుగు, தமிழ்) and SQLite registry run locally on this machine.</p>
                </div>
                """
            )

    # --------------------------------------------------------------
    # TABS (Clean English headings)
    # --------------------------------------------------------------
    with gr.Tabs():

        # ==========================================================
        # TAB 1: Clinical Screening Dashboard & Registry (Default Tab)
        # ==========================================================
        with gr.Tab("📊 Clinical Screening Dashboard & Registry"):

            # Live KPI Stat Cards
            kpi_display = gr.HTML(value=database.render_kpi_cards_html())

            # Visual Analytics Charts Row
            with gr.Row():
                with gr.Column(scale=1):
                    chart_severity_dist = gr.Plot(label="Severity Distribution")
                with gr.Column(scale=1):
                    chart_age_risk = gr.Plot(label="Age Cohort vs Retinopathy Status")

            # Patient Registry Controls
            gr.Markdown("### 📋 Screened Patient Registry & Clinic Records")
            with gr.Row():
                with gr.Column(scale=3):
                    dash_search_input = gr.Textbox(
                        label="🔍 Search Patient by Name or ID",
                        placeholder="e.g. Ramesh Kumar, Sunita, or P-101",
                    )
                with gr.Column(scale=2):
                    dash_urgency_filter = gr.Dropdown(
                        choices=[
                            "All",
                            "🚨 Urgent / Immediate (Grades 3-4)",
                            "🟡 Follow-up / Routine (Grades 1-2)",
                            "🟢 Normal (Grade 0)",
                        ],
                        value="All",
                        label="Filter by Triage Priority",
                    )

            with gr.Row():
                refresh_dash_btn = gr.Button("🔄 Refresh Dashboard", variant="secondary")
                export_reg_csv_btn = gr.Button("📥 Export Registry (CSV)", variant="primary")
                seed_demo_btn = gr.Button("📂 Load 5 Demo Clinical Patients", variant="secondary")

            dash_alert = gr.HTML(value="")

            # Live Patient Registry Table
            registry_table = gr.Dataframe(
                value=database.get_all_patients(),
                headers=[
                    "Rec #", "Patient ID", "Full Name", "Age/Sex", "Eye",
                    "Diabetic History", "Severity Stage", "Triage Urgency", "Confidence", "Screened At"
                ],
                interactive=False,
                wrap=True,
            )

            registry_file_download = gr.File(
                label="📄 Exported Clinic Patient Registry (CSV)",
                interactive=False,
            )

            # Dashboard Initial Load and Bindings
            demo.load(
                fn=update_dashboard_view,
                inputs=[dash_urgency_filter, dash_search_input],
                outputs=[kpi_display, chart_severity_dist, chart_age_risk, registry_table],
            )

            refresh_dash_btn.click(
                fn=update_dashboard_view,
                inputs=[dash_urgency_filter, dash_search_input],
                outputs=[kpi_display, chart_severity_dist, chart_age_risk, registry_table],
            )

            dash_urgency_filter.change(
                fn=update_dashboard_view,
                inputs=[dash_urgency_filter, dash_search_input],
                outputs=[kpi_display, chart_severity_dist, chart_age_risk, registry_table],
            )

            dash_search_input.change(
                fn=update_dashboard_view,
                inputs=[dash_urgency_filter, dash_search_input],
                outputs=[kpi_display, chart_severity_dist, chart_age_risk, registry_table],
            )

            export_reg_csv_btn.click(
                fn=export_dashboard_csv_action,
                inputs=[],
                outputs=[registry_file_download],
            )

            seed_demo_btn.click(
                fn=load_demo_patients_action,
                inputs=[],
                outputs=[kpi_display, chart_severity_dist, chart_age_risk, registry_table, dash_alert],
            )

        # ==========================================================
        # TAB 2: Patient Intake & Screening
        # ==========================================================
        with gr.Tab("👤 Patient Intake & Screening"):

            disclaimer_output = gr.HTML(value=render_disclaimer_html(MESSAGES["en"]["disclaimer"]))

            with gr.Row():
                # Left Column: Patient Intake Form + Image Upload
                with gr.Column(scale=1):
                    gr.Markdown("#### 📝 Step 1: Patient Demographics & Clinical History")
                    with gr.Row():
                        patient_name_input = gr.Textbox(
                            label="Full Name",
                            placeholder="e.g. Ramesh Kumar",
                            value="Ramesh Kumar",
                        )
                        patient_id_input = gr.Textbox(
                            label="Patient ID / OPD No.",
                            placeholder="e.g. P-1042",
                            value="P-1042",
                        )

                    with gr.Row():
                        patient_age_input = gr.Number(
                            label="Age (Years)",
                            value=54,
                            precision=0,
                        )
                        patient_gender_input = gr.Radio(
                            choices=["Male", "Female", "Other"],
                            value="Male",
                            label="Gender",
                        )

                    with gr.Row():
                        patient_contact_input = gr.Textbox(
                            label="Phone / Mobile (Optional)",
                            placeholder="e.g. 9876543210",
                        )
                        patient_eye_input = gr.Radio(
                            choices=["Right Eye (OD)", "Left Eye (OS)"],
                            value="Right Eye (OD)",
                            label="Eye Examined",
                        )

                    with gr.Row():
                        patient_diab_dur_input = gr.Dropdown(
                            choices=["Non-Diabetic", "< 1 year", "1 - 5 years", "5 - 10 years", "> 10 years", "Unknown"],
                            value="5 - 10 years",
                            label="Duration of Diabetes",
                        )
                        patient_sugar_input = gr.Textbox(
                            label="Blood Sugar (mg/dL)",
                            placeholder="e.g. 175",
                            value="175",
                        )
                        patient_htn_input = gr.Radio(
                            choices=["No", "Yes", "Unknown"],
                            value="Yes",
                            label="Hypertension (High BP)",
                        )

                    gr.Markdown("#### 📷 Step 2: Retinal Fundus Photograph")
                    image_input = gr.Image(
                        type="pil",
                        label="Upload Retinal Fundus Photograph",
                        elem_classes=["output-image"],
                    )

                    analyse_btn = gr.Button("🔍 Analyse Retina & Register Patient", variant="primary", size="lg")

                    if available_single_examples:
                        gr.Examples(
                            examples=available_single_examples,
                            inputs=image_input,
                            label="Quick Clinical Patient Samples",
                        )

                # Right Column: Diagnostic Findings, Grad-CAM & Slip
                with gr.Column(scale=1):
                    gr.Markdown("#### 🔍 Step 3: Diagnostic Findings & Lesion Localization")
                    gradcam_output = gr.Image(
                        type="pil",
                        label="Grad-CAM Lesion Localization (Model Attention)",
                        interactive=False,
                        elem_classes=["output-image"],
                    )

                    opacity_slider = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=40,
                        step=5,
                        label="🎚️ Heatmap Opacity (%) (0% = Raw Retina, 100% = Pure Spotlight)",
                        interactive=True,
                    )

                    caption_output = gr.Textbox(
                        label="Lesion Explanation / Model Focus",
                        lines=2,
                        interactive=False,
                    )

            # Registration Status Alert
            intake_status_alert = gr.HTML(value="")

            # Urgency Badge & Clinical Recommendation
            gr.Markdown("### 🏥 Patient Triage & Recommended Action")
            urgency_badge_output = gr.HTML(
                value="""
                <div style="background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 10px; padding: 18px; text-align: center; color: #64748b;">
                    <p style="font-size: 15px; margin: 0; font-weight: 600;">📷 Complete patient details and upload fundus photograph to begin screening.</p>
                </div>
                """
            )

            with gr.Row():
                with gr.Column(scale=1):
                    patient_message_output = gr.Markdown(
                        value="*Patient-friendly explanation will appear here after screening.*"
                    )
                with gr.Column(scale=1):
                    summary_output = gr.Textbox(
                        label="Clinical Summary",
                        lines=3,
                        interactive=False,
                    )
                    confidence_output = gr.Label(
                        num_top_classes=5,
                        label="Confidence Scores Across All 5 Severity Grades",
                    )

            # Printable Referral Slip with QR Code
            gr.Markdown("### 📄 Printable Patient Referral Slip (with Scannable EHR QR Code)")
            with gr.Accordion("Click to View / Download Patient Referral Slip", open=True):
                with gr.Row():
                    with gr.Column(scale=2):
                        generate_slip_btn = gr.Button("🔄 Re-Generate Referral Slip", variant="secondary")
                    with gr.Column(scale=3):
                        slip_download_file = gr.File(
                            label="📥 Download Printable Referral Slip (PNG)",
                            interactive=False,
                        )

                referral_slip_preview = gr.Image(
                    label="Official Referral Prescription Slip Preview",
                    interactive=False,
                )

            # Event Handlers for Tab 2
            intake_inputs = [
                patient_name_input,
                patient_id_input,
                patient_age_input,
                patient_gender_input,
                patient_contact_input,
                patient_eye_input,
                patient_diab_dur_input,
                patient_sugar_input,
                patient_htn_input,
                image_input,
                language_dropdown,
                opacity_slider,
            ]

            intake_outputs = [
                gradcam_output,
                urgency_badge_output,
                summary_output,
                patient_message_output,
                confidence_output,
                caption_output,
                disclaimer_output,
                referral_slip_preview,
                slip_download_file,
                intake_status_alert,
            ]

            analyse_btn.click(
                fn=run_patient_intake_screening,
                inputs=intake_inputs,
                outputs=intake_outputs,
            )

            opacity_slider.change(
                fn=on_opacity_change,
                inputs=[opacity_slider],
                outputs=[gradcam_output],
            )

            generate_slip_btn.click(
                fn=on_generate_slip_click,
                inputs=[
                    patient_name_input,
                    patient_id_input,
                    patient_age_input,
                    patient_gender_input,
                    patient_eye_input,
                    patient_diab_dur_input,
                    patient_sugar_input,
                    patient_htn_input,
                    language_dropdown,
                ],
                outputs=[referral_slip_preview, slip_download_file],
            )

            # Dynamic Language Update Event
            language_dropdown.change(
                fn=on_language_change_global,
                inputs=[
                    language_dropdown,
                    patient_name_input,
                    patient_id_input,
                    patient_age_input,
                    patient_gender_input,
                    patient_contact_input,
                    patient_eye_input,
                    patient_diab_dur_input,
                    patient_sugar_input,
                    patient_htn_input,
                    image_input,
                    opacity_slider,
                ],
                outputs=[
                    rural_banner_display,
                    gradcam_output,
                    urgency_badge_output,
                    summary_output,
                    patient_message_output,
                    confidence_output,
                    caption_output,
                    disclaimer_output,
                    referral_slip_preview,
                    slip_download_file,
                    intake_status_alert,
                ],
            )

        # ==========================================================
        # TAB 3: Camp Mode -- Rapid Batch Screening
        # ==========================================================
        with gr.Tab("🏕️ Camp Mode — Rapid Batch Screening"):

            gr.Markdown("### 🏥 Rural Health Camp Mass Screening Mode")
            gr.Markdown(
                "Upload multiple fundus photographs from a community health camp session. "
                "The system rapidly classifies all patients, prioritizes cases by referral urgency, "
                "and generates an exportable CSV clinical report."
            )

            with gr.Row():
                with gr.Column(scale=3):
                    batch_files_input = gr.File(
                        file_count="multiple",
                        file_types=["image"],
                        label="📁 Upload Multiple Fundus Images",
                    )
                with gr.Column(scale=1):
                    batch_run_btn = gr.Button("⚡ Run Camp Batch Screening", variant="primary", size="lg")
                    load_demo_batch_btn = gr.Button("📂 Load 5 Demo Patients", variant="secondary")

            batch_summary_output = gr.HTML(
                value=render_summary_banner_html("Upload fundus images and click 'Run Camp Batch Screening'")
            )

            gr.Markdown("#### 📋 Prioritized Triage List (Critical Cases First)")
            batch_table_output = gr.Dataframe(
                headers=["Patient ID", "Severity", "Urgency Level", "Confidence"],
                datatype=["str", "str", "str", "str"],
                interactive=False,
                wrap=True,
            )

            with gr.Row():
                with gr.Column(scale=1):
                    download_batch_csv_btn = gr.Button("📥 Download Report (CSV)", variant="primary")
                with gr.Column(scale=2):
                    batch_csv_file_output = gr.File(
                        label="📄 Exported Clinical Report (CSV)",
                        interactive=False,
                    )

            def on_batch_run(files, lang):
                return run_batch_camp_screening(files, lang)

            batch_run_btn.click(
                fn=on_batch_run,
                inputs=[batch_files_input, language_dropdown],
                outputs=[batch_summary_output, batch_table_output, batch_csv_file_output],
            )

            load_demo_batch_btn.click(
                fn=load_5_sample_patients,
                inputs=[],
                outputs=[batch_files_input],
            )

            download_batch_csv_btn.click(
                fn=on_batch_run,
                inputs=[batch_files_input, language_dropdown],
                outputs=[batch_summary_output, batch_table_output, batch_csv_file_output],
            )

    # Reference protocol
    gr.Markdown(SEVERITY_REFERENCE_MD)


# ------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        css=custom_css,
    )
