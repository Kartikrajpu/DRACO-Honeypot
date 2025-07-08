# DRACO-Honeypot
# 🛡️ DRACO-Honeypot – Telegram Alerting System

A lightweight, cross-platform honeypot system built with Python 3.11 that listens on critical ports (22, 80, 443) and instantly alerts via Telegram when suspicious connections occur.

🧠 Built and tested as part of my cybersecurity internship.

## 🚀 Features

- Monitors ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)
- Sends real-time Telegram alerts with timestamp and IP
- Logs intrusions into:
  - 📄 honeypot_log.txt
  - 🗃️ SQLite database (honeypot_logs.db)
- Includes a built-in Telegram Bot with command support
- Compatible with Windows & Kali Linux
- Designed to run via virtual environment (Python 3.11+)

## 💬 Telegram Bot Commands

| Command   | Description                         |
|-----------|-------------------------------------|
| /start    | Check bot is active                 |
| /status   | Shows monitored ports               |
| /stats    | Total intrusion attempts            |
| /recent   | Last 5 logged IPs                   |

## 🖥️ How to Run (Windows/Linux)

```bash
# 1. Create virtual environment
python3.11 -m venv honeypot-venv

# 2. Activate venv
source honeypot-venv/bin/activate     # On Kali
.\honeypot-venv\Scripts\activate      # On Windows

# 3. Install requirements
pip install -r requirements.txt

# 4. Run the honeypot
python honeypot.py
