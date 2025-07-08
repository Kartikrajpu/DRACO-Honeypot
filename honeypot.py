import socket
import threading
import requests
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict, deque

import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 🔧 Configure your Telegram bot token and chat ID
BOT_TOKEN = "API_TOKEN"
CHAT_ID = "ID"  # Must be an integer

# 🎯 Ports to monitor
PORTS_TO_MONITOR = [22, 80, 443]

# ⚠️ DDoS Detection Settings
REQUEST_LIMIT = 10
TIME_WINDOW = 30  # seconds
ip_activity = defaultdict(lambda: deque(maxlen=REQUEST_LIMIT))

# 🚨 Send alert to Telegram
def send_telegram_alert(ip, port, ddos=False):
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if ddos:
        message = f"🚨 DDoS Detected 🚨\nTime: {time}\nIP: {ip}\nPort: {port}\n> {REQUEST_LIMIT}+ requests in {TIME_WINDOW}s"
    else:
        message = f"🚨 Honeypot Alert 🚨\nTime: {time}\nIP: {ip}\nPort: {port}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("❌ Failed to send Telegram alert:", e)

# 📝 Log to text file
def log_to_file(ip, port):
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("honeypot_log.txt", "a") as f:
        f.write(f"{time} | IP: {ip} | Port: {port}\n")

# 🧠 Log to SQLite DB
def log_to_db(ip, port):
    conn = sqlite3.connect("honeypot_logs.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            port INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    c.execute("INSERT INTO logs (ip, port, timestamp) VALUES (?, ?, ?)",
              (ip, port, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# 🛡 Honeypot listener
def start_honeypot(port):
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(('0.0.0.0', port))
        sock.listen(5)
        print(f"🛡 Listening on port {port}")
        while True:
            conn, addr = sock.accept()
            ip = addr[0]
            now = datetime.now()

            # DDoS Detection
            ip_activity[ip].append(now)
            recent_requests = [t for t in ip_activity[ip] if now - t <= timedelta(seconds=TIME_WINDOW)]

            if len(recent_requests) >= REQUEST_LIMIT:
                send_telegram_alert(ip, port, ddos=True)
            else:
                send_telegram_alert(ip, port)

            print(f"⚠ Connection from {ip} on port {port}")
            log_to_file(ip, port)
            log_to_db(ip, port)
            conn.close()
    except Exception as e:
        print(f"[ERROR] Port {port}: {e}")

# 🤖 Telegram command handlers (v20 style)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Honeypot Bot Active.\nUse /status, /stats, /recent.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ports = ', '.join(map(str, PORTS_TO_MONITOR))
    await update.message.reply_text(f"🛡 Honeypot is monitoring ports: {ports}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = sqlite3.connect("honeypot_logs.db")
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM logs")
        total = c.fetchone()[0]
        conn.close()
        await update.message.reply_text(f"📊 Total intrusion attempts: {total}")
    except:
        await update.message.reply_text("No data available.")

async def recent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = sqlite3.connect("honeypot_logs.db")
        c = conn.cursor()
        c.execute("SELECT ip, port, timestamp FROM logs ORDER BY id DESC LIMIT 5")
        rows = c.fetchall()
        conn.close()
        if not rows:
            await update.message.reply_text("No recent logs.")
            return
        message = "📄 Last 5 attempts:\n" + "\n".join(
            [f"{r[2]} | {r[0]}:{r[1]}" for r in rows]
        )
        await update.message.reply_text(message)
    except:
        await update.message.reply_text("Error reading database.")

# ▶ Start Telegram bot in a thread (for sync compatibility)
def run_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("recent", recent))
    print("📡 Telegram bot listening...")
    app.run_polling()


    threading.Thread(target=lambda: asyncio.run(main()), daemon=True).start()

# 🚀 Main
if __name__ == "__main__":
    # Start honeypot listeners in threads
    for port in PORTS_TO_MONITOR:
        threading.Thread(target=start_honeypot, args=(port,), daemon=True).start()

    # Start the bot in main thread
    run_bot()

