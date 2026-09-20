"""
download_real_clinical_data.py -- Downloads genuine clinical fundus images
spanning all 5 Diabetic Retinopathy severity levels (Grade 0 to Grade 4).
"""

import urllib.request
from pathlib import Path
from PIL import Image

sample_dir = Path("sample_images")
sample_dir.mkdir(exist_ok=True)

base_url = "https://raw.githubusercontent.com/tansugangopadhyay/Diabetic-Retinopathy-Detection/main/Retinal_blindness_detection_Pytorch-master/sampleimages/"

CLINICAL_SAMPLES = [
    {
        "source": "eye15.jpg",
        "target": "clinical_grade0_no_dr.jpg",
        "expected_grade": 0,
        "label": "Grade 0: No DR (Healthy Retina)",
    },
    {
        "source": "eye11.png",
        "target": "clinical_grade1_mild_npdr.png",
        "expected_grade": 1,
        "label": "Grade 1: Mild NPDR (Early Microaneurysms)",
    },
    {
        "source": "eye17.png",
        "target": "clinical_grade2_moderate_npdr.png",
        "expected_grade": 2,
        "label": "Grade 2: Moderate NPDR (Hemorrhages & Leakage)",
    },
    {
        "source": "eye4.jpg",
        "target": "clinical_grade3_severe_npdr.jpg",
        "expected_grade": 3,
        "label": "Grade 3: Severe NPDR (Extensive Damage)",
    },
    {
        "source": "eye8.jpg",
        "target": "clinical_grade4_proliferative_dr.jpg",
        "expected_grade": 4,
        "label": "Grade 4: Proliferative DR (Sight-Threatening Neovascularisation)",
    },
]

print("Downloading authentic clinical fundus images...")
for item in CLINICAL_SAMPLES:
    src_url = base_url + item["source"]
    dest_path = sample_dir / item["target"]
    req = urllib.request.Request(src_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, open(dest_path, "wb") as f:
        f.write(resp.read())
    # Verify image opens cleanly
    with Image.open(dest_path) as img:
        w, h = img.size
    print(f"  ✓ {item['target']} ({w}x{h}) - {item['label']}")

print("\nAll 5 clinical grade fundus images downloaded successfully!")
