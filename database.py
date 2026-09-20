"""
database.py -- Local SQLite database, clinical registry, KPI metrics,
and Matplotlib visual analytics for the Diabetic Retinopathy Screening Dashboard.
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend safe for web servers
import matplotlib.pyplot as plt

DB_PATH = Path("patients.db")


def get_connection():
    """Returns a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the patients database table and indexes."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                name TEXT NOT NULL,
                age INTEGER DEFAULT 50,
                gender TEXT DEFAULT 'Unspecified',
                contact TEXT DEFAULT '',
                eye_examined TEXT DEFAULT 'Right Eye (OD)',
                diabetic_duration TEXT DEFAULT 'Unknown',
                blood_sugar TEXT DEFAULT '',
                hypertension TEXT DEFAULT 'No',
                grade INTEGER NOT NULL,
                severity_label TEXT NOT NULL,
                urgency TEXT NOT NULL,
                confidence REAL NOT NULL,
                slip_path TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_patients_created ON patients(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_patients_grade ON patients(grade)")
        conn.commit()


# Run initialization on import
init_db()


def save_patient_record(
    patient_id: str,
    name: str,
    age: int,
    gender: str,
    contact: str,
    eye_examined: str,
    diabetic_duration: str,
    blood_sugar: str,
    hypertension: str,
    grade: int,
    severity_label: str,
    urgency: str,
    confidence: float,
    slip_path: str = "",
) -> int:
    """Inserts a new screened patient record and returns the record ID."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO patients (
                patient_id, name, age, gender, contact, eye_examined,
                diabetic_duration, blood_sugar, hypertension,
                grade, severity_label, urgency, confidence, slip_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(patient_id).strip() or "PATIENT-UNASSIGNED",
            str(name).strip() or "Unnamed Patient",
            int(age) if age else 0,
            str(gender).strip() or "Other",
            str(contact).strip(),
            str(eye_examined).strip() or "Right Eye (OD)",
            str(diabetic_duration).strip() or "Unknown",
            str(blood_sugar).strip(),
            str(hypertension).strip() or "No",
            int(grade),
            str(severity_label).strip(),
            str(urgency).strip(),
            float(confidence),
            str(slip_path).strip(),
            now_str,
        ))
        conn.commit()
        return cur.lastrowid


def get_all_patients(
    urgency_filter: str = "All",
    search_query: str = "",
) -> pd.DataFrame:
    """
    Retrieves screened patients formatted for the Gradio Dataframe.
    Supports filtering by urgency category and substring search by name or ID.
    """
    query = """
        SELECT 
            id as "Rec #",
            patient_id as "Patient ID",
            name as "Full Name",
            age || ' / ' || substr(gender, 1, 1) as "Age/Sex",
            eye_examined as "Eye",
            diabetic_duration || (CASE WHEN blood_sugar != '' THEN ' (' || blood_sugar || ')' ELSE '' END) as "Diabetic History",
            'Grade ' || grade || ': ' || severity_label as "Severity Stage",
            urgency as "Triage Urgency",
            printf('%.1f%%', confidence * 100) as "Confidence",
            created_at as "Screened At"
        FROM patients
        WHERE 1=1
    """
    params = []

    # Search filter
    if search_query and search_query.strip():
        q = f"%{search_query.strip()}%"
        query += " AND (name LIKE ? OR patient_id LIKE ?)"
        params.extend([q, q])

    # Urgency filter
    if urgency_filter == "🚨 Urgent / Immediate (Grades 3-4)":
        query += " AND grade >= 3"
    elif urgency_filter == "🟡 Follow-up / Routine (Grades 1-2)":
        query += " AND grade IN (1, 2)"
    elif urgency_filter == "🟢 Normal (Grade 0)":
        query += " AND grade = 0"

    query += " ORDER BY id DESC"

    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if df.empty:
        return pd.DataFrame(columns=[
            "Rec #", "Patient ID", "Full Name", "Age/Sex", "Eye",
            "Diabetic History", "Severity Stage", "Triage Urgency", "Confidence", "Screened At"
        ])

    return df


def get_dashboard_kpis() -> Dict[str, Any]:
    """Calculates live key performance indicators across all registered patients."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM patients")
        total = cur.fetchone()[0]

        if total == 0:
            return {
                "total": 0,
                "grade_counts": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0},
                "normal": 0,
                "mild_mod": 0,
                "urgent": 0,
                "referral_rate": 0.0,
                "urgent_rate": 0.0,
                "avg_age": 0.0,
                "avg_confidence": 0.0,
            }

        cur.execute("SELECT grade, COUNT(*) FROM patients GROUP BY grade")
        counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        for g, count in cur.fetchall():
            counts[g] = count

        normal = counts[0]
        mild_mod = counts[1] + counts[2]
        urgent = counts[3] + counts[4]
        referral_count = mild_mod + urgent

        cur.execute("SELECT AVG(age), AVG(confidence) FROM patients WHERE age > 0")
        row = cur.fetchone()
        avg_age = row[0] if row[0] is not None else 0.0
        avg_conf = row[1] if row[1] is not None else 0.0

        return {
            "total": total,
            "grade_counts": counts,
            "normal": normal,
            "mild_mod": mild_mod,
            "urgent": urgent,
            "referral_rate": (referral_count / total) * 100.0,
            "urgent_rate": (urgent / total) * 100.0,
            "avg_age": avg_age,
            "avg_confidence": avg_conf * 100.0,
        }


