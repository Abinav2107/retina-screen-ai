"""
referral_slip.py -- Generates official printable digital patient referral slips
with QR codes, dual retinal imagery, patient demographics, clinical diabetic history,
multi-language advisory, and clinical triage.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
import qrcode

from languages import MESSAGES, get_language_code
from referral import get_patient_message


def _get_font(size: int, bold: bool = False):
    """Load Nirmala font on Windows for multi-language glyph support, or fallback."""
    font_paths = [
        "C:/Windows/Fonts/Nirmala.ttc",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size=size, index=0)
            except Exception:
                try:
                    return ImageFont.truetype(fp, size=size)
                except Exception:
                    pass
    return ImageFont.load_default()


def generate_referral_slip(
    patient_id: str,
    original_image: Image.Image,
    gradcam_image: Image.Image,
    predicted_grade: int,
    confidence_score: float,
    language: str = "en",
    output_filename: str = "patient_referral_slip.png",
    name: str = "",
    age: int = 0,
    gender: str = "",
    eye_examined: str = "Right Eye (OD)",
    diabetic_duration: str = "",
    blood_sugar: str = "",
    hypertension: str = "No",
) -> Tuple[Image.Image, str]:
    """
    Generate an official-looking printable medical referral slip (920x1280 px)
    enriched with patient demographics, clinical history, and scannable EHR QR code.
    """
    lang_code = get_language_code(language)
    conf_norm = confidence_score / 100.0 if confidence_score > 1.0 else confidence_score
    patient_msg = get_patient_message(predicted_grade, conf_norm, language=lang_code)

    # 1. Canvas setup
    w, h = 920, 1280
    canvas = Image.new("RGB", (w, h), color="#ffffff")
    draw = ImageDraw.Draw(canvas)

    # Palette
    color_map = {
        0: {"bg": "#ecfdf5", "border": "#10b981", "banner": "#059669", "icon": "NORMAL"},
        1: {"bg": "#fefce8", "border": "#eab308", "banner": "#d97706", "icon": "ROUTINE"},
        2: {"bg": "#fff7ed", "border": "#f97316", "banner": "#ea580c", "icon": "CONSULT"},
        3: {"bg": "#fef2f2", "border": "#ef4444", "banner": "#dc2626", "icon": "URGENT"},
        4: {"bg": "#fee2e2", "border": "#b91c1c", "banner": "#991b1b", "icon": "IMMEDIATE"},
    }
    triage_theme = color_map.get(predicted_grade, color_map[0])

    # 2. Header Banner
    header_h = 100
    draw.rectangle([(0, 0), (w, header_h)], fill="#0f172a")
    draw.rectangle([(0, header_h - 6), (w, header_h)], fill="#0284c7")

    f_head_main = _get_font(21, bold=True)
    f_head_sub = _get_font(13)
    f_title = _get_font(16, bold=True)

    draw.text((25, 14), "NATIONAL PROGRAMME FOR CONTROL OF BLINDNESS (NPCB)", fill="#38bdf8", font=f_head_main)
    draw.text((25, 45), "PRIMARY EYE CARE TELE-TRIAGE & HOSPITAL REFERRAL SLIP", fill="#ffffff", font=f_title)
    draw.text((25, 72), "Rural Vision Mission • Comprehensive Diabetic Eye Screening Unit", fill="#94a3b8", font=f_head_sub)

    # 3. Patient Demographics & Clinical History Box
    meta_y = 112
    meta_h = 95
    draw.rounded_rectangle([(20, meta_y), (w - 20, meta_y + meta_h)], radius=8, fill="#f8fafc", outline="#cbd5e1", width=1)

    f_meta_lbl = _get_font(10)
    f_meta_val = _get_font(12, bold=True)

    timestamp_str = datetime.now().strftime("%d-%b-%Y  %I:%M %p")
    display_name = f"{name} ({patient_id})" if name and name != patient_id else str(patient_id)
    age_sex_str = f"{age} yrs • {gender}" if age > 0 else (gender or "Adult")
    sugar_str = f"{blood_sugar} mg/dL" if blood_sugar else "Not tested"

    ui_strings = MESSAGES.get(lang_code, MESSAGES["en"]).get("ui", {})
    demog_hdr = ui_strings.get("demographics_heading", "PATIENT DEMOGRAPHICS")
    context_hdr = ui_strings.get("clinical_context_heading", "CLINICAL DIABETIC CONTEXT")

    # Column 1: Demographics
    draw.text((35, meta_y + 10), demog_hdr, fill="#64748b", font=f_meta_lbl)
    draw.text((35, meta_y + 24), display_name[:32], fill="#0f172a", font=f_meta_val)
    draw.text((35, meta_y + 46), f"Age / Sex: {age_sex_str}", fill="#334155", font=_get_font(11, bold=True))
    draw.text((35, meta_y + 68), f"Eye Examined: {eye_examined}", fill="#0284c7", font=_get_font(11, bold=True))

    # Column 2: Clinical Diabetic Context
    draw.text((340, meta_y + 10), context_hdr, fill="#64748b", font=f_meta_lbl)
    draw.text((340, meta_y + 24), f"Diabetes: {diabetic_duration or 'Unknown'}", fill="#0f172a", font=f_meta_val)
    draw.text((340, meta_y + 46), f"Blood Sugar: {sugar_str}", fill="#334155", font=_get_font(11))
    draw.text((340, meta_y + 68), f"Hypertension: {hypertension or 'No'}", fill="#334155", font=_get_font(11))

    # Column 3: Referral & Date
    ref_id = f"REF-2026-{(predicted_grade * 179 + 4821) % 9000 + 1000}"
    draw.text((640, meta_y + 10), "REFERRAL & CAMP METADATA", fill="#64748b", font=f_meta_lbl)
    draw.text((640, meta_y + 24), f"No: {ref_id}", fill="#0284c7", font=f_meta_val)
    draw.text((640, meta_y + 46), f"Date: {timestamp_str}", fill="#334155", font=_get_font(11))
    draw.text((640, meta_y + 68), f"Lang: {language.upper()} • Unit: PHC Camp #4", fill="#64748b", font=_get_font(10))

    # 4. Retinal Imagery Section (Side-by-Side)
    img_y = meta_y + meta_h + 12
    f_sec_hdr = _get_font(13, bold=True)
    draw.text((22, img_y), f"CLINICAL RETINAL EVIDENCE ({eye_examined.upper()})", fill="#0f172a", font=f_sec_hdr)

    box_w = 425
    box_h = 290
    img_box_y = img_y + 20

    # Left image box (Original Fundus)
    draw.rounded_rectangle([(20, img_box_y), (20 + box_w, img_box_y + box_h)], radius=8, fill="#f1f5f9", outline="#cbd5e1", width=1)
    orig_resized = original_image.convert("RGB").resize((236, 236), Image.LANCZOS)
    canvas.paste(orig_resized, (20 + (box_w - 236) // 2, img_box_y + 14))

    f_caption = _get_font(12, bold=True)
    draw.text((20 + (box_w - 236) // 2, img_box_y + 258), f"Original Fundus ({eye_examined})", fill="#0f172a", font=f_caption)

    # Right image box (Grad-CAM Overlay)
    r_x = 20 + box_w + 30
    draw.rounded_rectangle([(r_x, img_box_y), (r_x + box_w, img_box_y + box_h)], radius=8, fill="#f1f5f9", outline="#cbd5e1", width=1)
    grad_resized = gradcam_image.convert("RGB").resize((236, 236), Image.LANCZOS)
    canvas.paste(grad_resized, (r_x + (box_w - 236) // 2, img_box_y + 14))
    draw.text((r_x + (box_w - 236) // 2, img_box_y + 258), "Grad-CAM Lesion Heatmap Overlay", fill="#0f172a", font=f_caption)

    # 5. Prominent Triage Urgency Banner
    triage_y = img_box_y + box_h + 12
    draw.rounded_rectangle(
        [(20, triage_y), (w - 20, triage_y + 115)],
        radius=10,
        fill=triage_theme["bg"],
        outline=triage_theme["border"],
        width=2,
    )

    f_badge_tag = _get_font(11, bold=True)
    f_urg_main = _get_font(19, bold=True)
    f_urg_sub = _get_font(12)

    # Top indicator pill
    pill_w = 190
    draw.rounded_rectangle([(35, triage_y + 12), (35 + pill_w, triage_y + 34)], radius=11, fill=triage_theme["banner"])
    draw.text((45, triage_y + 15), f"TRIAGE: {triage_theme['icon']} PRIORITY", fill="#ffffff", font=f_badge_tag)

    # Severity name and confidence
    sev_text = f"Diagnosis: {patient_msg.severity_name}  •  Confidence: {conf_norm*100:.1f}%  •  Eye: {eye_examined}"
    draw.text((35, triage_y + 42), sev_text, fill="#0f172a", font=f_urg_sub)

    # Action urgency
    draw.text((35, triage_y + 68), patient_msg.urgency, fill=triage_theme["banner"], font=f_urg_main)
    draw.text((35, triage_y + 93), f"Recommended Action Window: {patient_msg.action_timeline}", fill="#334155", font=f_urg_sub)

    # 6. Patient Advisory (Native Language) + Scannable QR Code
    adv_y = triage_y + 126
    adv_hdr = ui_strings.get("advisory_heading", "PATIENT ADVISORY")
    draw.text((22, adv_y), adv_hdr, fill="#0f172a", font=f_sec_hdr)

    card_y = adv_y + 20
    card_h = 230
    draw.rounded_rectangle([(20, card_y), (w - 20, card_y + card_h)], radius=8, fill="#f8fafc", outline="#cbd5e1", width=1)

    # Left: Explanation text (word wrapped)
    f_expl = _get_font(13)
    words = patient_msg.explanation.split(" ")
    lines = []
    curr = []
    for word in words:
        test_line = " ".join(curr + [word])
        if len(test_line) > 55:
            lines.append(" ".join(curr))
            curr = [word]
        else:
            curr.append(word)
    if curr:
        lines.append(" ".join(curr))

    text_y = card_y + 16
    for line in lines[:5]:
        draw.text((35, text_y), line, fill="#1e293b", font=f_expl)
        text_y += 22

    draw.text((35, card_y + 165), f"⏱️ Recommended Window: {patient_msg.action_timeline}", fill="#0f172a", font=_get_font(12, bold=True))
    draw.text((35, card_y + 188), f"🩺 Strict Glucose Control: Blood Sugar {sugar_str} • HTN {hypertension}", fill="#475569", font=_get_font(11))

    # Right: Generate and paste scannable QR Code with full patient record
    qr_payload = (
        f"NETRASCREEN CLINICAL EHR SLIP\n"
        f"Ref: {ref_id}\n"
        f"Patient ID: {patient_id}\n"
        f"Name: {name or 'N/A'}\n"
        f"Age/Sex: {age_sex_str}\n"
        f"Eye: {eye_examined}\n"
        f"Diabetic History: {diabetic_duration or 'Unknown'}\n"
        f"Blood Sugar: {sugar_str}\n"
        f"Hypertension: {hypertension}\n"
        f"Date: {timestamp_str}\n"
        f"Severity: {patient_msg.severity_name} (Grade {predicted_grade})\n"
        f"Urgency: {patient_msg.urgency}\n"
        f"Timeline: {patient_msg.action_timeline}\n"
        f"Confidence: {conf_norm*100:.1f}%\n"
        f"Verified via Offline Edge AI Unit"
    )
    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(qr_payload)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0f172a", back_color="#ffffff").resize((150, 150))

    qr_x = w - 195
    canvas.paste(qr_img, (qr_x, card_y + 22))

    f_qr_caption = _get_font(10, bold=True)
    f_qr_sub = _get_font(9)
    draw.text((qr_x, card_y + 180), "SCAN FOR PATIENT EHR", fill="#0f172a", font=f_qr_caption)
    draw.text((qr_x, card_y + 196), "Hospital Intake Verification", fill="#64748b", font=f_qr_sub)

    # 7. Clinical Sign-Off & Official Disclaimer Footer
    foot_y = card_y + card_h + 12
    draw.rounded_rectangle([(20, foot_y), (w - 20, h - 20)], radius=8, fill="#f1f5f9", outline="#e2e8f0", width=1)

    f_disc = _get_font(10)
    disc_text = (
        "OFFICIAL DISCLAIMER: This document is a preliminary screening triage report generated by AI under the National Programme "
        "for Control of Blindness guidelines. It does not constitute a definitive medical diagnosis. All flagged findings must be confirmed by a licensed "
        "ophthalmologist via dilated slit-lamp biomicroscopy / OCT before clinical intervention."
    )
    draw.text((35, foot_y + 10), disc_text[:130], fill="#64748b", font=f_disc)
    draw.text((35, foot_y + 25), disc_text[130:260], fill="#64748b", font=f_disc)
    draw.text((35, foot_y + 40), disc_text[260:], fill="#64748b", font=f_disc)

    # Signatures
    sig_y = foot_y + 65
    draw.line([(35, sig_y), (310, sig_y)], fill="#94a3b8", width=1)
    draw.text((35, sig_y + 4), "Screening Health Worker / ASHA Signature", fill="#475569", font=_get_font(11))

    draw.line([(w - 310, sig_y), (w - 35, sig_y)], fill="#94a3b8", width=1)
    draw.text((w - 310, sig_y + 4), "Receiving Hospital Ophthalmologist Stamp / Seal", fill="#475569", font=_get_font(11))

    # Save to disk
    out_path = Path(output_filename).resolve()
    canvas.save(out_path, format="PNG")
    print(f"[referral_slip.py] Generated referral slip: {out_path}")

    return canvas, str(out_path)
