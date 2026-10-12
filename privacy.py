"""
privacy.py — Data Privacy, De-identification & Algorithmic Fairness.
L&T TECHNUM Feature 7: Salted SHA-256 patient de-identification,
zero-raw-image retention policy, and demographic subgroup bias analysis.
"""

import hashlib
import os
from typing import Dict, Any, List
import pandas as pd

# Persistent static salt for reproducible de-identification
_SYSTEM_SALT = os.environ.get("NETRASCREEN_SALT", "LNT_TECHNUM_SALT_2026_DR_SCREEN").encode("utf-8")

PRIVACY_MANIFESTO = """
### 🛡️ Privacy & Responsible AI Architecture
- **Zero Raw Image Retention by Default:** Scans are processed in volatile memory. Images are only saved if the attending clinician explicitly opts in via 'Save scan for review'.
- **De-identified Audit Logging:** Patient identifiers (Name/OPD ID) are cryptographically hashed using salted SHA-256 before insertion into the audit log. The raw identity never leaves the secure local clinical session.
- **Data Sovereignty:** All inference, Grad-CAM generation, and audit logging execute 100% locally on device CPU. No patient health information (PHI) is transmitted over external networks.
- **Fairness & Non-Discrimination:** Triage rules apply objective ICDR ophthalmic standards regardless of patient demographic cohort.
"""


def hash_patient_id(patient_id: str) -> str:
    """Produces a secure, irreversible 12-character salted SHA-256 hash."""
    clean_id = (str(patient_id).strip() or "ANONYMOUS").encode("utf-8")
    return hashlib.sha256(clean_id + _SYSTEM_SALT).hexdigest()[:12]


def evaluate_subgroup_bias(eval_records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Computes diagnostic accuracy, referable sensitivity, and specificity across demographic cohorts.
    
    Parameters
    ----------
    eval_records : list of dicts with keys: 'age', 'gender', 'true_grade', 'pred_grade'
    """
    if not eval_records:
        return pd.DataFrame(columns=["Subgroup", "Cohort", "Count", "Accuracy", "Sensitivity (Referable)", "Specificity"])

    df = pd.DataFrame(eval_records)
    df["age_band"] = pd.cut(df["age"], bins=[0, 45, 60, 120], labels=["<45 Yrs", "45-60 Yrs", ">60 Yrs"])
    df["is_referable_true"] = df["true_grade"] >= 2
    df["is_referable_pred"] = df["pred_grade"] >= 2
    df["correct"] = df["true_grade"] == df["pred_grade"]

    rows = []
    # Evaluate across Gender and Age Bands
    for col, name in [("gender", "Gender Cohort"), ("age_band", "Age Bracket")]:
        for val, group in df.groupby(col, observed=True):
            count = len(group)
            if count == 0:
                continue
            acc = (group["correct"].sum() / count) * 100.0
            
            # Sensitivity (Referable DR: Grade >= 2)
            positives = group["is_referable_true"].sum()
            tp = (group["is_referable_true"] & group["is_referable_pred"]).sum()
            sens = (tp / positives * 100.0) if positives > 0 else 100.0
            
            # Specificity (Non-referable: Grade 0-1)
            negatives = (~group["is_referable_true"]).sum()
            tn = ((~group["is_referable_true"]) & (~group["is_referable_pred"])).sum()
            spec = (tn / negatives * 100.0) if negatives > 0 else 100.0

            rows.append({
                "Subgroup": name,
                "Cohort": str(val),
                "Sample Count": count,
                "Accuracy": f"{acc:.1f}%",
                "Sensitivity (Referable DR)": f"{sens:.1f}%",
                "Specificity": f"{spec:.1f}%",
            })

    return pd.DataFrame(rows)
