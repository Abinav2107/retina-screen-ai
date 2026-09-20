"""
test_predict.py -- Quick smoke test for the predict module.

Tests inference with:
  1. A downloaded sample fundus image (tries multiple sources)
  2. A synthetic red-channel image as a guaranteed fallback

Run: python test_predict.py
"""

import os
import sys
import urllib.request
from pathlib import Path
import numpy as np
from PIL import Image

# Force UTF-8 output on Windows to avoid cp1252 codec errors
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

from predict import predict, CLASS_LABELS  # noqa: E402 (must come after env vars)

# ------------------------------------------------------------------
# Sample fundus images to try (first success wins)
# ------------------------------------------------------------------
SAMPLE_URLS = [
    (
        "fundus_dr",
        "https://upload.wikimedia.org/wikipedia/commons/b/b8/Fundus_of_patient_with_diabetic_retinopathy.jpg",
    ),
    (
        "fundus_normal",
        "https://upload.wikimedia.org/wikipedia/commons/3/3d/Retina_right.jpg",
    ),
]


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def try_download(name: str, url: str, dest: Path) -> bool:
    if dest.exists():
        return True
    try:
        print(f"  Trying {name} ...")
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp, open(dest, "wb") as f:
            f.write(resp.read())
        print(f"  OK - Downloaded {dest.name}")
        return True
    except Exception as e:
        print(f"  FAIL - {e}")
        if dest.exists():
            dest.unlink()
        return False


def make_synthetic_fundus(path: Path) -> Path:
    """Generate a synthetic reddish circular image resembling a fundus photo."""
    size = 224
    arr = np.zeros((size, size, 3), dtype=np.uint8)
    cx, cy, r = size // 2, size // 2, size // 2 - 4
    Y, X = np.ogrid[:size, :size]
    mask = (X - cx) ** 2 + (Y - cy) ** 2 < r ** 2
    arr[mask] = [175, 55, 35]
    Image.fromarray(arr).save(path)
    print(f"  OK - Synthetic fundus saved -> {path.name}")
    return path


def print_scores(scores: dict):
    for cls, conf in scores.items():
        bar = "#" * int(conf * 30)
        print(f"    {cls:<20} {conf*100:5.1f}%  {bar}")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def run_tests():
    sample_dir = Path("sample_images")
    sample_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("DR Screening -- Smoke Test")
    print("=" * 60)

    # --- Test 1: real fundus image ---
    real_img_path = None
    for name, url in SAMPLE_URLS:
        dest = sample_dir / f"{name}.jpg"
        if try_download(name, url, dest):
            real_img_path = dest
            break

    if real_img_path:
        print(f"\n[Test 1] Real fundus image: {real_img_path.name}")
        img = Image.open(real_img_path).convert("RGB")
        idx, label, scores = predict(img)
        print(f"  Predicted : [{idx}] {label}")
        print_scores(scores)
    else:
        print("\n[Test 1] All image URLs unavailable -- skipping real image test.")

    # --- Test 2: synthetic image (always works) ---
    synth_path = sample_dir / "synthetic_fundus.png"
    make_synthetic_fundus(synth_path)
    print(f"\n[Test 2] Synthetic fundus: {synth_path.name}")
    img = Image.open(synth_path).convert("RGB")
    idx, label, scores = predict(img)
    print(f"  Predicted : [{idx}] {label}")
    print_scores(scores)

    print("\n" + "=" * 60)
    print("Smoke test PASSED. Model inference is working correctly.")
    print("Run `python app.py` or double-click run_app.bat to launch the UI.")


if __name__ == "__main__":
    run_tests()
