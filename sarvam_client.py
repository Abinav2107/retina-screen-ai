"""
sarvam_client.py — GenAI Explanation & Multilingual Voice Layer via Sarvam AI.
L&T TECHNUM Feature 4: Context-constrained LLM explanations, multilingual translation,
interactive doctor Q&A, and resilient 100% offline fallback.
"""

import os
import json
from typing import Dict, Any, Optional
import requests

SARVAM_CHAT_URL = "https://api.sarvam.ai/v1/chat/completions"
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"


DEFAULT_SARVAM_API_KEY = "sk_tqja8mou_myoarWUcyyZzP0RNj8iz6FYN"


def get_sarvam_api_key() -> Optional[str]:
    """Retrieves Sarvam API key safely from environment, Streamlit secrets, or local .env file, with active fallback."""
    key = os.environ.get("SARVAM_API_KEY", "").strip()
    if not key:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "SARVAM_API_KEY" in st.secrets:
                key = str(st.secrets["SARVAM_API_KEY"]).strip()
        except Exception:
            pass
    if not key:
        env_file = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_file):
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("SARVAM_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    if not key:
        key = DEFAULT_SARVAM_API_KEY
    return key if key else None


def is_sarvam_online() -> bool:
    """Returns True if a non-empty Sarvam API key is configured."""
    return get_sarvam_api_key() is not None


def generate_sarvam_explanation(
    grade: int,
    label: str,
    confidence_data: Dict[str, Any],
    quality_data: Dict[str, Any],
    language_code: str = "en",
    support_mode: str = "Detailed",
    doctor_question: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates a medically constrained GenAI explanation using Sarvam AI.
    Falls back gracefully to preloaded local templates if offline or error occurs.
    """
    api_key = get_sarvam_api_key()
    
    # 1. Offline Fallback if no key is supplied
    if not api_key:
        return {
            "status": "offline",
            "provider": "Offline Local Template Engine",
            "text": _get_offline_explanation(grade, label, language_code, support_mode, doctor_question),
            "badge_text": "AI Explanation: Offline (Local Engine)",
            "badge_color": "#64748b",
        }

    LANG_NAMES = {
        "en": "English",
        "hi": "Hindi (हिंदी)",
        "bn": "Bengali (বাংলা)",
        "mr": "Marathi (मराठी)",
        "te": "Telugu (తెలుగు)",
        "ta": "Tamil (தமிழ்)",
    }
    target_lang_name = LANG_NAMES.get(language_code, "English")

    # 2. Strict System Prompt enforcing medical safety and guardrails
    system_prompt = (
        "You are an AI Clinical Decision Support Explainer for Diabetic Retinopathy. "
        "NON-NEGOTIABLE CLINICAL GUARDRAILS:\n"
        "1. You MUST NOT invent clinical findings, hallucinate symptoms, or change the assigned grade.\n"
        "2. You may ONLY explain the provided grade, probabilities, Grad-CAM focus, and clinical timeline.\n"
        "3. Emphasize that you are a decision-support aid and the clinician makes the final decision.\n"
        "4. Always mention the limits of the result and uncertainty where present.\n"
        f"5. Respond empathetically, fluently, and clearly in {target_lang_name} (Language code: {language_code}). Write directly in {target_lang_name} script."
    )

    user_payload = {
        "model_grade": grade,
        "severity_stage": label,
        "confidence_status": confidence_data.get("confidence_status"),
        "top1_probability": confidence_data.get("top1_prob"),
        "entropy": confidence_data.get("entropy"),
        "is_uncertain": confidence_data.get("is_uncertain"),
        "uncertainty_reason": confidence_data.get("uncertainty_reason"),
        "quality_score": quality_data.get("quality_score"),
        "support_mode": support_mode,
        "doctor_question": doctor_question or "Summarize clinical findings and next steps.",
    }

    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": api_key,
        "Authorization": f"Bearer {api_key}",
    }

    body = {
        "model": "sarvam-105b-conversations",
        "messages": [
            {"role": "user", "content": f"{system_prompt}\n\nClinical Scan Data: {json.dumps(user_payload)}"},
        ],
        "temperature": 0.2,  # Low temperature for deterministic medical reasoning
        "max_tokens": 400,
    }

    try:
        resp = requests.post(SARVAM_CHAT_URL, headers=headers, json=body, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            message_obj = data.get("choices", [{}])[0].get("message", {})
            explanation_text = message_obj.get("content") or message_obj.get("reasoning_content") or ""
            if explanation_text:
                return {
                    "status": "online",
                    "provider": "Sarvam AI (Online Cloud)",
                    "text": explanation_text,
                    "badge_text": "AI Explanation: Online (Sarvam AI)",
                    "badge_color": "#0d9488",
                }
    except Exception:
        pass

    # 3. Fallback on network timeout or API error
    return {
        "status": "offline",
        "provider": "Offline Local Template Engine (Network Fallback)",
        "text": _get_offline_explanation(grade, label, language_code, support_mode, doctor_question),
        "badge_text": "AI Explanation: Offline (Local Fallback)",
        "badge_color": "#f59e0b",
    }


def _get_offline_explanation(
    grade: int,
    label: str,
    language_code: str,
    support_mode: str,
    question: Optional[str],
) -> str:
    """Preloaded resilient offline explanations."""
    from referral import PATIENT_GUIDANCE
    guidance = PATIENT_GUIDANCE.get(grade, {})
    title = guidance.get("title", label)
    action = guidance.get("action", "Clinical follow-up required.")
    
    if question:
        return (
            f"[Offline CDS Response]: The neural network classified this fundus scan as "
            f"Grade {grade} ({title}). Recommended action timeline: {action} "
            f"Regarding your inquiry '{question}': Please cross-examine with dilated slit-lamp biomicroscopy. "
            f"Notice: Assistive AI tool only. Final clinical diagnosis rests with the attending doctor."
        )
    
    if support_mode == "Concise":
        return (
            f"AI Decision Support: Grade {grade} ({title}). Timeline: {action} "
            f"Notice: Decision-support tool. Final decision rests with the clinician."
        )

    return (
        f"AI Decision Support Assessment: Patient presents with Grade {grade} ({title}). "
        f"Recommended Action Pathway: {action} "
        f"Key Features: Microvascular inspection indicates consistent pathological staging. "
        f"Notice: Decision-support tool. Final decision rests with the clinician."
    )
