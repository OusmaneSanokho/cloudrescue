import requests
import time
import logging
import subprocess
from datetime import datetime

from config import (
    FAILURE_THRESHOLD,
    MAX_RESTART_ATTEMPTS,
    RESPONSE_TIME_WARNING_MS,
    RESPONSE_TIME_CRITICAL_MS,
    POLL_INTERVAL_SECONDS,
    ALERT_WINDOW_SECONDS,
)
from database import init_database, get_monitoring_start_time, save_incident, calculate_metrics

failure_count = 0
alert_sent = False
incident_start_time = None
restart_attempts = 0
failure_timestamps = []

logging.basicConfig(
    filename="cloudrescue.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

console = logging.StreamHandler()
console.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logging.getLogger().addHandler(console)


def print_metrics():
    total_incidents, total_downtime_seconds, longest_incident_seconds = calculate_metrics()
    total_monitoring_time = (datetime.now() - monitoring_start_time).total_seconds()
    uptime_seconds = total_monitoring_time - total_downtime_seconds
    availability = (uptime_seconds / total_monitoring_time) * 100 if total_monitoring_time > 0 else 100
    mttr = (total_downtime_seconds / total_incidents) if total_incidents > 0 else 0

    logging.info(
        f"📊 METRICS — Incidents: {total_incidents}, "
        f"Total downtime: {total_downtime_seconds:.0f}s, "
        f"Longest incident: {longest_incident_seconds:.0f}s, "
        f"MTTR: {mttr:.0f}s, "
        f"Availability: {availability:.2f}%"
    )


init_database()
monitoring_start_time = get_monitoring_start_time()

while True:
    try:
        start_time = datetime.now()
        response = requests.get("http://127.0.0.1:5000/health")
        end_time = datetime.now()
        response_time_ms = (end_time - start_time).total_seconds() * 1000

        data = response.json()

        if response.status_code == 200 and data.get("status") == "ok":
            if incident_start_time is not None:
                duration = (datetime.now() - incident_start_time).total_seconds()
                logging.info(f"✅ RECOVERY: Service is back online. Incident lasted {duration:.0f} seconds.")

                save_incident(incident_start_time, duration)
                print_metrics()
                incident_start_time = None

            if response_time_ms >= RESPONSE_TIME_CRITICAL_MS:
                logging.error(f"🔴 Service is healthy but CRITICALLY SLOW: {response_time_ms:.0f}ms")
            elif response_time_ms >= RESPONSE_TIME_WARNING_MS:
                logging.warning(f"🟡 Service is healthy but slow: {response_time_ms:.0f}ms")
            else:
                logging.info(f"Service is healthy: {data} ({response_time_ms:.0f}ms)")

            failure_count = 0
            alert_sent = False
            restart_attempts = 0
        else:
            failure_count += 1
            if incident_start_time is None:
                incident_start_time = datetime.now()

            logging.warning(f"Service responded but is UNHEALTHY: {response.status_code} {data} (failure #{failure_count})")

            failure_timestamps.append(datetime.now())
            failure_timestamps[:] = [t for t in failure_timestamps if (datetime.now() - t).total_seconds() <= ALERT_WINDOW_SECONDS]

            if len(failure_timestamps) >= FAILURE_THRESHOLD and not alert_sent:
                logging.critical(f"🚨 ALERT: {len(failure_timestamps)} failures within the last {ALERT_WINDOW_SECONDS} seconds!")
                alert_sent = True

    except requests.exceptions.ConnectionError:
        failure_count += 1
        if incident_start_time is None:
            incident_start_time = datetime.now()

        logging.error(f"Service is DOWN - no response (failure #{failure_count})")

        if failure_count % FAILURE_THRESHOLD == 0:
            if restart_attempts < MAX_RESTART_ATTEMPTS:
                restart_attempts += 1
                logging.info(f"🔧 Attempting automatic recovery (attempt {restart_attempts}/{MAX_RESTART_ATTEMPTS}): restarting app.py")
                subprocess.Popen(["python", "app.py"])
            else:
                logging.error("⛔ Max restart attempts reached. Manual intervention required.")

        if failure_count >= FAILURE_THRESHOLD and not alert_sent:
            logging.critical(f"🚨 ALERT: Service has failed {failure_count} times in a row!")
            alert_sent = True

    time.sleep(POLL_INTERVAL_SECONDS)