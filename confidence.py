"""
confidence.py — Confidence Quantification & Clinical Uncertainty Engine.
L&T TECHNUM Feature 2: Calculates entropy, top-2 probability margins, and model bounds.

Rule: Do not change the predicted grade logic. Provide uncertainty classification
and explicit clinical limitations.
"""

from typing import Dict, Any, List
import numpy as np

LIMITS_OF_RESULT_NOTE = (
    "Limits of this result: Model trained exclusively on macula/disc-centered retinal fundus imagery. "
    "Not calibrated for anterior segment, ultrasound, OCT, or non-retinal ocular conditions. "
    "Confidence scores are sensitive to corneal opacity, mature cataract, and optical artefacts."
)


def compute_uncertainty_metrics(
    scores: Dict[str, float],
    class_labels: List[str],
) -> Dict[str, Any]:
    """
    Computes top-1 probability, top-2 margin, normalized Shannon entropy, and clinical uncertainty.
    
    Parameters
    ----------
    scores : dict
        Mapping from class name to probability float (0.0 to 1.0).
    class_labels : list[str]
        Ordered class labels matching model index.
    """
    probs = np.array([float(scores.get(c, 0.0)) for c in class_labels], dtype=np.float64)
    # Numerical clip & re-normalize
    probs = np.clip(probs, 1e-9, 1.0)
    probs = probs / np.sum(probs)
    
    sorted_indices = np.argsort(probs)[::-1]
    top1_idx = int(sorted_indices[0])
    top2_idx = int(sorted_indices[1])
    
    top1_prob = float(probs[top1_idx])
    top2_prob = float(probs[top2_idx])
    margin = float(top1_prob - top2_prob)
    
    # Normalized Shannon Entropy (0.0 = uniform certainty, 1.0 = maximum ambiguity)
    raw_entropy = -float(np.sum(probs * np.log(probs)))
    max_entropy = float(np.log(len(class_labels)))
    normalized_entropy = float(raw_entropy / max_entropy) if max_entropy > 0 else 0.0
    
    # Clinical Confidence Categorization
    if top1_prob >= 0.85 and margin >= 0.45:
        confidence_status = "High Confidence"
        uncertain = False
        badge_color = "#10b981"  # Emerald
    elif top1_prob >= 0.60 and margin >= 0.25:
        confidence_status = "Moderate Confidence"
        uncertain = False
        badge_color = "#f59e0b"  # Amber
    else:
        confidence_status = "Low Confidence"
        uncertain = True
        badge_color = "#ef4444"  # Rose

    # Boundary check: If top-2 grades are adjacent and close, flag for review
    if margin < 0.20 or top1_prob < 0.60:
        uncertain = True
        uncertainty_reason = (
            f"Uncertain: specialist review recommended. Close classification margin "
            f"between {class_labels[top1_idx]} ({top1_prob*100:.1f}%) and "
            f"{class_labels[top2_idx]} ({top2_prob*100:.1f}%)."
        )
    else:
        uncertainty_reason = ""

    return {
        "top1_prob": round(top1_prob, 4),
        "top2_prob": round(top2_prob, 4),
        "top1_class": class_labels[top1_idx],
        "top2_class": class_labels[top2_idx],
        "margin": round(margin, 4),
        "top2_margin": round(margin, 4),
        "entropy": round(normalized_entropy, 3),
        "confidence_status": confidence_status,
        "is_uncertain": uncertain,
        "uncertainty_reason": uncertainty_reason,
        "badge_color": badge_color,
        "limits_note": LIMITS_OF_RESULT_NOTE,
    }
