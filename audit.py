"""
audit.py — Compliance Audit Trail & SQLite Audit Logger.
L&T TECHNUM Feature 6: Immutable record of AI classifications, quality gate overrides,
and authoritative doctor actions.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import privacy

DB_PATH = Path("patients.db")


def init_audit_table():
    """Initializes the additive audit_log table without modifying existing tables."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                scan_id TEXT NOT NULL,
                patient_hash TEXT NOT NULL,
                model_version TEXT NOT NULL,
                ai_grade INTEGER NOT NULL,
                confidence_status TEXT NOT NULL,
                top1_prob REAL NOT NULL,
                quality_pass INTEGER NOT NULL,
                support_mode TEXT NOT NULL,
                language TEXT NOT NULL,
                doctor_action TEXT NOT NULL,
                final_grade INTEGER NOT NULL,
                reason TEXT NOT NULL,
                proceeded_despite_quality INTEGER NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(timestamp)")
        conn.commit()


# Run initialization on import
init_audit_table()


def log_audit_event(
    scan_id: str,
    patient_id: str,
    model_version: str,
    ai_grade: int,
    confidence_status: str,
    top1_prob: float,
    quality_pass: bool,
    support_mode: str,
    language: str,
    doctor_action: str,
    final_grade: int,
    reason: str,
    proceeded_despite_quality: bool,
) -> int:
    """Inserts a new immutable audit row with salted patient hashing."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    p_hash = privacy.hash_patient_id(patient_id)

    with sqlite3.connect(str(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO audit_log (
                timestamp, scan_id, patient_hash, model_version, ai_grade,
                confidence_status, top1_prob, quality_pass, support_mode,
                language, doctor_action, final_grade, reason, proceeded_despite_quality
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now_str, str(scan_id), p_hash, str(model_version), int(ai_grade),
            str(confidence_status), float(top1_prob), 1 if quality_pass else 0,
            str(support_mode), str(language), str(doctor_action), int(final_grade),
            str(reason), 1 if proceeded_despite_quality else 0
        ))
        conn.commit()
        return cur.lastrowid


def get_audit_records(action_filter: str = "All") -> pd.DataFrame:
    """Fetches audit records formatted for UI inspection and CSV export."""
    query = """
        SELECT 
            id as "Log ID",
            timestamp as "Timestamp",
            scan_id as "Scan ID",
            patient_hash as "Salted Patient Hash",
            'Grade ' || ai_grade as "AI Grade",
            printf('%.1f%%', top1_prob * 100) as "Top-1 Prob",
            confidence_status as "Confidence",
            CASE WHEN quality_pass = 1 THEN 'PASSED' ELSE 'FLAGGED' END as "Quality Gate",
            doctor_action as "Doctor Action",
            CASE WHEN final_grade >= 0 THEN 'Grade ' || final_grade ELSE 'REJECTED' END as "Final Grade",
            CASE WHEN proceeded_despite_quality = 1 THEN 'YES (Override)' ELSE 'NO' END as "Quality Override",
            reason as "Clinical Rationale"
        FROM audit_log
        WHERE 1=1
    """
    params = []
    if action_filter != "All":
        query += " AND doctor_action = ?"
        params.append(action_filter)
    query += " ORDER BY id DESC"

    with sqlite3.connect(str(DB_PATH)) as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if df.empty:
        return pd.DataFrame(columns=[
            "Log ID", "Timestamp", "Scan ID", "Salted Patient Hash", "AI Grade",
            "Top-1 Prob", "Confidence", "Quality Gate", "Doctor Action", "Final Grade",
            "Quality Override", "Clinical Rationale"
        ])
    return df


def get_audit_summary() -> Dict[str, int]:
    """Calculates summary KPIs across doctor actions."""
    with sqlite3.connect(str(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM audit_log")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM audit_log WHERE doctor_action = 'ACCEPT'")
        accepted = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM audit_log WHERE doctor_action = 'CORRECT'")
        corrected = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM audit_log WHERE doctor_action = 'REJECT'")
        rejected = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM audit_log WHERE quality_pass = 0 OR proceeded_despite_quality = 1")
        low_quality = cur.fetchone()[0]
    return {
        "total": total,
        "accepted": accepted,
        "corrected": corrected,
        "rejected": rejected,
        "low_quality": low_quality,
    }
