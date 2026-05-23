#!/usr/bin/env python3
"""
STAB SYSTEM v2 -- Telegram Logger -> Local CSV Tracker

Monitors a Telegram chat/channel and logs message counts to a local CSV file.
Works WITHOUT Google credentials -- uses a simple CSV file that you can later
import into Google Sheets.

Usage:
  1. Set environment variables (see below)
  2. pip install telethon
  3. python telegram_logger.py

Environment variables:
  TG_API_ID       -- your Telegram API ID (from my.telegram.org)
  TG_API_HASH     -- your Telegram API hash
  TG_TARGET_CHAT  -- numeric chat ID to monitor (e.g. -1001234567890)
                     Leave empty to log ALL incoming messages.

The script writes to STAB_TRACKING.csv in the same directory.
"""

import os
import sys
import csv
import asyncio
import logging
from datetime import datetime, date
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("stab_logger")

# ---------- paths ----------
SCRIPT_DIR = Path(__file__).parent
CSV_PATH = SCRIPT_DIR / "STAB_TRACKING.csv"

# ---------- daily counters (in-memory, flushed to CSV) ----------
counters = {
    "date": str(date.today()),
    "messages": 0,
    "replies": 0,
    "clients": 0,
    "revenue": 0.0,
}


def ensure_csv():
    """Create the CSV with headers if it doesn't exist yet."""
    if not CSV_PATH.exists():
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["DATE", "MESSAGES", "REPLIES", "CLIENTS", "REVENUE"])
        log.info("Created tracking CSV at %s", CSV_PATH)


def flush_to_neon():
    """Upsert current daily stats into Neon PostgreSQL leads table."""
    env_path = SCRIPT_DIR / ".env"
    db_url = None
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    if key.strip() == "DATABASE_URL":
                        db_url = val.strip()
                        break
    if not db_url:
        db_url = os.getenv("DATABASE_URL")
        
    if not db_url:
        return
        
    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Check if row with today's date exists
        cur.execute("SELECT id FROM leads WHERE date = %s", (counters["date"],))
        row = cur.fetchone()
        
        if row:
            # Update
            cur.execute("""
                UPDATE leads 
                SET messages_sent = %s, replies_received = %s, clients_converted = %s, revenue = %s
                WHERE date = %s
            """, (counters["messages"], counters["replies"], counters["clients"], counters["revenue"], counters["date"]))
        else:
            # Insert
            cur.execute("""
                INSERT INTO leads (date, messages_sent, replies_received, clients_converted, revenue)
                VALUES (%s, %s, %s, %s, %s)
            """, (counters["date"], counters["messages"], counters["replies"], counters["clients"], counters["revenue"]))
            
        conn.commit()
        cur.close()
        conn.close()
        log.info("Successfully synced today's counters to Neon Cloud database!")
    except Exception as e:
        log.warning("Failed to sync counters to Neon: %s", e)


def flush_counters():
    """Append the current counters as a new row in the CSV and sync to Neon."""
    ensure_csv()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            counters["date"],
            counters["messages"],
            counters["replies"],
            counters["clients"],
            counters["revenue"],
        ])
    log.info(
        "Flushed: date=%s msgs=%d replies=%d clients=%d revenue=%.0f",
        counters["date"],
        counters["messages"],
        counters["replies"],
        counters["clients"],
        counters["revenue"],
    )
    flush_to_neon()


def reset_if_new_day():
    """Check if the date has changed; if so, flush and reset."""
    today = str(date.today())
    if counters["date"] != today:
        flush_counters()
        counters["date"] = today
        counters["messages"] = 0
        counters["replies"] = 0
        counters["clients"] = 0
        counters["revenue"] = 0.0


async def run_telegram_monitor():
    """Connect to Telegram and start counting events."""
    try:
        from telethon import TelegramClient, events
    except ImportError:
        log.error("telethon not installed. Run: pip install telethon")
        sys.exit(1)

    api_id = os.getenv("TG_API_ID")
    api_hash = os.getenv("TG_API_HASH")
    target_chat_str = os.getenv("TG_TARGET_CHAT", "")

    if not api_id or not api_hash:
        log.error("Set TG_API_ID and TG_API_HASH environment variables.")
        sys.exit(1)

    session_path = str(SCRIPT_DIR / "stab_logger_session")
    client = TelegramClient(session_path, int(api_id), api_hash)
    await client.start()
    log.info("Telegram client started. Session: %s", session_path)

    target_chat = int(target_chat_str) if target_chat_str else None

    @client.on(events.NewMessage(chats=target_chat))
    async def on_new_message(event):
        reset_if_new_day()
        counters["messages"] += 1
        if event.message.reply_to_msg_id:
            counters["replies"] += 1
        log.info(
            "[%s] msg +1 (total %d) | reply %s",
            counters["date"],
            counters["messages"],
            "+1" if event.message.reply_to_msg_id else "-",
        )

    # Periodic flush every 5 minutes so data isn't lost on crash
    async def periodic_flush():
        while True:
            await asyncio.sleep(300)
            reset_if_new_day()
            flush_counters()

    asyncio.get_event_loop().create_task(periodic_flush())

    log.info(
        "Monitoring %s. Ctrl+C to stop.",
        f"chat {target_chat}" if target_chat else "ALL chats",
    )
    try:
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        pass
    finally:
        flush_counters()
        log.info("Final flush done. Goodbye.")


if __name__ == "__main__":
    ensure_csv()
    asyncio.run(run_telegram_monitor())
