"""
quality.py — Pre-inference Image Quality Gate for Retinal Fundus Scans.
L&T TECHNUM Feature 1: Validates blur, exposure, contrast, and retinal FoV.

Rule: If a scan fails, do NOT show a grade. Return quality score, pass/fail,
and human-readable reasons. Configurable threshold dictionary.
"""

from typing import Dict, Any
import cv2
import numpy as np
from PIL import Image

# Configurable clinical thresholds in a single centralized dictionary
QUALITY_THRESHOLDS = {
    "min_laplacian_var": 45.0,      # Below 45 indicates severe optical blur
    "min_brightness": 35.0,         # Mean pixel value below 35 is underexposed / dark
    "max_brightness": 215.0,        # Mean pixel value above 215 is overexposed / washed out
    "min_contrast_michelson": 0.28, # Minimum Michelson contrast across green/red channel
    "min_retina_fov_ratio": 0.20,   # At least 20% circular illuminated retinal mask in frame
}


def assess_scan_quality(
    pil_image: Image.Image,
    thresholds: Dict[str, float] = QUALITY_THRESHOLDS,
) -> Dict[str, Any]:
    """
    Evaluates retinal image quality using purely algorithmic OpenCV filters.
    
    Returns
    -------
    dict:
        quality_score: float (0.0 to 100.0)
        passed: bool
        reasons: list[str] (human-readable diagnostic feedback)
        metrics: dict (raw scalar measurements)
        user_guidance: str
    """
    reasons = []
    
    # Convert PIL to BGR OpenCV array
    rgb = np.array(pil_image.convert("RGB"))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    
    # 1. Blur Detection (Variance of Laplacian)
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if laplacian_var < thresholds["min_laplacian_var"]:
        reasons.append(
            f"Excessive optical blur detected (Variance: {laplacian_var:.1f} < threshold {thresholds['min_laplacian_var']}). "
            f"Please stabilize patient eye and refocus."
        )
        
    # 2. Brightness / Exposure Check
    mean_brightness = float(np.mean(gray))
    if mean_brightness < thresholds["min_brightness"]:
        reasons.append(
            f"Underexposed / severely dark scan (Mean Brightness: {mean_brightness:.1f} < {thresholds['min_brightness']}). "
            f"Increase flash intensity or room darkness."
        )
    elif mean_brightness > thresholds["max_brightness"]:
        reasons.append(
            f"Overexposed / washed out scan (Mean Brightness: {mean_brightness:.1f} > {thresholds['max_brightness']}). "
            f"Reduce flash power to avoid glare saturation."
        )
        
    # 3. Contrast Check (Green channel - critical for retinal vessel tree)
    g_channel = rgb[:, :, 1]
    g_min, g_max = float(np.percentile(g_channel, 2)), float(np.percentile(g_channel, 98))
    michelson_contrast = (g_max - g_min) / (g_max + g_min + 1e-6)
    if michelson_contrast < thresholds["min_contrast_michelson"]:
        reasons.append(
            f"Low vascular contrast (Michelson: {michelson_contrast:.2f} < {thresholds['min_contrast_michelson']}). "
            f"Macula details are indistinct."
        )
        
    # 4. Field of View / Retina-Visible Check
    _, fg_mask = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)
    fov_ratio = float(np.count_nonzero(fg_mask)) / float(gray.size)
    if fov_ratio < thresholds["min_retina_fov_ratio"]:
        reasons.append(
            f"Retinal circular field of view missing or off-center (Illuminated FoV: {fov_ratio*100:.1f}% < {thresholds['min_retina_fov_ratio']*100:.0f}%). "
            f"Align patient pupil directly with optical axis."
        )

    # Compute continuous quality score (0 to 100)
    score_blur = min(40.0, (laplacian_var / (thresholds["min_laplacian_var"] * 2.5)) * 40.0)
    score_exp = 30.0 if (thresholds["min_brightness"] <= mean_brightness <= thresholds["max_brightness"]) else 10.0
    score_fov = min(30.0, (fov_ratio / 0.50) * 30.0)
    total_score = round(max(5.0, min(100.0, score_blur + score_exp + score_fov)), 1)
    
    passed = len(reasons) == 0

    return {
        "passed": passed,
        "quality_score": total_score,
        "reasons": reasons,
        "metrics": {
            "laplacian_var": round(laplacian_var, 2),
            "mean_brightness": round(mean_brightness, 2),
            "michelson_contrast": round(michelson_contrast, 3),
            "fov_ratio": round(fov_ratio, 3),
        },
        "user_guidance": (
            "Scan passes clinical quality gate."
            if passed
            else "Poor quality scan: please recapture or send for manual review."
        )
    }
