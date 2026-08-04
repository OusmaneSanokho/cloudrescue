import requests
import time
from datetime import datetime
import subprocess

FAILURE_THRESHOLD = 3
failure_count = 0
alert_sent = False
incident_start_time = None
MAX_RESTART_ATTEMPTS = 3
restart_attempts = 0

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} - {message}"
    print(line)
    with open("cloudrescue.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")

while True:
    try:
        response = requests.get("http://127.0.0.1:5000/health")
        data = response.json()

        if response.status_code == 200 and data.get("status") == "ok":
            if incident_start_time is not None:
                duration = (datetime.now() - incident_start_time).total_seconds()
                log_message(f"✅ RECOVERY: Service is back online. Incident lasted {duration:.0f} seconds.")
                incident_start_time = None

            log_message(f"Service is healthy: {data}")
            failure_count = 0
            alert_sent = False
            restart_attempts = 0
        else:
            failure_count += 1
            if incident_start_time is None:
                incident_start_time = datetime.now()

            log_message(f"Service responded but is UNHEALTHY: {response.status_code} {data} (failure #{failure_count})")
            if failure_count >= FAILURE_THRESHOLD and not alert_sent:
                log_message(f"🚨 ALERT: Service has failed {failure_count} times in a row!")
                alert_sent = True

    except requests.exceptions.ConnectionError:
        failure_count += 1
        if incident_start_time is None:
            incident_start_time = datetime.now()

        log_message(f"Service is DOWN - no response (failure #{failure_count})")

        if failure_count == FAILURE_THRESHOLD:
            if restart_attempts < MAX_RESTART_ATTEMPTS:
                restart_attempts += 1
                log_message(f"🔧 Attempting automatic recovery (attempt {restart_attempts}/{MAX_RESTART_ATTEMPTS}): restarting app.py")
                subprocess.Popen(["python", "app.py"])
            else:
                log_message("⛔ Max restart attempts reached. Manual intervention required.")

        if failure_count >= FAILURE_THRESHOLD and not alert_sent:
            log_message(f"🚨 ALERT: Service has failed {failure_count} times in a row!")
            alert_sent = True

    time.sleep(5)