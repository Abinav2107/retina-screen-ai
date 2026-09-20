"""
create_sample_patients.py -- Generates 5 sample fundus images representing
5 different patients for camp-mode batch testing.
"""

import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw

out_dir = Path("sample_images")
out_dir.mkdir(exist_ok=True)

size = 224
cx, cy, r = size // 2, size // 2, size // 2 - 4
Y, X = np.ogrid[:size, :size]
mask = (X - cx) ** 2 + (Y - cy) ** 2 < r ** 2

# Patient 1: Healthy Dark Red
arr1 = np.zeros((size, size, 3), dtype=np.uint8)
arr1[mask] = [170, 50, 30]
img1 = Image.fromarray(arr1)
img1.save(out_dir / "patient_1_normal.png")

# Patient 2: Normal Bright
arr2 = np.zeros((size, size, 3), dtype=np.uint8)
arr2[mask] = [190, 80, 50]
img2 = Image.fromarray(arr2)
img2.save(out_dir / "patient_2_mild.png")

# Patient 3: High Contrast Mid-Tone
arr3 = np.zeros((size, size, 3), dtype=np.uint8)
arr3[mask] = [185, 65, 45]
img3 = Image.fromarray(arr3)
draw3 = ImageDraw.Draw(img3)
# Optic disc
draw3.ellipse([140, 95, 170, 125], fill=(245, 210, 150))
img3.save(out_dir / "patient_3_moderate.png")

# Patient 4: Retinal lesions / blot simulation
arr4 = np.zeros((size, size, 3), dtype=np.uint8)
arr4[mask] = [160, 45, 30]
img4 = Image.fromarray(arr4)
draw4 = ImageDraw.Draw(img4)
draw4.ellipse([140, 95, 170, 125], fill=(230, 190, 130))
# Lesion spots
for pt in [(80, 80), (85, 90), (100, 140), (110, 130), (70, 110), (120, 70)]:
    draw4.ellipse([pt[0]-4, pt[1]-4, pt[0]+4, pt[1]+4], fill=(70, 10, 10))
img4.save(out_dir / "patient_4_severe.png")

# Patient 5: Pale / Vascular simulation
arr5 = np.zeros((size, size, 3), dtype=np.uint8)
arr5[mask] = [210, 140, 110]
img5 = Image.fromarray(arr5)
draw5 = ImageDraw.Draw(img5)
draw5.ellipse([135, 90, 165, 120], fill=(255, 230, 180))
img5.save(out_dir / "patient_5_pdr.png")

print(f"Created 5 sample patient images in {out_dir.resolve()}")