def render_kpi_cards_html() -> str:
    """Renders modern, visually prominent clinical metric cards in responsive HTML."""
    kpis = get_dashboard_kpis()
    tot = kpis["total"]
    norm = kpis["normal"]
    mild_mod = kpis["mild_mod"]
    urg = kpis["urgent"]
    ref_rate = kpis["referral_rate"]

    return f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px; margin: 10px 0 16px 0;">
        <!-- Card 1: Total -->
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-top: 4px solid #3b82f6; border-radius: 10px; padding: 14px 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">🩺 Total Screened</div>
            <div style="font-size: 28px; font-weight: 800; color: #0f172a; margin-top: 4px;">{tot}</div>
            <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">Registered patients</div>
        </div>
        <!-- Card 2: Normal -->
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-top: 4px solid #10b981; border-radius: 10px; padding: 14px 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; font-weight: 700; color: #059669; text-transform: uppercase; letter-spacing: 0.5px;">🟢 Normal (Grade 0)</div>
            <div style="font-size: 28px; font-weight: 800; color: #065f46; margin-top: 4px;">{norm}</div>
            <div style="font-size: 11px; color: #059669; margin-top: 2px;">Annual monitoring</div>
        </div>
        <!-- Card 3: Mild / Moderate -->
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-top: 4px solid #f59e0b; border-radius: 10px; padding: 14px 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; font-weight: 700; color: #d97706; text-transform: uppercase; letter-spacing: 0.5px;">🟡 Mild / Moderate (1-2)</div>
            <div style="font-size: 28px; font-weight: 800; color: #92400e; margin-top: 4px;">{mild_mod}</div>
            <div style="font-size: 11px; color: #b45309; margin-top: 2px;">Primary eye care review</div>
        </div>
        <!-- Card 4: Urgent Referrals -->
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-top: 4px solid #ef4444; border-radius: 10px; padding: 14px 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; font-weight: 700; color: #dc2626; text-transform: uppercase; letter-spacing: 0.5px;">🚨 Urgent Referrals (3-4)</div>
            <div style="font-size: 28px; font-weight: 800; color: #991b1b; margin-top: 4px;">{urg}</div>
            <div style="font-size: 11px; color: #dc2626; margin-top: 2px;">Vision-threatening stages</div>
        </div>
        <!-- Card 5: Referral Rate % -->
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-top: 4px solid #8b5cf6; border-radius: 10px; padding: 14px 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="font-size: 11px; font-weight: 700; color: #7c3aed; text-transform: uppercase; letter-spacing: 0.5px;">📈 Overall Referral Rate</div>
            <div style="font-size: 28px; font-weight: 800; color: #5b21b6; margin-top: 4px;">{ref_rate:.1f}%</div>
            <div style="font-size: 11px; color: #6d28d9; margin-top: 2px;">Requiring clinic triage</div>
        </div>
    </div>
    """


def generate_dashboard_charts() -> Tuple[matplotlib.figure.Figure, matplotlib.figure.Figure]:
    """
    Generates two clean, publication-quality clinical analytics figures:
      1. DR Severity Grade Distribution Donut Chart
      2. Age Cohort vs. Severity Risk Distribution Chart
    """
    kpis = get_dashboard_kpis()
    tot = kpis["total"]
    grade_counts = kpis["grade_counts"]

    # -------------------------------------------------------------
    # Figure 1: Severity Distribution Donut Chart
    # -------------------------------------------------------------
    fig_dist, ax_dist = plt.subplots(figsize=(5, 3.6), dpi=100)
    fig_dist.patch.set_facecolor("#ffffff")
    ax_dist.set_facecolor("#ffffff")

    labels = ["Grade 0: No DR", "Grade 1: Mild", "Grade 2: Moderate", "Grade 3: Severe", "Grade 4: PDR"]
    sizes = [grade_counts.get(i, 0) for i in range(5)]
    colors = ["#10b981", "#eab308", "#f97316", "#ef4444", "#991b1b"]

    if tot == 0 or sum(sizes) == 0:
        ax_dist.text(0.5, 0.5, "No patient records yet\nComplete a screening in Tab 2",
                     horizontalalignment='center', verticalalignment='center',
                     fontsize=11, color='#94a3b8', weight='semibold')
        ax_dist.axis('off')
    else:
        # Filter out 0 slices for clean legend/donut
        plot_sizes = []
        plot_labels = []
        plot_colors = []
        for s, l, c in zip(sizes, labels, colors):
            if s > 0:
                plot_sizes.append(s)
                plot_labels.append(f"{l} ({s})")
                plot_colors.append(c)

        wedges, texts, autotexts = ax_dist.pie(
            plot_sizes,
            labels=None,
            autopct='%1.0f%%',
            startangle=140,
            colors=plot_colors,
            wedgeprops=dict(width=0.42, edgecolor='#ffffff', linewidth=2),
            pctdistance=0.76,
        )
        for at in autotexts:
            at.set_color('#ffffff')
            at.set_fontsize(9)
            at.set_weight('bold')

        ax_dist.legend(wedges, plot_labels, loc="center left", bbox_to_anchor=(0.95, 0.5),
                       frameon=False, fontsize=8)
        ax_dist.set_title("DR Severity Breakdown (NPCB Triage)", fontsize=11, fontweight="bold", pad=10, color="#0f172a")

    fig_dist.tight_layout()

    # -------------------------------------------------------------
    # Figure 2: Age vs. Risk / Severity Cohort Chart
    # -------------------------------------------------------------
    fig_age, ax_age = plt.subplots(figsize=(5, 3.6), dpi=100)
    fig_age.patch.set_facecolor("#ffffff")
    ax_age.set_facecolor("#ffffff")

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT age, grade FROM patients WHERE age > 0")
        rows = cur.fetchall()

    if not rows:
        ax_age.text(0.5, 0.5, "No demographic data yet\nScreen patients with age input",
                    horizontalalignment='center', verticalalignment='center',
                    fontsize=11, color='#94a3b8', weight='semibold')
        ax_age.axis('off')
    else:
        cohorts = ["< 45 yrs", "45 - 55 yrs", "56 - 65 yrs", "> 65 yrs"]
        normal_counts = [0, 0, 0, 0]
        referral_counts = [0, 0, 0, 0]

        for age, grade in rows:
            if age < 45:
                idx = 0
            elif 45 <= age <= 55:
                idx = 1
            elif 56 <= age <= 65:
                idx = 2
            else:
                idx = 3

            if grade == 0:
                normal_counts[idx] += 1
            else:
                referral_counts[idx] += 1

        x = range(len(cohorts))
        width = 0.35

        ax_age.bar([i - width/2 for i in x], normal_counts, width, label="Normal (Gr 0)", color="#10b981")
        ax_age.bar([i + width/2 for i in x], referral_counts, width, label="Referral (Gr 1-4)", color="#ea580c")

        ax_age.set_xticks(list(x))
        ax_age.set_xticklabels(cohorts, fontsize=8)
        ax_age.set_ylabel("Patients", fontsize=9, color="#64748b")
        ax_age.set_title("Age Cohort vs. Retinopathy Status", fontsize=11, fontweight="bold", pad=10, color="#0f172a")
        ax_age.legend(frameon=False, fontsize=8)
        ax_age.spines['top'].set_visible(False)
        ax_age.spines['right'].set_visible(False)
        ax_age.spines['left'].set_color('#cbd5e1')
        ax_age.spines['bottom'].set_color('#cbd5e1')

    fig_age.tight_layout()

    return fig_dist, fig_age


def export_registry_csv(output_path: str = "clinic_patient_registry.csv") -> str:
    """Exports the full SQLite patient database to a structured CSV file."""
    df = get_all_patients(urgency_filter="All", search_query="")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return str(Path(output_path).resolve())


def seed_demo_patients() -> int:
    """
    Seeds the database with 5 genuine clinical cases across grades 0 to 4
    with realistic clinical histories and authentic fundus images.
    """
    demo_cases = [
        {
            "patient_id": "P-101-DEL",
            "name": "Sunita Sharma",
            "age": 42,
            "gender": "Female",
            "contact": "9876543210",
            "eye_examined": "Right Eye (OD)",
            "diabetic_duration": "2 - 5 years",
            "blood_sugar": "112 mg/dL",
            "hypertension": "No",
            "grade": 0,
            "severity_label": "No DR",
            "urgency": "🟢 No action needed (Annual screening)",
            "confidence": 0.990,
            "slip_path": "sample_images/clinical_grade0_no_dr.jpg",
        },
        {
            "patient_id": "P-102-PAT",
            "name": "Ramvilas Paswan",
            "age": 51,
            "gender": "Male",
            "contact": "9811223344",
            "eye_examined": "Left Eye (OS)",
            "diabetic_duration": "5 - 10 years",
            "blood_sugar": "148 mg/dL",
            "hypertension": "Yes",
            "grade": 1,
            "severity_label": "Mild NPDR",
            "urgency": "🟡 Routine checkup within 6 months",
            "confidence": 0.309,
            "slip_path": "sample_images/clinical_grade1_mild_npdr.png",
        },
        {
            "patient_id": "P-103-LKO",
            "name": "Mohd. Azharuddin",
            "age": 58,
            "gender": "Male",
            "contact": "9823456789",
            "eye_examined": "Right Eye (OD)",
            "diabetic_duration": "5 - 10 years",
            "blood_sugar": "178 mg/dL",
            "hypertension": "Yes",
            "grade": 2,
            "severity_label": "Moderate NPDR",
            "urgency": "🟠 See a doctor within 2 weeks",
            "confidence": 0.438,
            "slip_path": "sample_images/clinical_grade2_moderate_npdr.png",
        },
        {
            "patient_id": "P-104-HYD",
            "name": "Lakshmi Narayana",
            "age": 63,
            "gender": "Female",
            "contact": "9898765432",
            "eye_examined": "Right Eye (OD)",
            "diabetic_duration": "> 10 years",
            "blood_sugar": "224 mg/dL",
            "hypertension": "Yes",
            "grade": 3,
            "severity_label": "Severe NPDR",
            "urgency": "🔴 Urgent — see a doctor within 3 days",
            "confidence": 0.681,
            "slip_path": "sample_images/clinical_grade3_severe_npdr.jpg",
        },
        {
            "patient_id": "P-105-CHE",
            "name": "Muruganandham K.",
            "age": 67,
            "gender": "Male",
            "contact": "9845123654",
            "eye_examined": "Left Eye (OS)",
            "diabetic_duration": "> 10 years",
            "blood_sugar": "260 mg/dL",
            "hypertension": "Yes",
            "grade": 4,
            "severity_label": "Proliferative DR",
            "urgency": "🚨 Immediate referral required — risk of vision loss",
            "confidence": 0.894,
            "slip_path": "sample_images/clinical_grade4_proliferative_dr.jpg",
        },
    ]

    inserted = 0
    for case in demo_cases:
        save_patient_record(
            patient_id=case["patient_id"],
            name=case["name"],
            age=case["age"],
            gender=case["gender"],
            contact=case["contact"],
            eye_examined=case["eye_examined"],
            diabetic_duration=case["diabetic_duration"],
            blood_sugar=case["blood_sugar"],
            hypertension=case["hypertension"],
            grade=case["grade"],
            severity_label=case["severity_label"],
            urgency=case["urgency"],
            confidence=case["confidence"],
            slip_path=case["slip_path"],
        )
        inserted += 1

    return inserted


def clear_all_records() -> None:
    """Clears all records in the patients database."""
    with get_connection() as conn:
        conn.execute("DELETE FROM patients")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='patients'")
        conn.commit()
