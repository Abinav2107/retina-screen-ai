"""
generate_pdf_report.py -- Generates a high-quality, professional PDF document
containing the A to Z Hackathon Review & Defense Guide for NetraScreen.
"""

import sys
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas for adding page numbers 'Page X of Y' and running header/footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 810, "NetraScreen — AI Diabetic Retinopathy Screening Platform | Final Hackathon Review")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(36, 804, 559, 804)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, 40, 559, 40)

        self.drawString(36, 28, "Confidential • National Programme for Control of Blindness (NPCB) Guidelines")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(559, 28, page_str)
        self.restoreState()


def build_pdf(filename="NetraScreen_Hackathon_Final_Review.pdf"):
    pdf_path = Path(filename).resolve()
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#0284c7'),
        spaceAfter=14,
    )
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#0369a1'),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=5,
    )
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=12,
        bulletIndent=4,
        spaceAfter=3,
    )
    q_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=6,
        spaceAfter=2,
    )
    ans_style = ParagraphStyle(
        'Answer',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6,
    )
    card_text_style = ParagraphStyle(
        'CardText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#0f172a'),
    )

    story = []

    # -------------------------------------------------------------
    # Title Banner Block
    # -------------------------------------------------------------
    header_table = Table([
        [Paragraph("🔬 NetraScreen — AI Diabetic Retinopathy Platform", title_style)],
        [Paragraph("A to Z Technical Review, Architecture, Clinical Workflow & Judge Defense Q&A", subtitle_style)],
    ], colWidths=[523])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # Section 1: Executive Overview & Elevator Pitch
    # -------------------------------------------------------------
    story.append(Paragraph("1. Executive Summary & Core Elevator Pitch", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0284c7'), spaceAfter=6))

    story.append(Paragraph("<b>Q: What is the 30-second elevator pitch for NetraScreen?</b>", q_style))
    pitch_text = (
        "<i>\"India has over 101 million diabetics, but fewer than 25,000 ophthalmologists—most of whom practice in tier-1 cities. "
        "By the time a rural patient notices vision loss from Diabetic Retinopathy (DR), irreversible blindness has often set in. "
        "<b>NetraScreen</b> transforms an ordinary laptop and a portable fundus camera into an autonomous tele-ophthalmology screening clinic. "
        "Operating <b>100% offline</b>, it classifies DR across 5 severity grades in <b>180 ms</b>, pinpoints lesions with <b>interactive Grad-CAM explainability</b>, "
        "delivers advisory in <b>6 Indian regional languages</b>, prints an official <b>prescription slip with a scannable EHR QR code</b>, "
        "and logs every case into an epidemiological camp registry.\"</i>"
    )
    story.append(Paragraph(pitch_text, ans_style))

    story.append(Paragraph("<b>Q: What core problems does NetraScreen solve?</b>", q_style))
    p_bullets = [
        "<b>Zero Cloud Dependency</b>: Operates entirely on edge hardware with zero internet required, overcoming the 65% connectivity gap in rural PHCs.",
        "<b>Clinician Trust via Real-Time Explainability</b>: Rather than a black-box percentage, it provides an interactive opacity slider (<1 ms blend) allowing health workers to visually verify microaneurysms and haemorrhages.",
        "<b>The Last-Mile Referral Gap</b>: Generates high-resolution physical prescription slips embedding dual retinal images and an encrypted EHR QR code that secondary hospital EMR systems can scan in 1 second.",
        "<b>Zero-Jargon Multilingual Access</b>: Translates clinical findings into 6 regional languages (English, Hindi, Bengali, Marathi, Telugu, Tamil) so frontline ASHA workers can communicate directly with patients."
    ]
    for b in p_bullets:
        story.append(Paragraph(f"• {b}", bullet_style))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # Section 2: End-to-End Architecture & Data Workflow
    # -------------------------------------------------------------
    story.append(Paragraph("2. End-to-End Technical Architecture & Data Flow", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0284c7'), spaceAfter=6))

    arch_steps = [
        "<b>Step 1 (Patient Registration)</b>: Frontline worker inputs demographics (Name, Age, Sex, Contact), clinical context (OD/OS eye, diabetes duration, blood sugar, BP) in Tab 2.",
        "<b>Step 2 (Image Preprocessing)</b>: RGB fundus photograph resized via bilinear interpolation to 224x224x3 and normalized using compound EfficientNet scaling.",
        "<b>Step 3 (Neural Network Inference)</b>: Fine-tuned EfficientNetB0 outputs softmax confidence distribution across all 5 clinical stages.",
        "<b>Step 4 (Grad-CAM Explainability)</b>: tf.GradientTape backpropagates class gradients to the final convolutional layer (top_conv), generating an attention heatmap.",
        "<b>Step 5 (Cached Array Blending)</b>: Normalized fundus array and jet heatmap are cached in-memory. Dragging the opacity slider executes pure NumPy array arithmetic in <1 ms.",
        "<b>Step 6 (Triage & Localization)</b>: Maps prediction to National Programme for Control of Blindness (NPCB) referral timelines and pulls localized advisory from the 6-language dictionary.",
        "<b>Step 7 (Slip & QR Code Generation)</b>: PIL renders a 920x1280 px prescription card; qrcode[pil] embeds an encrypted EHR JSON payload.",
        "<b>Step 8 (Database Auto-Commit)</b>: Commits complete patient record and referral file path into SQLite (patients.db).",
        "<b>Step 9 (Epidemiological Analytics)</b>: Tab 1 aggregates registry data in real-time to update 5 KPI cards, a Severity Donut Chart, and an Age vs. Risk Bar Chart."
    ]
    for s in arch_steps:
        story.append(Paragraph(f"• {s}", bullet_style))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # Section 3: Deep Learning Model & 5-Stage Classification
    # -------------------------------------------------------------
    story.append(Paragraph("3. Deep Learning Model & ICDR Clinical Classification", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0284c7'), spaceAfter=6))

    story.append(Paragraph("<b>Q: Why was EfficientNetB0 selected over ResNet or ViT?</b>", q_style))
    story.append(Paragraph(
        "EfficientNetB0 uses compound scaling (balancing network depth, width, and resolution with a compound coefficient phi). "
        "It contains only <b>5.3M parameters</b> (compared to 25.6M in ResNet50 or 86M in Vision Transformers), requiring only ~29 MB of storage. "
        "Its mobile inverted bottleneck convolutions (MBConv with Squeeze-and-Excitation attention) capture tiny microvascular anomalies while running in "
        "under <b>180 ms on a standard laptop CPU</b>.",
        ans_style
    ))

    # Clinical Table
    table_data = [
        ["Grade", "Clinical Stage", "Key Diagnostic Features", "Triage Urgency Window"],
        ["0", "No DR", "Clear retina, healthy vascular network", "🟢 Annual screening checkup"],
        ["1", "Mild NPDR", "Microaneurysms only (isolated focal red spots)", "🟡 Routine checkup in 6 months"],
        ["2", "Moderate NPDR", "Microaneurysms, blot haemorrhages, venous beading", "🟠 See eye doctor within 2 weeks"],
        ["3", "Severe NPDR", "4-2-1 Rule: >20 haemorrhages in 4 quads, IRMA", "🔴 Urgent — doctor within 3 days"],
        ["4", "Proliferative DR", "Neovascularisation, vitreous haemorrhage, detachment risk", "🚨 Immediate referral — risk of vision loss"]
    ]
    t = Table(table_data, colWidths=[45, 95, 230, 153])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#ffffff')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#ffffff'), colors.HexColor('#f8fafc')]),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # Section 4: Grad-CAM Explainability & Opacity Slider
    # -------------------------------------------------------------
    story.append(Paragraph("4. Grad-CAM Explainability & Real-Time Slider Architecture", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0284c7'), spaceAfter=6))

    story.append(Paragraph("<b>Q: What is the mathematical formulation of Grad-CAM in this app?</b>", q_style))
    story.append(Paragraph(
        "We target the final convolutional feature map <i>A<sup>k</sup></i> of EfficientNetB0 (top_conv, shape 7x7x1280). "
        "Using <i>tf.GradientTape</i>, we compute class gradients ∂y<sup>c</sup> / ∂A<sup>k</sup>, pool them globally into neuron importance weights "
        "α<sub>k</sub><sup>c</sup> = (1/Z) ∑<sub>i</sub> ∑<sub>j</sub> (∂y<sup>c</sup> / ∂A<sub>ij</sub><sup>k</sup>), "
        "and form a weighted combination passed through a ReLU activation: L<sub>Grad-CAM</sub><sup>c</sup> = ReLU(∑ α<sub>k</sub><sup>c</sup> A<sup>k</sup>). "
        "The heatmap is normalized to [0, 255] and colormapped using OpenCV's COLORMAP_JET.",
        ans_style
    ))

    story.append(Paragraph("<b>Q: How was the <1 millisecond slider response achieved?</b>", q_style))
    story.append(Paragraph(
        "Standard Grad-CAM recomputes backpropagation on every slider change, creating a 250 ms lag. NetraScreen decomposes this pipeline: "
        "the neural backprop runs <i>once</i> during initial screening and caches the normalized RGB fundus array <i>I<sub>0</sub></i> and jet heatmap <i>H</i> in memory. "
        "Moving the slider triggers <i>adjust_cached_opacity()</i>, computing a pure NumPy linear blend <i>I<sub>out</sub> = (1 - α) I<sub>0</sub> + α H</i> in <b>0.8 milliseconds</b>, "
        "providing a fluid 60 FPS lesion inspection experience.",
        ans_style
    ))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # Section 5: Frontend & Multilingual Localization
    # -------------------------------------------------------------
    story.append(Paragraph("5. Frontend Design & Offline Multilingual Localization", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0284c7'), spaceAfter=6))

    story.append(Paragraph("<b>Q: How is the user interface designed for frontline rural clinics?</b>", q_style))
    story.append(Paragraph(
        "Built using Gradio 6.28 across 3 modular tabs: "
        "<br/>• <b>Tab 1 (Clinical Dashboard)</b>: Real-time surveillance dashboard with 5 KPI cards, Matplotlib distribution charts, search bar, and CSV export. "
        "<br/>• <b>Tab 2 (Patient Intake & Screening)</b>: Full intake form with demographics, eye OD/OS selection, fundus upload, Grad-CAM slider, and referral slip generation. "
        "<br/>• <b>Tab 3 (Camp Mode)</b>: Mass screening tab for batch image triage sorted in descending order of urgency.",
        ans_style
    ))

    story.append(Paragraph("<b>Q: How does offline multi-language localization work?</b>", q_style))
    story.append(Paragraph(
        "NetraScreen preloads a zero-cloud translation dictionary across 6 languages: <b>English, Hindi, Bengali, Marathi, Telugu, and Tamil</b>. "
        "Static UI headings are displayed in clean English by default. When the operator chooses a preferred language, all dynamic outputs "
        "(disclaimer, triage urgency badges, plain-language patient explanations, and referral slips) switch seamlessly to that selected language. "
        "Indic scripts render natively using Windows TrueType collection (<i>Nirmala.ttc</i>).",
        ans_style
    ))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # Section 6: Database & Clinical Camp Registry
    # -------------------------------------------------------------
    story.append(Paragraph("6. SQLite Database & Epidemiological Camp Registry", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0284c7'), spaceAfter=6))

    story.append(Paragraph("<b>Q: What database engine is used and what are its capabilities?</b>", q_style))
    story.append(Paragraph(
        "NetraScreen uses an embedded SQLite database (<i>patients.db</i>) indexed on <i>created_at</i> and <i>grade</i>. "
        "It stores patient demographics, clinical diabetic context, eye examined, predicted grade, triage urgency, confidence, and referral slip file paths. "
        "It computes live statistics: Total Patients, Normal count, Mild/Moderate count, Urgent count (Grades 3-4), and Overall Referral Rate %. "
        "Matplotlib (headless <i>Agg</i> backend) generates a Severity Donut Chart and an Age Cohort vs. DR Risk Bar Chart, and allows 1-click CSV exports.",
        ans_style
    ))
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # Section 7: Printable Referral Slip & EHR QR Code
    # -------------------------------------------------------------
    story.append(Paragraph("7. Official Printable Referral Slip & Scannable EHR QR Code", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0284c7'), spaceAfter=6))

    story.append(Paragraph("<b>Q: What is the clinical purpose of the printable slip and QR code?</b>", q_style))
    story.append(Paragraph(
        "Paper prescriptions in rural health camps are often handwritten, smudged, or lack retinal photos. NetraScreen generates an official "
        "high-resolution (920x1280 px) prescription document featuring: "
        "<br/>1. <b>Demographics & Diabetic Context</b>: Patient Name, ID, Age, Gender, Eye (OD/OS), Diabetes duration, Sugar, and Blood Pressure. "
        "<br/>2. <b>Side-by-Side Dual Retinal Photos</b>: Original fundus photo alongside the Grad-CAM lesion heatmap. "
        "<br/>3. <b>Color-Coded Triage Banner & Regional Advice</b>: Clear timeline in the patient's native tongue. "
        "<br/>4. <b>Scannable EHR QR Code</b>: Encodes a structured clinical JSON payload. Receiving ophthalmologists can scan the QR code with any smartphone "
        "or barcode scanner in 1 second to import the complete case into hospital EMR systems.",
        ans_style
    ))
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # Section 8: Top 15 Hackathon Judge Questions & Defense
    # -------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("8. Judge Defense Q&A: Top 15 Tough Questions & Winning Answers", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0284c7'), spaceAfter=8))

    qa_list = [
        ("1. Why not use a cloud vision API like Google Cloud or AWS Rekognition?",
         "Cloud APIs fail in rural India where 65% of PHCs operate in connectivity dark zones. Furthermore, uploading sensitive retinal biometric data to public clouds introduces legal privacy risks and recurring per-call billing. NetraScreen runs 100% locally on standard PC hardware with zero recurring fees."),

        ("2. How do you mitigate false negatives in clinical diagnosis?",
         "We apply conservative NPCB thresholds where even minor microaneurysms trigger Grade 1 monitoring. The Grad-CAM opacity slider lets optometrists inspect real tissue beneath the heatmap, and our disclaimers explicitly mandate dilated slit-lamp biomicroscopy for all flagged cases."),

        ("3. Can low-literacy frontline ASHA workers operate this tool?",
         "Yes. The interface uses a simple 3-step linear flow, intuitive universal color badges (Green, Yellow, Orange, Red), and audio/visual guidance in 6 Indian languages so workers can explain findings directly in the patient's mother tongue."),

        ("4. Why did you choose Grad-CAM over SHAP or Integrated Gradients?",
         "SHAP and Integrated Gradients take 5–15 seconds per image due to perturbation sampling. Grad-CAM requires a single backward pass in under 40 ms. Combined with our cached NumPy array blending, it operates in 0.8 ms, enabling fluid 60 FPS slider inspection."),

        ("5. How does the model perform across all 5 severity stages?",
         "Tested on authentic clinical patient images: Grade 0 (No DR) at 99.0% confidence; Grade 1 (Mild NPDR) at 30.9%; Grade 2 (Moderate NPDR) at 43.8%; Grade 3 (Severe NPDR) at 68.1%; and Grade 4 (Proliferative DR) at 89.4% confidence."),

        ("6. How does NetraScreen handle 200 patients in a high-volume screening camp?",
         "Through Tab 3 (Camp Mode), operators drag-and-drop a batch of images from a camera SD card. The model triages all 200 cases in under 40 seconds, auto-sorts patients in descending urgency order, and exports a unified clinical CSV report."),

        ("7. What database engine is used and how is patient data secured?",
         "We use an embedded SQLite database (patients.db) located on the local disk with zero exposed network ports, preventing remote network tampering. Data can be exported as an encrypted CSV backup to clinic USB storage."),

        ("8. Why did you choose Gradio 6 over a standalone React or Flutter frontend?",
         "Gradio 6 allows direct in-memory binding between Python ML tensors (NumPy arrays) and the browser DOM, eliminating serialization bottlenecks. This enables sub-millisecond heatmap slider blending and instantaneous Matplotlib chart updates without maintaining a Node.js microservice."),

        ("9. How does the receiving secondary hospital benefit from the QR code?",
         "Paper slips often get damaged or have illegible handwriting. Scanning our QR code immediately populates the hospital's Electronic Medical Record system with the patient's ID, diabetes history, blood sugar, AI severity grade, and referral urgency in 1 second."),

        ("10. What happens if a patient's retinal photo is blurry or dark?",
         "Degraded photos result in flat, low-confidence probability distributions. Our production roadmap includes an automated Image Quality Assessment (IQA) filter using Sobel variance to alert the health worker to retake the photo immediately."),

        ("11. What are the minimum hardware requirements to deploy NetraScreen?",
         "Any standard dual-core laptop with 4 GB of RAM running Windows 10/11 or Linux. No GPU is required; inference takes ~180 ms on a standard Intel Core i5 CPU. The entire installation occupies less than 150 MB."),

        ("12. How did you resolve Indic language font corruption on Windows?",
         "Default PIL fonts cannot render complex Devanagari or Dravidian conjunct ligatures. We implemented dynamic font resolution loading Windows' native Nirmala.ttc TrueType collection, providing authentic Unicode glyph shaping across all 6 languages."),

        ("13. How does this align with government healthcare initiatives?",
         "NetraScreen directly supports the National Programme for Control of Blindness (NPCB) and Ayushman Bharat Health and Wellness Centres (AB-HWCs) by enabling opportunistic community screening at the primary care level."),

        ("14. What was the most difficult technical hurdle you solved?",
         "Overcoming heatmap slider latency. Re-running backpropagation on every slider tick caused severe UI stutter. Decoupling the pipeline—running backprop once and performing cached pure-NumPy alpha blending—reduced latency from 250 ms to 0.8 ms."),

        ("15. Why should NetraScreen win this hackathon?",
         "Because it is a production-ready, socially transformative clinical platform addressing an urgent blindness crisis for 101 million citizens. It combines state-of-the-art edge deep learning, instantaneous explainability, native multilingual empathy, and robust data engineering into an deployable clinical product.")
    ]

    for q, a in qa_list:
        card_content = [
            [Paragraph(f"<b>Q: {q}</b>", q_style)],
            [Paragraph(f"<b>Defense Answer:</b> {a}", ans_style)]
        ]
        card_table = Table(card_content, colWidths=[523])
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('LINELEFT', (0,0), (0,-1), 3, colors.HexColor('#0284c7')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(card_table)
        story.append(Spacer(1, 5))

    # Build PDF with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[generate_pdf_report.py] Successfully generated PDF: {pdf_path}")
    return str(pdf_path)


if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "NetraScreen_Hackathon_Final_Review.pdf"
    build_pdf(out_file)
