"""
adaptive.py — Adaptive Clinical Support Modes & Presentation Formatting.
L&T TECHNUM Feature 3: Supports Detailed vs. Concise clinician views,
adapts by urgency level (Grade 3-4 front-and-center), and works 100% offline.
"""

from typing import Dict, Any

TIMELINES = {
    0: "Annual routine rescreening (12 months).",
    1: "Routine ophthalmic checkup within 6 months.",
    2: "Specialist dilated fundus examination within 2 weeks.",
    3: "URGENT: Retina specialist review within 3 days.",
    4: "EMERGENCY: Immediate vitreoretinal intervention within 24-48 hours.",
}

LESION_HINTS = {
    0: "Uniform retinal background, sharp optic disc contours, and clear macula without microvascular disruption.",
    1: "Isolated tiny red capillary microaneurysms in parafoveal loops. Early signs of pericyte loss.",
    2: "Multiple blot/flame hemorrhages, hard lipid exudate clusters, and focal venous dilation.",
    3: "Severe intraretinal microvascular abnormalities (IRMA), venous beading in multiple quadrants, and widespread capillary dropout.",
    4: "Neovascularization of the optic disc or elsewhere (NVD/NVE), preretinal/vitreous hemorrhage, and fibrovascular traction.",
}


def format_adaptive_report(
    grade: int,
    label: str,
    confidence_data: Dict[str, Any],
    quality_data: Dict[str, Any],
    support_mode: str = "Detailed",
    show_evidence: bool = True,
) -> Dict[str, Any]:
    """
    Constructs adaptive clinical decision support text and HTML components.
    
    Parameters
    ----------
    grade : int (0 to 4)
    label : str
    confidence_data : dict
    quality_data : dict
    support_mode : "Detailed" or "Concise"
    show_evidence : bool
    """
    top1_pct = f"{confidence_data.get('top1_prob', 0.0) * 100:.1f}%"
    conf_status = confidence_data.get("confidence_status", "Unspecified")
    action_timeline = TIMELINES.get(grade, "Clinical review as indicated.")
    badge_color = confidence_data.get("badge_color", "#0d9488")
    
    uncertainty_banner = ""
    if confidence_data.get("is_uncertain"):
        reason = confidence_data.get("uncertainty_reason", "Borderline classification probability.")
        uncertainty_banner = f"""
        <div style="background:#fff7ed; border-left:4px solid #ea580c; padding:8px 12px; margin:6px 0; border-radius:4px;">
            <strong style="color:#c2410c; font-size:12px;">⚠️ Clinical Uncertainty Flag:</strong>
            <span style="color:#9a3412; font-size:11.5px; margin-left:4px;">{reason}</span>
        </div>
        """

    # 1. Concise Mode (Fast-paced outpatient / triage focus)
    if support_mode == "Concise":
        urgency_prefix = "🚨 URGENT ACTION: " if grade >= 3 else "Action Timeline: "
        html_content = f"""
        <div style="background:#ffffff; border:1px solid #cbd5e1; border-left:5px solid {badge_color}; padding:10px 14px; border-radius:8px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:16px; font-weight:800; color:#0f172a;">Grade {grade}: {label}</span>
                <span style="font-size:12px; font-weight:700; color:{badge_color}; background:#f1f5f9; padding:2px 8px; border-radius:10px;">
                    {conf_status} ({top1_pct})
                </span>
            </div>
            {uncertainty_banner}
            <div style="font-size:13px; font-weight:700; color:#b91c1c; margin-top:6px;">
                {urgency_prefix}{action_timeline}
            </div>
            <div style="font-size:11px; color:#64748b; margin-top:4px;">
                Entropy: {confidence_data.get('entropy', 0.0)} | Quality Score: {quality_data.get('quality_score', 100)}/100
            </div>
        </div>
        """
        return {
            "mode": "Concise",
            "html": html_content,
            "markdown": html_content,
            "timeline": action_timeline,
            "evidence_displayed": show_evidence,
        }

    # 2. Detailed Mode (In-depth diagnostic & pathological review)
    urgency_top = ""
    if grade >= 3:
        urgency_top = f"""
        <div style="background:#fef2f2; border:1px solid #f87171; border-radius:6px; padding:10px 14px; margin-bottom:8px;">
            <div style="color:#991b1b; font-weight:800; font-size:13px;">🚨 CRITICAL URGENCY TIMELINE: Fast-track referral required</div>
            <div style="color:#7f1d1d; font-size:12px; margin-top:2px;">{action_timeline}</div>
        </div>
        """

    lesion_text = LESION_HINTS.get(grade, "")

    html_content = f"""
    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:14px; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
        {urgency_top}
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
            <span style="font-size:18px; font-weight:800; color:#0f172a;">Grade {grade}: {label}</span>
            <span style="background:{badge_color}20; color:{badge_color}; font-weight:700; font-size:12px; padding:3px 10px; border-radius:12px;">
                {conf_status} ({top1_pct})
            </span>
        </div>
        {uncertainty_banner}
        <div style="margin:10px 0 6px 0;">
            <div style="font-size:12px; font-weight:700; color:#475569; text-transform:uppercase;">Pathological Biomarkers & Features:</div>
            <p style="font-size:12.5px; color:#334155; margin:3px 0; line-height:1.4;">{lesion_text}</p>
        </div>
        <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:6px; padding:8px 12px; margin:8px 0;">
            <strong style="color:#166534; font-size:12px;">Clinical Action Window:</strong>
            <span style="color:#15803d; font-size:12px; margin-left:6px;">{action_timeline}</span>
        </div>
        <div style="font-size:11px; color:#64748b; margin-top:8px; border-top:1px solid #f1f5f9; pt:4px;">
            <em>{confidence_data.get('limits_note', '')}</em>
        </div>
    </div>
    """

    return {
        "mode": "Detailed",
        "html": html_content,
        "markdown": html_content,
        "timeline": action_timeline,
        "evidence_displayed": show_evidence,
    }
