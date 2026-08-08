# CloudRescue

**CloudRescue** is a self-healing service monitoring system I built to track a service's health, detect failures automatically, and alert or recover when something goes wrong.

## Why I built this

After deploying a service, how do engineers actually know something has gone wrong? How do they track a system's health once it's live, and diagnose exactly what broke? I built CloudRescue to answer these questions for myself — not just to read about SRE (Site Reliability Engineering) practices, but to actually implement detection, alerting, and recovery from scratch, and understand the reasoning behind each design decision.

## Architecture

CloudRescue consists of five components, each with a single responsibility:

- **`app.py`** — a minimal Flask service being monitored, exposing a `/health` endpoint that reports status, uptime, version, and hostname.
- **`monitor.py`** — the core watcher. Polls `/health` on a configurable interval, distinguishes between healthy, degraded ("zombie"), and fully-down states, tracks failures using both consecutive and rolling-time-window counting, triggers alerts, and attempts automatic recovery with capped, safe retry logic.
- **`config.py`** — centralizes all tunable settings (thresholds, intervals, limits) as environment variables with sensible defaults, so behavior can be adjusted without touching code.
- **`database.py`** — persists incident history and current status to SQLite, so metrics survive restarts and reflect true, long-term reliability rather than a single session.
- **`dashboard.py`** — a lightweight Flask web dashboard, auto-refreshing every 5 seconds, displaying live status, key metrics (MTTR, availability, downtime), and recent incident history.

`monitor.py` is decoupled from `app.py`'s implementation — it only depends on the HTTP health-check contract, meaning it could monitor any compatible service, not just this one.

📸 **[SCREENSHOT: architecture diagram, if you make one later — optional]**

## Features

- **Health monitoring** — polls a `/health` endpoint on a configurable interval
- **Three-state failure detection** — distinguishes healthy, "zombie" (responding but unhealthy), and fully-down states
- **Dual alerting strategies** — consecutive-failure detection *and* rolling time-window detection, catching both sustained outages and intermittent/flaky failures
- **Alert suppression** — alerts fire once per incident, not repeatedly, avoiding alert fatigue
- **Automatic recovery** — restarts a crashed service, with a capped retry limit to prevent restart storms
- **Incident tracking** — records every incident's start time and duration to a persistent database
- **Reliability metrics** — calculates real SRE metrics (MTTR, Availability %) from actual incident history, not estimates
- **Structured logging** — uses Python's standard `logging` module with proper severity levels (INFO/WARNING/ERROR/CRITICAL)
- **Configuration via environment variables** — all thresholds and intervals adjustable without code changes
- **Live dashboard** — auto-refreshing web view of current status, metrics, and recent incident history
- **Response time monitoring** — measures latency, flags degraded performance separately from outright failure

## Screenshots

📸 **[SCREENSHOT: dashboard showing healthy status + metrics]**

📸 **[SCREENSHOT: dashboard showing an active incident, if you have one]**

📸 **[SCREENSHOT: terminal log output showing DOWN → RESTART → RECOVERY sequence]**

## Installation & Usage

### Requirements
- Python 3.10+
- `pip`

### Setup

1. Clone the repository:

git clone https://github.com/OusmaneSanokho/cloudrescue.git
cd cloudrescue


2. Install dependencies:

pip install flask requests


3. Run the three components, each in its own terminal:

python app.py # the monitored service (port 5000)
python monitor.py # the watcher
python dashboard.py # the live dashboard (port 5001)


4. Open the dashboard in your browser:

http://127.0.0.1:5001


### Configuration

All thresholds are configurable via environment variables (see `config.py` for full list and defaults), for example:

$env:FAILURE_THRESHOLD=5
$env:POLL_INTERVAL_SECONDS=10
python monitor.py


## Limitations

- **Single point of failure** — if the monitor process itself crashes, nothing watches it. Solving this properly usually involves container orchestration (e.g., Kubernetes) or a process supervisor — deliberately out of scope for a single-machine project, but a natural next step (see Future Improvements).
- **No real-time human notification** — alerts are logged with `CRITICAL` severity but not sent via email/SMS/Slack. This was scoped out to focus on the detection/recovery logic first; the alerting *pipeline* is built, only the final delivery step is missing.
- **No authentication on `/health` or the dashboard** — acceptable for a local learning project, but a real deployment would need this. Deferred to keep focus on core reliability logic rather than security concerns unrelated to monitoring itself.
- **Single-instance SQLite** — appropriate for one monitor process; would need PostgreSQL if scaled to multiple monitor instances or remote access (a deliberate, documented tradeoff, not an oversight).
- **Manual version numbering** — real systems auto-generate versions from build/deployment metadata; this becomes meaningful once actual deployment exists (see AWS section, once added).
- **No automated test suite** — all testing was done through deliberate manual fault injection (documented throughout development). `pytest`-based tests are a planned improvement.

## Future Improvements

- CPU/memory usage in health endpoint (via `psutil`)
- Auto-generated version numbers (from Git tags/build metadata)
- Real-time notifications (email via AWS SES, or Slack webhook)
- Authentication on `/health` and dashboard endpoints
- Automated test suite using `pytest`
- Migration from SQLite to PostgreSQL (if multi-instance or remote access becomes necessary)
- Container-based process supervision (Docker/Kubernetes) to address the "who watches the watcher" gap
- Prometheus-compatible `/metrics` endpoint
- Dashboard rebuild in Next.js for improved visual design
- Easier local testing of restarted background processes

## Lessons Learned

Building CloudRescue taught me that alerting is far harder to get right than it first appears. A naive "alert on every failure" approach either floods the operator with noise or, in the case of consecutive-only counting, silently misses real problems — flaky services that fail often but never in a strict, unbroken sequence. Getting alerting right required careful, deliberate tuning: consecutive-failure detection, a separate rolling time-window, alert suppression to avoid duplicate noise, and retry caps to prevent the recovery system itself from making things worse.

I also learned that a monitoring system's real value isn't just *detecting* that something is wrong — it's producing a clear enough signal that a human only needs to look when something genuinely requires their attention, and act automatically when it's safe to do so. That balance, between automation and human judgment, shaped almost every design decision in this project: the watcher needed the ability to take real action (restarting a crashed service), but only within carefully bounded limits, with everything logged for accountability.

## Tech Stack

Python, Flask, SQLite, `requests`, Python `logging`

---

*Built by Ousmane Sanokho as a Cloud Engineering / DevOps portfolio project.*