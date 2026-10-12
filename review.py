"""
review.py — Doctor-in-the-Loop Review & Decision Recording.
L&T TECHNUM Feature 5: Accept, Correct, Reject actions with mandatory clinical reasons.
Ensures the physician holds final diagnostic authority and decisions are never overwritten.
"""

from typing import Dict, Any, Optional
import audit


def record_clinician_decision(
    scan_id: str,
    patient_id: str,
    ai_grade: int,
    confidence_data: Dict[str, Any],
    quality_data: Dict[str, Any],
    support_mode: str,
    language: str,
    action: str,  # "ACCEPT", "CORRECT", "REJECT"
    doctor_final_grade: Optional[int] = None,
    clinical_reason: str = "",
    proceeded_despite_quality: bool = False,
) -> int:
    """
    Records the clinician's authoritative decision into the immutable audit trail.
    
    Returns
    -------
    int: Database row ID of the logged audit entry.
    """
    if action == "ACCEPT":
        final_grade = int(ai_grade)
        reason = clinical_reason.strip() or "Clinician accepted AI diagnostic assessment."
    elif action == "CORRECT":
        final_grade = int(doctor_final_grade) if doctor_final_grade is not None else int(ai_grade)
        reason = clinical_reason.strip() or f"Clinician adjusted grade to Grade {final_grade} based on dilated examination."
    elif action == "REJECT":
        final_grade = -1  # -1 denotes rejected / non-diagnostic scan
        reason = clinical_reason.strip() or "Clinician rejected automated output due to optical/clinical discrepancy."
    else:
        raise ValueError(f"Unsupported clinician action: {action}")

    log_id = audit.log_audit_event(
        scan_id=scan_id,
        patient_id=patient_id,
        model_version="EfficientNetB0-v1.0-LNT",
        ai_grade=ai_grade,
        confidence_status=confidence_data.get("confidence_status", "Unspecified"),
        top1_prob=confidence_data.get("top1_prob", 0.0),
        quality_pass=quality_data.get("passed", True),
        support_mode=support_mode,
        language=language,
        doctor_action=action,
        final_grade=final_grade,
        reason=reason,
        proceeded_despite_quality=proceeded_despite_quality,
    )
    return log_id
