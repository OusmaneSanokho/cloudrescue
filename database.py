import sqlite3
from datetime import datetime

def init_database():
    conn = sqlite3.connect("cloudrescue.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT,
            duration_seconds REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitor_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cursor.execute("SELECT value FROM monitor_metadata WHERE key = 'monitoring_start_time'")
    row = cursor.fetchone()
    if row is None:
        cursor.execute(
            "INSERT INTO monitor_metadata (key, value) VALUES (?, ?)",
            ("monitoring_start_time", datetime.now().isoformat())
        )
    conn.commit()
    conn.close()

def get_monitoring_start_time():
    conn = sqlite3.connect("cloudrescue.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM monitor_metadata WHERE key = 'monitoring_start_time'")
    row = cursor.fetchone()
    conn.close()
    return datetime.fromisoformat(row[0])

def save_incident(start_time, duration_seconds):
    conn = sqlite3.connect("cloudrescue.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO incidents (start_time, duration_seconds) VALUES (?, ?)",
        (start_time.isoformat(), duration_seconds)
    )
    conn.commit()
    conn.close()

def calculate_metrics():
    conn = sqlite3.connect("cloudrescue.db")
    cursor = conn.cursor()
    cursor.execute("SELECT duration_seconds FROM incidents")
    rows = cursor.fetchall()
    conn.close()

    total_incidents = len(rows)
    total_downtime_seconds = sum(row[0] for row in rows)
    longest_incident_seconds = max((row[0] for row in rows), default=0)

    return total_incidents, total_downtime_seconds, longest_incident_seconds