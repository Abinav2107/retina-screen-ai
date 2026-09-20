# 🔬 NetraScreen — AI Diabetic Retinopathy Screening Assistant & Clinical Registry

> **An edge-ready, offline AI tele-ophthalmology screening platform that grades diabetic retinopathy from retinal fundus photographs, highlights lesions via Grad-CAM, delivers 6-language patient advisory, issues scannable EHR referral slips, and manages epidemiological camp screening registries.**

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![TensorFlow 2.x](https://img.shields.io/badge/TensorFlow-2.21-FF6F00.svg?logo=tensorflow&logoColor=white)](https://tensorflow.org)
[![Keras 3.x](https://img.shields.io/badge/Keras-3.15-D00000.svg?logo=keras&logoColor=white)](https://keras.io)
[![Gradio 6.x](https://img.shields.io/badge/Gradio-6.28-orange.svg?logo=gradio&logoColor=white)](https://gradio.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Offline Ready](https://img.shields.io/badge/Offline-100%25%20Edge%20Ready-success.svg)]()

---

## 📌 Overview & Real-World Impact

India is home to over **101 million citizens living with diabetes**, yet the country has fewer than **25,000 ophthalmologists**—nearly 70% of whom practice exclusively in metropolitan areas. Over **65% of rural Primary Health Centres (PHCs)** operate in connectivity-constrained zones with zero or unstable internet access.

By the time a rural diabetic patient notices vision impairment from **Diabetic Retinopathy (DR)**, irreversible capillary closure or retinal detachment has often already occurred. 

**NetraScreen** bridges this critical healthcare divide by transforming a low-cost laptop and a portable handheld fundus camera into an autonomous tele-ophthalmology triage station. Operating **100% offline**, it classifies DR across the 5 international clinical severity stages in **under 180 ms**, provides sub-millisecond **Grad-CAM visual explainability**, communicates empathetically in **6 regional Indian languages**, prints a physical **prescription referral slip with an EHR QR code**, and maintains an indexed local **patient camp registry**.

---

## 🌟 Key Features

- 🧠 **Pretrained EfficientNetB0 Classifier**: Fine-tuned on authentic clinical fundus imagery (`manudaza/retinal-triage-efficientnetb0`), categorizing retinas across all 5 ICDR severity stages (Grade 0: No DR to Grade 4: Proliferative DR).
- 🔍 **Explainable Grad-CAM Heatmaps**: Uses `tf.GradientTape` on the final convolutional layer (`top_conv`) to highlight microaneurysms, hemorrhages, and vascular proliferation.
- 🎚️ **Instant Opacity Slider (<1 ms Blend)**: Decomposes neural backpropagation from rendering. Backpropagation runs once, while the interactive slider ($0\% \rightarrow 100\%$) executes pure NumPy array blending at **60 FPS** for real-time tissue inspection beneath the AI spotlight.
- 🌐 **Offline Multi-Language Support (6 Regional Languages)**: Zero cloud APIs or internet required. Empathetic patient explanations, recommended action timelines, and disclaimers are preloaded in **English, Hindi (हिंदी), Bengali (বাংলা), Marathi (मराठी), Telugu (తెలుగు), and Tamil (தமிழ்)**.
- 🗣️ **Patient-Friendly Plain Language Advisory**: Translates clinical findings into non-technical language (e.g. explaining microaneurysms as "tiny blood spots at the back of the eye") paired with universal color-coded urgency badges (Green, Yellow, Orange, Red).
- 📄 **Printable Referral Slip with Scannable EHR QR Code**: Generates high-resolution ($920 \times 1280\text{ px}$) physical prescription slips featuring dual retinal images (raw fundus + Grad-CAM heatmap), patient demographics, diabetes context, and a QR code encoding structured EHR JSON for hospital reception scanners.
- 📊 **Clinical Surveillance Dashboard & Registry**: SQLite-backed surveillance registry with real-time KPI metric cards (*Total Screened, Normal, Mild/Mod, Urgent Referrals, Referral Rate %*), Matplotlib distribution charts (*Severity Donut Chart, Age Cohort vs. DR Risk*), and 1-click CSV export.
- 🏕️ **Camp Mode — Rapid Batch Screening**: Multi-image batch processing for high-volume rural screening camps (100+ patients/day), automatically sorting patients in descending urgency order with critical cases pinned to the top.

---

## 🛠️ Tech Stack

| Component | Technology | Role |
|---|---|---|
| **Language** | Python 3.11 | Core runtime environment |
| **Deep Learning** | TensorFlow 2.21 & Keras 3.15 | Preprocessing, inference & gradient tape backprop |
| **Model Backbone** | EfficientNetB0 | Compound-scaled 5.3M parameter feature extractor |
| **Explainability** | Grad-CAM (Custom GradientTape + OpenCV) | Visual attention localization & jet colormapping |
| **Web Interface** | Gradio 6.28 | Modular 3-tab reactive browser application |
| **Edge Database** | SQLite 3 (`patients.db`) | Relational patient demographics & camp registry |
| **Visual Analytics** | Matplotlib 3.11 (Headless `Agg` backend) | Severity donut charts & age cohort risk graphs |
| **Document Engine** | Pillow (PIL) & `qrcode[pil]` | Prescription referral slips & EHR QR codes |
| **Documentation** | ReportLab 5.0 | Publication-grade PDF reporting engine |

---

## 📊 Diabetic Retinopathy Severity Staging Reference

NetraScreen maps predictions directly to the **National Programme for Control of Blindness (NPCB)** guidelines:

| Grade | Severity Stage | Primary Clinical Features | Recommended Rural Triage Window | Urgency Badge |
|:---:|:---|:---|:---|:---:|
| **0** | **No DR** | Clear retina, healthy vascular network | Annual routine checkup | 🟢 Normal |
| **1** | **Mild NPDR** | Microaneurysms only (isolated focal red spots) | Routine checkup within 6 months | 🟡 Routine |
| **2** | **Moderate NPDR** | Microaneurysms, blot haemorrhages, venous beading | See eye doctor within 2 weeks | 🟠 Review |
| **3** | **Severe NPDR** | >20 haemorrhages in 4 quadrants, IRMA, beading | Urgent — eye doctor within 3 days | 🔴 Urgent |
| **4** | **Proliferative DR** | Neovascularisation, vitreous haemorrhage, detachment risk | Immediate referral — risk of vision loss | 🚨 Immediate |

---

## 🚀 Installation & Setup

### 1. Prerequisites
- **Python 3.11** installed on your system.
- Standard computer or laptop (Windows 10/11, macOS, or Linux). No dedicated GPU required; inference runs efficiently on CPU.

### 2. Clone the Repository
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd dr_screening
```

### 3. Create and Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Run the Application
```bash
# Run web interface
python app.py

# Or on Windows, double-click:
run_app.bat
```
Open your browser and navigate to:
👉 **`http://localhost:7860`** (or `http://127.0.0.1:7860`)

---

## 🧪 Verification & Test Suite

Run the automated test scripts to verify all subsystems:

```bash
# 1. Benchmark model accuracy on authentic clinical patient images (Grades 0-4)
python test_clinical_accuracy.py

# 2. Verify Grad-CAM explainability and jet heatmap overlay
python test_gradcam.py

# 3. Test multi-language rendering across all 6 regional languages
python test_multilingual.py

# 4. Verify triage messaging and patient referral rules
python test_referral.py

# 5. Verify Camp Mode batch screening and CSV export
python test_batch.py

# 6. Generate the comprehensive A-to-Z Hackathon Review PDF
python generate_pdf_report.py NetraScreen_Hackathon_Final_Review.pdf
```

---

## 📁 Repository Structure

```text
dr_screening/
├── app.py                          # Gradio web application with 3 modular tabs
├── predict.py                      # Preprocessing & EfficientNetB0 inference
├── gradcam.py                      # Grad-CAM calculation & <1ms cached opacity blending
├── referral.py                     # 5-stage triage rules & plain-language messaging
├── languages.py                    # Offline 6-language dictionary (en, hi, bn, mr, te, ta)
├── database.py                     # SQLite database, KPI calculations & Matplotlib charts
├── referral_slip.py                # Prescription card generator with EHR QR code
├── batch.py                        # Camp mode multi-file batch screening pipeline
├── generate_pdf_report.py          # ReportLab script generating documentation PDF
├── download_real_clinical_data.py  # Downloader for genuine clinical fundus images
├── run_app.bat                     # Windows 1-click batch launcher
├── requirements.txt                # Frozen Python package dependencies
├── .gitignore                      # Git exclusion rules for environments, caches & logs
├── README.md                       # Project documentation & clinical overview
├── NetraScreen_Hackathon_Final_Review.pdf # Comprehensive A-to-Z review & defense PDF
├── sample_images/                  # Authentic clinical fundus photos across Grades 0-4
│   ├── clinical_grade0_no_dr.jpg
│   ├── clinical_grade1_mild_npdr.png
│   ├── clinical_grade2_moderate_npdr.png
│   ├── clinical_grade3_severe_npdr.jpg
│   └── clinical_grade4_proliferative_dr.jpg
└── test_*.py                       # Unit tests for accuracy, batch, gradcam, and i18n
```

---

## ⚠️ Medical & Regulatory Disclaimer

> **IMPORTANT CLINICAL NOTICE**:  
> NetraScreen is an **assistive screening and epidemiological triage tool** designed to aid frontline community health workers and vision technicians under tele-ophthalmology supervision. **It does not constitute a definitive medical diagnosis.**  
> Image quality, optical artefacts, and co-existing ocular pathologies (e.g. cataracts, glaucoma, hypertensive retinopathy) may influence model outputs. **All flagged cases must be clinically confirmed by a licensed ophthalmologist** via dilated slit-lamp biomicroscopy or optical coherence tomography (OCT) prior to therapeutic or surgical intervention.

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
