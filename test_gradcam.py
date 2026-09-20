"""
test_gradcam.py -- Smoke test for Grad-CAM explainability.

Creates synthetic fundus images at different brightness levels (simulating
different "severity" appearances) and confirms:
  - generate_gradcam() returns a PIL Image of the correct size
  - The heatmap is non-trivial (not all zeros / all ones)
  - The overlay looks plausible (pixel values in [0, 255])

Run: python test_gradcam.py
"""

import os
import sys

# Suppress TF noise
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
from pathlib import Path
from PIL import Image

from predict import predict, model, CLASS_LABELS
from gradcam import generate_gradcam, get_caption


def make_fundus(color_rgb, size=400):
    """Create a synthetic circular fundus image with the given background colour."""
    arr = np.zeros((size, size, 3), dtype=np.uint8)
    cx, cy, r = size // 2, size // 2, size // 2 - 10
    Y, X = np.ogrid[:size, :size]
    mask = (X - cx) ** 2 + (Y - cy) ** 2 < r ** 2
    arr[mask] = color_rgb
    return Image.fromarray(arr)


def print_bar(label, value, width=30):
    bar = "#" * int(value * width)
    print(f"    {label:<20} {value*100:5.1f}%  {bar}")


SYNTHETIC_CASES = [
    ("dark_red_fundus",    [160, 40, 30]),   # dark red -- typical healthy-ish fundus
    ("bright_fundus",      [200, 100, 80]),  # brighter -- mid-tone
    ("pale_fundus",        [220, 160, 140]), # very pale -- unusual
]

out_dir = Path("sample_images")
out_dir.mkdir(exist_ok=True)

print("=" * 65)
print("Grad-CAM Smoke Test")
print("=" * 65)

all_passed = True
for name, colour in SYNTHETIC_CASES:
    print(f"\n[Test] {name}")

    img = make_fundus(colour)
    save_path = out_dir / f"{name}.png"
    img.save(save_path)

    # --- Predict ---
    idx, label, scores = predict(img)
    caption = get_caption(idx)
    print(f"  Prediction : [{idx}] {label}")
    for cls, sc in scores.items():
        print_bar(cls, sc)

    # --- Grad-CAM ---
    overlay = generate_gradcam(img, model, idx)

    # Validate output
    ok = True
    if not isinstance(overlay, Image.Image):
        print("  FAIL: generate_gradcam did not return a PIL Image")
        ok = False
    else:
        w, h = overlay.size
        if w != 224 or h != 224:
            print(f"  FAIL: Expected 224x224, got {w}x{h}")
            ok = False
        arr = np.array(overlay)
        if arr.min() == arr.max():
            print("  FAIL: Overlay is flat (all same value) -- heatmap may be trivial")
            ok = False
        if arr.max() > 255 or arr.min() < 0:
            print("  FAIL: Pixel values out of [0, 255] range")
            ok = False

    if ok:
        overlay.save(out_dir / f"{name}_gradcam.png")
        print(f"  Grad-CAM  : OK -- saved to sample_images/{name}_gradcam.png")
        print(f"  Caption   : {caption[:80]}...")
    else:
        all_passed = False

print("\n" + "=" * 65)
if all_passed:
    print("All Grad-CAM tests PASSED.")
    print("Open the PNG files in sample_images/ to visually inspect the overlays.")
    print("Run `python app.py` to launch the full interactive UI.")
else:
    print("Some tests FAILED -- review output above.")
