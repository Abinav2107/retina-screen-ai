"""
referral.py -- Patient communication, rural-health framing, and referral triage
for diabetic retinopathy screening with multi-language support (en, hi, bn, mr, te, ta).
"""

from typing import Tuple, Union
import numpy as np
from languages import (
    MESSAGES,
    LANGUAGE_OPTIONS,
    LANGUAGE_CODE_MAP,
    get_language_code,
    SeverityMessage,
)

# Backward-compatibility alias
PATIENT_GUIDANCE = MESSAGES["en"]


class PatientMessage(dict):
    """
    Structured patient message object supporting dict access, attribute access,
    and tuple unpacking: `explanation, urgency = get_patient_message(...)`.
    """

    def __init__(
        self,
        explanation: str,
        urgency: str,
        urgency_short: str,
        color: str,
        badge_html: str,
        action_timeline: str,
        language: str = "en",
        disclaimer: str = "",
        severity_name: str = "",
    ):
        super().__init__(
            explanation=explanation,
            urgency=urgency,
            urgency_level=urgency,
            urgency_short=urgency_short,
            color=color,
            badge_html=badge_html,
            action_timeline=action_timeline,
            language=language,
            disclaimer=disclaimer,
            severity_name=severity_name,
        )
        self.explanation = explanation
        self.urgency = urgency
        self.urgency_level = urgency
        self.urgency_short = urgency_short
        self.color = color
        self.badge_html = badge_html
        self.action_timeline = action_timeline
        self.language = language
        self.disclaimer = disclaimer
        self.severity_name = severity_name

    def __iter__(self):
        # Allows unpacking as: explanation, urgency = get_patient_message(...)
        yield self.explanation
        yield self.urgency


def _normalize_class_index(severity_class: Union[int, str, float]) -> int:
    """Safely convert class representation (int, str, or float) to index 0-4."""
    if isinstance(severity_class, (int, np.integer)):
        return max(0, min(4, int(severity_class)))
    if isinstance(severity_class, float):
        return max(0, min(4, int(round(severity_class))))
    if isinstance(severity_class, str):
        s = severity_class.strip().lower()
        if s.isdigit():
            return max(0, min(4, int(s)))
        name_map = {
            "no dr": 0,
            "no diabetic retinopathy": 0,
            "normal": 0,
            "mild": 1,
            "mild npdr": 1,
            "moderate": 2,
            "moderate npdr": 2,
            "severe": 3,
            "severe npdr": 3,
            "proliferative": 4,
            "proliferative dr": 4,
            "pdr": 4,
        }
        for k, v in name_map.items():
            if k in s:
                return v
    return 0


# Badge styling palette per color category
BADGE_PALETTES = {
    "green": {
        "bg": "#dcfce7",
        "border": "#86efac",
        "text": "#166534",
    },
    "yellow": {
        "bg": "#fef9c3",
        "border": "#fde047",
        "text": "#854d0e",
    },
    "orange": {
        "bg": "#ffedd5",
        "border": "#fdba74",
        "text": "#9a3412",
    },
    "red": {
        "bg": "#fee2e2",
        "border": "#fca5a5",
        "text": "#991b1b",
    },
}


def generate_badge_html(
    sev_msg: SeverityMessage,
    confidence: float = None,
    timeline_header: str = "RECOMMENDED ACTION TIMELINE",
) -> str:
    """Generate an accessible, high-visibility color-coded HTML urgency badge."""
    icon = sev_msg.badge_icon
    urgency = sev_msg.urgency
    color = sev_msg.color
    palette = BADGE_PALETTES.get(color, BADGE_PALETTES["red"])

    bg = palette["bg"]
    border = palette["border"]
    text_color = palette["text"]
    sev_name = sev_msg.severity_name

    conf_str = f" • Confidence: {confidence*100:.1f}%" if confidence is not None and confidence > 0 else ""

    return f"""
    <div style="
        background: {bg};
        border: 2px solid {border};
        border-radius: 12px;
        padding: 16px 20px;
        margin: 10px 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    ">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 32px; line-height: 1;">{icon}</span>
                <div>
                    <div style="font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: {text_color};">
                        {timeline_header}
                    </div>
                    <div style="font-size: 20px; font-weight: 800; color: {text_color}; margin-top: 2px;">
                        {urgency}
                    </div>
                </div>
            </div>
            <div style="
                background: white;
                border: 1px solid {border};
                border-radius: 20px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: 700;
                color: {text_color};
            ">
                Stage: {sev_name}{conf_str}
            </div>
        </div>
    </div>
    """


def get_patient_message(
    severity_class: Union[int, str, float],
    confidence: float = 1.0,
    language: str = "en",
) -> PatientMessage:
    """
    Produce patient-friendly explanation, urgency level, and color-coded badge
    pulled from MESSAGES[selected_language][severity_key].

    Parameters
    ----------
    severity_class : int | str | float
        The predicted severity class (0 to 4 or string name).
    confidence : float
        Prediction confidence score (0.0 to 1.0).
    language : str
        Language code or name ("en", "hi", "bn", "mr", "te", "ta", etc.).

    Returns
    -------
    PatientMessage (dict-like with tuple unpacking support: explanation, urgency)
        - explanation: Simple non-technical language explanation in chosen language
        - urgency: Urgency recommendation with timeline in chosen language
        - color: color category ("green", "yellow", "orange", "red")
        - badge_html: HTML markup for the visual badge
        - disclaimer: localized medical disclaimer
    """
    idx = _normalize_class_index(severity_class)
    lang_code = get_language_code(language)

    # Pull from MESSAGES dictionary
    lang_dict = MESSAGES.get(lang_code, MESSAGES["en"])
    sev_msg: SeverityMessage = lang_dict.get(idx, lang_dict[0])
    disclaimer = lang_dict.get("disclaimer", MESSAGES["en"]["disclaimer"])
    timeline_header = lang_dict.get("ui", {}).get("timeline_title", "RECOMMENDED ACTION TIMELINE")

    # Normalize confidence to 0..1 range
    conf_norm = confidence / 100.0 if confidence > 1.0 else confidence

    badge_html = generate_badge_html(sev_msg, conf_norm, timeline_header)

    return PatientMessage(
        explanation=sev_msg.explanation,
        urgency=sev_msg.urgency,
        urgency_short=sev_msg.urgency,
        color=sev_msg.color,
        badge_html=badge_html,
        action_timeline=sev_msg.action_timeline,
        language=lang_code,
        disclaimer=disclaimer,
        severity_name=sev_msg.severity_name,
    )
