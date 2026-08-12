from flask import Flask
from database import get_current_status, calculate_metrics, get_monitoring_start_time, get_recent_incidents
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def dashboard():
    status = get_current_status()
    total_incidents, total_downtime_seconds, longest_incident_seconds = calculate_metrics()
    monitoring_start_time = get_monitoring_start_time()

    total_monitoring_time = (datetime.now() - monitoring_start_time).total_seconds()
    uptime_seconds = total_monitoring_time - total_downtime_seconds
    availability = (uptime_seconds / total_monitoring_time) * 100 if total_monitoring_time > 0 else 100
    mttr = (total_downtime_seconds / total_incidents) if total_incidents > 0 else 0

    status_color = {"healthy": "green", "unhealthy": "orange", "down": "red"}.get(status, "gray")

    recent_incidents = get_recent_incidents()
    incidents_rows = "".join(
        f"<tr><td>{start}</td><td>{duration:.0f}s</td></tr>"
        for start, duration in recent_incidents
    )

    html = f"""
    <html>
    <head>
        <title>CloudRescue Dashboard</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: white; padding: 40px; }}
            .status {{ font-size: 32px; font-weight: bold; color: {status_color}; }}
            .metric {{ font-size: 18px; margin: 10px 0; }}
            .card {{ background: #2a2a2a; padding: 20px; border-radius: 10px; max-width: 500px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ padding: 8px; border-bottom: 1px solid #444; }}
        </style>
    </head>
    <body>
        <h1>CloudRescue Dashboard</h1>
        <div class="card">
            <div class="status">Status: {status.upper()}</div>
            <div class="metric">Total Incidents: {total_incidents}</div>
            <div class="metric">Total Downtime: {total_downtime_seconds:.0f}s</div>
            <div class="metric">Longest Incident: {longest_incident_seconds:.0f}s</div>
            <div class="metric">MTTR: {mttr:.0f}s</div>
            <div class="metric">Availability: {availability:.2f}%</div>
        </div>
        <div class="card" style="margin-top: 20px;">
            <h2>Recent Incidents</h2>
            <table>
                <tr><th>Start Time</th><th>Duration</th></tr>
                {incidents_rows}
            </table>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)