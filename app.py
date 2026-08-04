from flask import Flask
from datetime import datetime
import socket

app = Flask(__name__)

APP_VERSION = "1.0.0"
start_time = datetime.now()

@app.route("/")
def home():
    return "CloudRescue service is alive!"

@app.route("/health")
def health():
    uptime_seconds = (datetime.now() - start_time).total_seconds()
    return {
        "status": "ok",
        "uptime_seconds": round(uptime_seconds, 1),
        "timestamp": datetime.now().isoformat(),
        "version": APP_VERSION,
        "hostname": socket.gethostname()
    }, 200

if __name__ == "__main__":
    app.run(port=5000)
