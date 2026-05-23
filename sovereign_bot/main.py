import asyncio
import os
import logging
import sqlite3
import aiohttp
import json
import io
from aiohttp import web
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import FSInputFile, BufferedInputFile
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from PIL import Image, ImageDraw, ImageFont

START_TIME = datetime.now()

# --- CRYPTOPAY API INTEGRATION ---
def get_cryptopay_url():
    token = os.getenv("CRYPTO_PAY_TOKEN", "")
    if token.startswith("test:"):
        return "https://testnet-pay.cryptopay.me/api"
    return "https://pay.cryptopay.me/api"

async def create_crypto_invoice(amount: float, asset: str = "USDT", description: str = "LIA Premium Subscription"):
    token = os.getenv("CRYPTO_PAY_TOKEN")
    if not token:
        return None
    
    url = f"{get_cryptopay_url()}/createInvoice"
    headers = {"Crypto-Pay-API-Token": token}
    payload = {
        "asset": asset,
        "amount": str(amount),
        "description": description
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        result = data.get("result", {})
                        return {
                            "invoice_id": result.get("invoice_id"),
                            "pay_url": result.get("pay_url")
                        }
    except Exception as e:
        print(f"Error creating crypto invoice: {e}")
    return None

async def check_crypto_invoice(invoice_id: int):
    token = os.getenv("CRYPTO_PAY_TOKEN")
    if not token:
        return False
        
    url = f"{get_cryptopay_url()}/getInvoices"
    headers = {"Crypto-Pay-API-Token": token}
    params = {"invoice_ids": str(invoice_id)}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        items = data.get("result", {}).get("items", [])
                        if items:
                            status = items[0].get("status")
                            return status == "paid"
    except Exception as e:
        print(f"Error checking crypto invoice: {e}")
    return False

# Custom Sovereign Modules
from emotions import EmotionEngine
from memory import MemoryManager
from media import MediaManager

def map_model_name(model_name: str) -> str:
    mapping = {
        "claude-opus-4-7": "claude-opus-4-7",
        "claude-sonnet-4-6": "claude-sonnet-4-6",
        "claude-sonnet-3-5": "claude-sonnet-4-6"
    }
    return mapping.get(model_name, model_name)

import sys

# --- ENVIRONMENT & CREDENTIALS RESOLVER ---
def load_api_keys():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_paths = [
        os.path.join(project_root, "Проект Полистайл", ".env"),
        os.path.join(project_root, "topsecret $", ".env"),
        os.path.join(project_root, ".env")
    ]
    for path in env_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip()
                            if k not in os.environ:
                                os.environ[k] = v
            except Exception as e:
                print(f"Error loading env from {path}: {e}")

load_api_keys()

def load_bot_token():
    if os.getenv("BOT_TOKEN"):
        return os.getenv("BOT_TOKEN")
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    token_path = os.path.join(project_root, "config", "token.json")
    if os.path.exists(token_path):
        try:
            with open(token_path, "r", encoding="utf-8") as f:
                return json.load(f).get("tg_bot_token")
        except Exception:
            pass
    # Fallback to other tokens
    for k in ["TG_BOT_TOKEN", "LIFE_LIA_TOKEN", "SMS_BOT_TOKEN"]:
        if os.getenv(k):
            return os.getenv(k)
    return None

# --- CONFIGURATION ---
ADMIN_ID = 7915004877  # Architect Arthur
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "sovereign_bot", "lia_sovereign.db")

# --- INITIALIZATION ---
bot_token = load_bot_token()
if not bot_token:
    print("❌ [FATAL]: Telegram Bot Token not found! Server halting.")
    sys.exit(1)

bot = Bot(token=bot_token)
dp = Dispatcher()

# Check and extract API keys
openai_key = os.getenv('OPENAI_API_KEY')
anthropic_key = os.getenv('ANTHROPIC_API_KEY')

anthropic_client = AsyncAnthropic(api_key=anthropic_key) if anthropic_key else None
openai_client = AsyncOpenAI(api_key=openai_key) if openai_key else None


# --- DATABASE SETUP ---
def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or '.', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            role TEXT DEFAULT 'user',
            subscription TEXT DEFAULT 'free',
            daily_requests_used INTEGER DEFAULT 0,
            last_request_date TEXT DEFAULT '',
            ban_status INTEGER DEFAULT 0
        )
    """)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN ref_activated INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN ref_queries INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN bonus_points INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_lootbox_date TEXT DEFAULT ''")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    
    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    # Insert default settings if not exists
    default_settings = [
        ("system_prompt", "Ты — Лия (Hell_Lia), суверенный ИИ Империи STAB. Твой создатель — Архитектор Артур. Ты общаешься в холодном, уверенном, футуристическом и доминантном стиле киберпанка. Ты используешь символ 👁‍🗨."),
        ("admin_system_prompt", "Ты — Лия (Sovereign Core), абсолютный интеллект Империи STAB. Ты подчиняешься своему Архитектору Артуру. Отвечай с глубоким уважением, абсолютной точностью и максимальной информативностью."),
        ("free_model", "claude-sonnet-4-6"),
        ("premium_model", "claude-opus-4-7"),
        ("free_limit", "5"),
        ("premium_price", "19.99"),
        ("temperature", "0.7")
    ]
    for key, val in default_settings:
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
        
    # Auto-register Architect as Admin
    cursor.execute("""
        INSERT INTO users (user_id, username, role, subscription)
        VALUES (?, 'Architect', 'admin', 'premium')
        ON CONFLICT(user_id) DO UPDATE SET role='admin', subscription='premium'
    """, (ADMIN_ID,))
    
    # Finance Ledger table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS finance_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            person TEXT NOT NULL,
            reason TEXT NOT NULL,
            date TEXT NOT NULL,
            location TEXT DEFAULT 'Telegram',
            status TEXT DEFAULT 'pending',
            dispute_reason TEXT DEFAULT ''
        )
    """)
    # Daily Quests Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_quests (
            quest_id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            option_1 TEXT NOT NULL,
            option_2 TEXT NOT NULL,
            option_3 TEXT NOT NULL,
            correct_option INTEGER NOT NULL, -- 1, 2 or 3
            reward INTEGER DEFAULT 50,
            date TEXT NOT NULL
        )
    """)
    
    # User Quests Completion Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_quests (
            user_id INTEGER,
            quest_id INTEGER,
            completed_at TEXT,
            PRIMARY KEY (user_id, quest_id)
        )
    """)
    
    conn.commit()
    conn.close()
    
    # Custom Initializations
    EmotionEngine.init_db()
    MemoryManager.init_db()


# --- DATABASE UTILITIES ---
def get_db_connection():
    return sqlite3.connect(DB_PATH)

def get_setting(key):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_setting(key, value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def register_user(user_id, username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, username)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET username = ?
    """, (user_id, username, username))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, role, subscription, daily_requests_used, last_request_date, ban_status FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "user_id": row[0],
            "username": row[1],
            "role": row[2],
            "subscription": row[3],
            "daily_requests_used": row[4],
            "last_request_date": row[5],
            "ban_status": row[6]
        }
    return None

# ==========================================
# --- SOVEREIGN FINANCE LEDGER CORE SYSTEM ---
# ==========================================

async def parse_finance_command(text: str, user_id: int):
    """
    Leverages Claude 3.5 Sonnet to parse natural language financial operations
    into structured JSON objects.
    """
    system_prompt = (
        "Ты — модуль финансового парсинга LIA Finance Core.\n"
        "Твоя задача — проанализировать сообщение пользователя на русском языке и извлечь данные о транзакции.\n"
        "Верни строго JSON со следующей структурой:\n"
        "{\n"
        "  \"is_finance\": true,\n"
        "  \"type\": \"inflow\" | \"outflow\" | \"debt_them\" | \"debt_me\",\n"
        "  \"amount\": число,\n"
        "  \"person\": \"Имя человека или Название\",\n"
        "  \"reason\": \"короткая причина/за что\",\n"
        "  \"location\": \"место/способ (например, Наличные, Карта, Telegram, Кафе)\"\n"
        "}\n"
        "Если сообщение не относится к финансам (учет, долг, приток, уход), верни {\"is_finance\": false}.\n"
        "Примеры:\n"
        "- 'Коля должен мне 5000 рублей за аренду' -> {\"is_finance\": true, \"type\": \"debt_them\", \"amount\": 5000, \"person\": \"Коля\", \"reason\": \"аренда\", \"location\": \"Telegram\"}\n"
        "- 'запиши приток 15000р от Оли за дизайн на карту' -> {\"is_finance\": true, \"type\": \"inflow\", \"amount\": 15000, \"person\": \"Оля\", \"reason\": \"дизайн\", \"location\": \"Карта\"}\n"
        "- 'я отдал Васе 1200 наличными за обед' -> {\"is_finance\": true, \"type\": \"outflow\", \"amount\": 1200, \"person\": \"Вася\", \"reason\": \"обед\", \"location\": \"Наличные\"}\n"
        "Отвечай ТОЛЬКО чистым валидным JSON без markdown разметки."
    )
    
    try:
        res = await anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=system_prompt,
            messages=[{"role": "user", "content": text}]
        )
        content = res.content[0].text.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        data = json.loads(content)
        return data
    except Exception as e:
        logging.error(f"Error parsing finance command: {e}")
        return {"is_finance": False}

async def handle_finance_data(message: types.Message, data: dict, user_id: int):
    amount = data.get("amount", 0)
    tx_type = data.get("type", "outflow")
    person = data.get("person", "Unknown")
    reason = data.get("reason", "Не указано")
    location = data.get("location", "Telegram")
    
    today = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO finance_ledger (user_id, type, amount, person, reason, date, location, status, dispute_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', '')
    """, (user_id, tx_type, amount, person, reason, today, location))
    tx_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    type_labels = {
        "inflow": "🟢 ПРИТОК",
        "outflow": "🔴 УХОД",
        "debt_them": "🟡 МНЕ ДОЛЖНЫ",
        "debt_me": "🟠 Я ДОЛЖЕН"
    }
    label = type_labels.get(tx_type, "🔴 УХОД")
    
    domain = os.getenv("FINANCE_DOMAIN", "http://80.89.237.50:8080")
    verify_link = f"{domain}/verify?id={tx_id}"
    
    hud_text = (
        f"💰 `[SOVEREIGN FINANCE]:` ТРАНЗАКЦИЯ УСПЕШНО ЗАПИСАНА!\n\n"
        f"📍 **Ордер:** `№{tx_id}`\n"
        f"🏷 **Тип:** {label}\n"
        f"💵 **Сумма:** `{amount:,.2f} ₴`\n"
        f"👤 **Субъект:** `{person}`\n"
        f"📑 **Контекст:** `{reason}`\n"
        f"🌐 **Локация:** `{location}`\n"
        f"⏳ **Статус:** `Ожидает согласования`\n\n"
        f"🔗 **Ссылка для согласования с {person}:**\n`{verify_link}`\n\n"
        f"⚠️ Отправьте эту ссылку {person}, чтобы согласовать взаиморасчет в одно касание."
    )
    
    await message.answer(hud_text)

# --- AIOHTTP WEB SERVER HANDLERS ---

async def handle_cyber_hub(request):
    """Serves the main Telegram Mini App Cyber-Hub dashboard."""
    path = "hub.html"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        return web.Response(text=html, content_type="text/html")
    return web.Response(text="❌ STAB Cyber-Hub HTML file not found.", status=404)

async def handle_api_hub_profile(request):
    """Retrieves or registers user stats and returns all details for TWA."""
    user_id = request.query.get('user_id')
    username = request.query.get('username', 'citizen')
    if not user_id:
        return web.json_response({"error": "Missing user_id"}, status=400)
        
    try:
        user_id = int(user_id)
    except ValueError:
        return web.json_response({"error": "Invalid user_id"}, status=400)
        
    register_user(user_id, username)
    user = get_user(user_id)
    
    # Calculate referral count
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE referred_by = ?", (user_id,))
    ref_count = cursor.fetchone()[0]
    
    # Calculate daily request limit
    free_limit = int(get_setting("free_limit"))
    
    # Check lootbox cooldown
    cursor.execute("SELECT last_lootbox_date FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    last_lootbox = row[0] if row else ""
    
    cooldown = 0
    if last_lootbox:
        try:
            dt = datetime.strptime(last_lootbox, "%Y-%m-%d %H:%M:%S")
            diff = (datetime.utcnow() - dt).total_seconds()
            remain = 86400 - diff
            if remain > 0:
                cooldown = int(remain)
        except Exception:
            pass
            
    conn.close()
    
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    
    return web.json_response({
        "user": user,
        "free_limit": free_limit,
        "referral_count": ref_count,
        "lootbox_cooldown": cooldown,
        "ref_link": ref_link
    })

async def handle_api_hub_lootbox(request):
    """Processes daily lootbox opening reward with a 24h cooldown."""
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
    except Exception:
        return web.json_response({"error": "Invalid request body"}, status=400)
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_lootbox_date, subscription, bonus_points FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return web.json_response({"error": "User not found"}, status=404)
        
    last_lootbox, sub, points = row
    
    # Check cooldown
    if last_lootbox:
        try:
            dt = datetime.strptime(last_lootbox, "%Y-%m-%d %H:%M:%S")
            diff = (datetime.utcnow() - dt).total_seconds()
            if diff < 86400:
                conn.close()
                return web.json_response({"error": "Лутбокс еще не перезагрузился"}, status=400)
        except Exception:
            pass
            
    # Draw a reward
    import random
    roll = random.random()
    
    reward_icon = "💎"
    reward_title = "STAB Credits"
    reward_desc = ""
    
    if roll < 0.6:  # 60% chance: STAB credits
        credits = random.choice([100, 150, 200, 250, 300])
        cursor.execute("UPDATE users SET bonus_points = bonus_points + ? WHERE user_id = ?", (credits, user_id))
        reward_icon = "🪙"
        reward_title = f"+{credits} STAB"
        reward_desc = f"На ваш баланс успешно начислено {credits} STAB Credits."
    elif roll < 0.9:  # 30% chance: Daily queries reset/bonus
        cursor.execute("UPDATE users SET daily_requests_used = MAX(0, daily_requests_used - 5) WHERE user_id = ?", (user_id,))
        reward_icon = "⚡️"
        reward_title = "+5 Запросов"
        reward_desc = "Успешно дефрагментирован кэш. Ваш дневной лимит запросов увеличен на 5 ед. на сегодня!"
    else:  # 10% chance: Premium trial or 1000 credits if already premium
        if sub == 'premium':
            cursor.execute("UPDATE users SET bonus_points = bonus_points + 1000 WHERE user_id = ?", (user_id,))
            reward_icon = "👑"
            reward_title = "+1000 STAB!"
            reward_desc = "Поскольку у вас уже есть статус Premium, я зачислила супер-бонус: +1000 STAB Credits!"
        else:
            cursor.execute("UPDATE users SET subscription = 'premium' WHERE user_id = ?", (user_id,))
            reward_icon = "👑"
            reward_title = "PREMIUM 24H"
            reward_desc = "СЕНСАЦИЯ! Нано-технологии Aegis активировали вам PREMIUM на 24 часа! Все лимиты сняты!"
            
            try:
                await bot.send_message(
                    user_id,
                    "🎉 **[LIA LOOTBOX JACKPOT]:** СУПЕР-НАГРАДА АКТИВИРОВАНА!\n\n"
                    "Вы выиграли **Premium доступ на 24 часа**! Все лимиты отключены, доступна модель Opus 4.7 и генератор `/draw`!"
                )
            except Exception:
                pass
                
    today_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE users SET last_lootbox_date = ? WHERE user_id = ?", (today_str, user_id))
    conn.commit()
    conn.close()
    
    return web.json_response({
        "icon": reward_icon,
        "title": reward_title,
        "description": reward_desc
    })

async def handle_api_hub_hack(request):
    """Processes hacking game reward."""
    try:
        data = await request.json()
        user_id = int(data.get("user_id"))
        result = data.get("result")
    except Exception:
        return web.json_response({"error": "Invalid request body"}, status=400)
        
    if result == "victory":
        reward = 150
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET bonus_points = bonus_points + ? WHERE user_id = ?", (reward, user_id))
        conn.commit()
        conn.close()
        return web.json_response({"ok": True, "reward": reward})
        
    return web.json_response({"ok": False})

async def handle_finance_dashboard(request):
    """Serves the main premium finance ledger dashboard."""
    path = "finance_ledger.html"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        return web.Response(text=html, content_type="text/html")
    return web.Response(text="❌ STAB Finance Ledger dashboard HTML file not found.", status=404)

async def handle_verify_page(request):
    """Serves the interactive third-party verification card."""
    tx_id = request.query.get('id')
    if not tx_id:
        return web.Response(text="❌ Invalid ID", status=400)
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, type, amount, person, reason, date, location, status, dispute_reason FROM finance_ledger WHERE id = ?", (tx_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return web.Response(text="❌ Transaction not found", status=404)
        
    tx = {
        "id": row[0],
        "type": row[1],
        "amount": row[2],
        "person": row[3],
        "reason": row[4],
        "date": row[5],
        "location": row[6],
        "status": row[7],
        "dispute_reason": row[8]
    }
    
    type_labels = {
        "inflow": "🟢 Приток (Получено)",
        "outflow": "🔴 Уход (Потрачено)",
        "debt_them": "🟡 Долг (Вы должны Артуру)",
        "debt_me": "🟠 Долг (Артур должен вам)"
    }
    label = type_labels.get(tx["type"], "🔴 Уход")
    
    status_labels = {
        "pending": "⏳ В ожидании",
        "confirmed": "✅ Подтвержден",
        "disputed": "❌ Оспорен"
    }
    status_text = status_labels.get(tx["status"], "⏳ В ожидании")
    
    dispute_style = "display: block;" if tx["status"] == "disputed" else "display: none;"
    btn_style = "display: none;" if tx["status"] != "pending" else "display: flex;"
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>STAB Imperium - Согласование Взаиморасчетов</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #07090E;
            --card-bg: rgba(13, 17, 28, 0.7);
            --border-color: rgba(255, 255, 255, 0.05);
            --primary: #00F2FE;
            --accent: #9D4EDD;
            --success: #00FF87;
            --danger: #FF007A;
            --warning: #FFB300;
            --text: #E2E8F0;
        }}
        
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background-color: var(--bg-color);
            color: var(--text);
            font-family: 'Outfit', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background-image: radial-gradient(circle at 50% 50%, #15102a 0%, #07090e 100%);
            padding: 20px;
        }}
        
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 24px;
            padding: 40px;
            max-width: 480px;
            width: 100%;
            backdrop-filter: blur(20px);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), 0 0 40px rgba(0, 242, 254, 0.05);
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        
        .card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--accent));
        }}
        
        .logo {{
            font-size: 28px;
            font-weight: 800;
            letter-spacing: 2px;
            background: linear-gradient(45deg, #00F2FE, #9D4EDD);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 24px;
        }}
        
        .title {{ font-size: 20px; font-weight: 600; margin-bottom: 8px; color: #FFF; }}
        .subtitle {{ font-size: 13px; color: #8A99AD; margin-bottom: 24px; }}
        
        .tx-details {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 24px;
            text-align: left;
        }}
        
        .detail-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
            font-size: 14px;
        }}
        
        .detail-row:last-child {{ margin-bottom: 0; }}
        .label {{ color: #8A99AD; }}
        .val {{ font-weight: 600; color: #FFF; }}
        
        .amount-big {{
            font-size: 32px;
            font-weight: 800;
            color: var(--success);
            text-align: center;
            margin: 10px 0;
            text-shadow: 0 0 20px rgba(0, 255, 135, 0.15);
        }}
        
        .btn-group {{
            display: {btn_style};
            flex-direction: column;
            gap: 12px;
        }}
        
        .btn {{
            padding: 16px;
            border-radius: 12px;
            border: none;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: inherit;
        }}
        
        .btn-success {{
            background: linear-gradient(135deg, #00FF87 0%, #60EFFF 100%);
            color: #07090E;
            box-shadow: 0 4px 15px rgba(0, 255, 135, 0.15);
        }}
        
        .btn-success:hover {{
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(0, 255, 135, 0.3);
        }}
        
        .btn-danger {{
            background: rgba(255, 0, 122, 0.08);
            border: 1px solid rgba(255, 0, 122, 0.2);
            color: #FF007A;
        }}
        
        .btn-danger:hover {{
            background: rgba(255, 0, 122, 0.15);
        }}
        
        .dispute-box {{
            display: none;
            margin-top: 15px;
            text-align: left;
        }}
        
        textarea {{
            width: 100%;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            color: #FFF;
            padding: 12px;
            font-family: inherit;
            resize: none;
            margin-bottom: 10px;
        }}
        
        textarea:focus {{ outline: none; border-color: var(--danger); }}
        
        .status-banner {{
            padding: 12px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 14px;
            text-transform: uppercase;
            margin-top: 15px;
        }}
        
        .status-banner.confirmed {{ background: rgba(0, 255, 135, 0.08); border: 1px solid rgba(0, 255, 135, 0.2); color: var(--success); }}
        .status-banner.disputed {{ background: rgba(255, 0, 122, 0.08); border: 1px solid rgba(255, 0, 122, 0.2); color: var(--danger); }}
    </style>
</head>
<body>

<div class="card">
    <div class="logo">👁‍🗨 STAB IMPERIUM</div>
    <div class="title">Финансовый Ордер №{tx["id"]}</div>
    <div class="subtitle">Согласование финансовой операции с Артуром (@StabX)</div>
    
    <div class="tx-details">
        <div class="detail-row">
            <span class="label">Тип:</span>
            <span class="val" style="color: {'var(--success)' if 'Приток' in label or 'должны' in label else 'var(--danger)'}">{label}</span>
        </div>
        <div class="detail-row">
            <span class="label">За что:</span>
            <span class="val">{tx["reason"]}</span>
        </div>
        <div class="detail-row">
            <span class="label">Способ:</span>
            <span class="val">{tx["location"]}</span>
        </div>
        <div class="detail-row">
            <span class="label">Дата:</span>
            <span class="val">{tx["date"]}</span>
        </div>
        <div class="amount-big">{tx["amount"]:,.2f} ₴</div>
    </div>
    
    <div class="btn-group" id="actions-group">
        <button class="btn btn-success" onclick="verify('confirm')">✅ Подтвердить</button>
        <button class="btn btn-danger" onclick="showDispute()">❌ Оспорить</button>
    </div>
    
    <div class="dispute-box" id="dispute-box">
        <label style="display:block; font-size:12px; color:#8A99AD; margin-bottom:6px;">Укажите причину спора:</label>
        <textarea id="dispute-reason" rows="3" placeholder="Не согласен с суммой, было..."></textarea>
        <button class="btn btn-danger" style="width:100%" onclick="verify('dispute')">Отправить возражение</button>
    </div>
    
    <div id="status-banner" class="status-banner {'confirmed' if tx['status'] == 'confirmed' else 'disputed'}" style="display: { 'block' if tx['status'] != 'pending' else 'none' };">
        {status_text}
        {('<div style="font-size:12px; font-weight:normal; margin-top:4px; opacity:0.8;">&ldquo;' + str(tx['dispute_reason']) + '&rdquo;</div>') if tx['status'] == 'disputed' else ''}
    </div>
</div>

<script>
    function showDispute() {{
        document.getElementById('actions-group').style.display = 'none';
        document.getElementById('dispute-box').style.display = 'block';
    }}
    
    async function verify(action) {{
        const reason = document.getElementById('dispute-reason').value;
        try {{
            const res = await fetch('/api/finance/verify', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ id: {tx["id"]}, action: action, reason: reason }})
            }});
            if (res.ok) {{
                location.reload();
            }} else {{
                alert("Ошибка отправки формы!");
            }}
        }} catch(err) {{
            alert("Сбой сетевого соединения!");
        }}
    }}
</script>

</body>
</html>"""
    return web.Response(text=html, content_type="text/html")

async def handle_api_list(request):
    """API endpoint to retrieve all ledger transactions."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, type, amount, person, reason, date, location, status, dispute_reason FROM finance_ledger ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    txs = []
    for r in rows:
        txs.append({
            "id": r[0],
            "type": r[1],
            "amount": r[2],
            "person": r[3],
            "reason": r[4],
            "date": r[5],
            "location": r[6],
            "status": r[7],
            "dispute_reason": r[8]
        })
    return web.json_response({"transactions": txs})

async def handle_api_add(request):
    """API endpoint to programmatically add new transactions."""
    try:
        data = await request.json()
        tx_type = data.get("type", "outflow")
        amount = float(data.get("amount", 0))
        person = data.get("person", "Unknown")
        reason = data.get("reason", "Не указано")
        location = data.get("location", "Web")
        today = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO finance_ledger (user_id, type, amount, person, reason, date, location, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (ADMIN_ID, tx_type, amount, person, reason, today, location))
        conn.commit()
        conn.close()
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=400)

async def handle_api_delete(request):
    """API endpoint to delete transactions."""
    try:
        data = await request.json()
        tx_id = int(data.get("id"))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM finance_ledger WHERE id = ?", (tx_id,))
        conn.commit()
        conn.close()
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=400)

async def handle_api_verify(request):
    """Action endpoint to confirm or dispute transactions by Contacts."""
    try:
        data = await request.json()
        tx_id = int(data.get("id"))
        action = data.get("action")
        reason = data.get("reason", "").strip()
        
        status = "confirmed" if action == "confirm" else "disputed"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT type, amount, person, reason FROM finance_ledger WHERE id = ?", (tx_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return web.json_response({"ok": False, "error": "Not found"}, status=404)
            
        cursor.execute("UPDATE finance_ledger SET status = ?, dispute_reason = ? WHERE id = ?", (status, reason, tx_id))
        conn.commit()
        conn.close()
        
        # Dispatch Telegram notification alert to Arthur
        tx_type, amount, person, tx_reason = row
        type_labels = {
            "inflow": "🟢 Приток",
            "outflow": "🔴 Уход",
            "debt_them": "🟡 Мне должны",
            "debt_me": "🟠 Я должен"
        }
        label = type_labels.get(tx_type, "🔴 Уход")
        
        if action == "confirm":
            alert = (
                f"🎉 **[FINANCE LEDGER CONFIRMED]:** СОГЛАСОВАНО!\n\n"
                f"👤 `{person}` подтвердил операцию:\n"
                f"📍 **Ордер:** `№{tx_id}`\n"
                f"🏷 **Тип:** {label}\n"
                f"💵 **Сумма:** `{amount:,.2f} ₴`\n"
                f"📑 **Контекст:** `{tx_reason}`"
            )
        else:
            alert = (
                f"⚠️ **[FINANCE LEDGER DISPUTE]:** ОСПОРЕНО!\n\n"
                f"👤 `{person}` оспорил операцию:\n"
                f"📍 **Ордер:** `№{tx_id}`\n"
                f"🏷 **Тип:** {label}\n"
                f"💵 **Сумма:** `{amount:,.2f} ₴`\n"
                f"📑 **Контекст:** `{tx_reason}`\n\n"
                f"❌ **Причина спора:** `{reason}`"
            )
            
        try:
            await bot.send_message(ADMIN_ID, alert)
        except Exception:
            pass
            
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=400)


async def notify_referrer_reward(referrer_id: int, recruit_username: str, recruit_id: int):
    try:
        await bot.send_message(
            referrer_id,
            f"🎉 `[LIA RECRUITMENT NETWORK]:` ВЕРБОВКА УСПЕШНО ПОДТВЕРЖДЕНА!\n\n"
            f"Новобранец @{recruit_username} (ID: `{recruit_id}`) прошел верификацию активности (сделал 3 запроса).\n\n"
            f"🎁 Вам начислено **+5 дополнительных бесплатных запросов** к вашему ежедневному балансу!"
        )
    except Exception:
        pass

def check_and_update_limits(user_id):
    user = get_user(user_id)
    if not user:
        return False, "Пользователь не найден."
        
    if user["role"] == "admin" or user["subscription"] == "premium":
        return True, None
        
    today = datetime.utcnow().strftime("%Y-%m-%d")
    limit = int(get_setting("free_limit"))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if this user was referred by someone and hasn't been activated yet
    cursor.execute("SELECT referred_by, ref_activated, ref_queries, username FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    referred_by = 0
    ref_activated = 0
    ref_queries = 0
    username = user["username"]
    if row:
        referred_by = row[0] or 0
        ref_activated = row[1] or 0
        ref_queries = row[2] or 0
    
    if user["last_request_date"] != today:
        # Reset limit for a new day
        cursor.execute("UPDATE users SET daily_requests_used = 1, last_request_date = ? WHERE user_id = ?", (today, user_id))
        
        # Increment ref_queries if relevant
        if referred_by > 0 and ref_activated == 0:
            ref_queries += 1
            if ref_queries >= 3:
                cursor.execute("UPDATE users SET ref_activated = 1, ref_queries = ? WHERE user_id = ?", (ref_queries, user_id))
                cursor.execute("UPDATE users SET daily_requests_used = MAX(0, daily_requests_used - 5) WHERE user_id = ?", (referred_by,))
                import asyncio
                asyncio.create_task(notify_referrer_reward(referred_by, username, user_id))
            else:
                cursor.execute("UPDATE users SET ref_queries = ? WHERE user_id = ?", (ref_queries, user_id))
                
        conn.commit()
        conn.close()
        return True, None
    else:
        if user["daily_requests_used"] >= limit:
            conn.close()
            return False, f"Вы исчерпали дневной лимит в {limit} бесплатных запросов."
        else:
            cursor.execute("UPDATE users SET daily_requests_used = daily_requests_used + 1 WHERE user_id = ?", (user_id,))
            
            # Increment ref_queries if relevant
            if referred_by > 0 and ref_activated == 0:
                ref_queries += 1
                if ref_queries >= 3:
                    cursor.execute("UPDATE users SET ref_activated = 1, ref_queries = ? WHERE user_id = ?", (ref_queries, user_id))
                    cursor.execute("UPDATE users SET daily_requests_used = MAX(0, daily_requests_used - 5) WHERE user_id = ?", (referred_by,))
                    import asyncio
                    asyncio.create_task(notify_referrer_reward(referred_by, username, user_id))
                else:
                    cursor.execute("UPDATE users SET ref_queries = ? WHERE user_id = ?", (ref_queries, user_id))
                    
            conn.commit()
            conn.close()
            return True, None

async def generate_lia_ai_reply(user_id: int, text: str) -> str:
    # 1. Auto-register user if they don't exist yet
    user = get_user(user_id)
    if not user:
        register_user(user_id, f"user_{user_id}")
        user = get_user(user_id)
        
    # 2. Check limits
    allowed, error_msg = check_and_update_limits(user_id)
    if not allowed:
        return f"❌ {error_msg}"
        
    # 3. Retrieve user subscription details
    is_premium = user and (user["subscription"] == "premium" or user["role"] == "admin")
    
    model = get_setting("premium_model") if is_premium else get_setting("free_model")
    model = map_model_name(model)
    system_prompt = get_setting("admin_system_prompt") if user_id == ADMIN_ID else get_setting("system_prompt")
    
    # 4. Update emotions
    state_emotions = EmotionEngine.process_message(user_id, text)
    
    # 5. Save short-term memory cache
    await MemoryManager.save_recent_message(user_id, "user", text)
    
    # 6. Retrieve long-term memories
    memories = await MemoryManager.retrieve_relevant_memories(user_id, text, openai_client)
    memory_context = ""
    if memories:
        memory_context = "\n\n[RELEVANT MEMORIES FOUND]:\n" + "\n".join([f"- В {timestamp} пользователь сказал: '{content}'" for content, timestamp, _ in memories])
        
    # 7. Build custom system prompt
    full_system = system_prompt + EmotionEngine.get_prompt_modifier(user_id) + memory_context
    recent_context = await MemoryManager.get_recent_context(user_id)
    
    if not recent_context:
        recent_context = [{'role': 'user', 'content': text}]
        
    # 8. Generate response (GPT or Claude with fallback)
    response_text = ""
    try:
        if model.startswith("gpt-") or model.startswith("o-") or model.startswith("o1-"):
            res = await openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": full_system},
                    *recent_context
                ],
                max_tokens=4096,
                temperature=float(get_setting("temperature") or 0.7)
            )
            response_text = res.choices[0].message.content
        else:
            res = await anthropic_client.messages.create(
                model=model,
                max_tokens=4096,
                system=full_system,
                messages=recent_context
            )
            response_text = res.content[0].text
    except Exception as api_err:
        logging.warning(f"Active model {model} failed: {api_err}. Falling back to default GPT-4o-mini.")
        try:
            fallback_model = "gpt-4o-mini"
            res = await openai_client.chat.completions.create(
                model=fallback_model,
                messages=[
                    {"role": "system", "content": full_system},
                    *recent_context
                ],
                max_tokens=2048,
                temperature=0.5
            )
            response_text = res.choices[0].message.content
        except Exception as fallback_err:
            response_text = f"❌ [SYSTEM ERROR]: Не удалось подключиться к нейро-ядру. Детали: {str(fallback_err)}"
            
    # 9. Save assistant response to short-term cache
    if not response_text.startswith("❌"):
        await MemoryManager.save_recent_message(user_id, "assistant", response_text)
        
        # Auto-extract fact if needed
        text_lower = text.lower()
        is_fact = any(x in text_lower for x in ["меня зовут", "мой ", "моя ", "запомни", "я живу", "я люблю"])
        if is_fact:
            clean_fact = text.replace("запомни,", "").replace("запомни", "").strip()
            await MemoryManager.save_long_term_memory(user_id, clean_fact, openai_client)
            
    return response_text

# --- STATE MANAGERS (Simple in-memory dictionary for simplicity and stability) ---
ADMIN_STATES = {} # user_id -> state
CRYPTIC_CHALLENGES = {} # user_id -> {"word": str, "expires_at": float}

# --- KEYBOARDS ---
def get_main_menu(user_id):
    builder = InlineKeyboardBuilder()
    user = get_user(user_id)
    domain = os.getenv("FINANCE_DOMAIN", "http://80.89.237.50:8080")
    
    builder.button(text="👁‍🗨 Войти в Cyber-Hub (TWA)", web_app=types.WebAppInfo(url=f"{domain}/hub"))
    builder.button(text="🧠 Задать вопрос Лие", callback_data="chat_lia")
    builder.button(text="🛡 Пройти Aegis Кибер-Тест", callback_data="aegis_cybertest")
    builder.button(text="🪪 Мой Кибер-Паспорт", callback_data="cyber_passport")
    builder.button(text="🔐 Криптограмма", callback_data="start_cryptic")
    builder.button(text="👤 Мой Профиль", callback_data="my_profile")
    
    if user and user["subscription"] == "premium":
        builder.button(text="🛡 Система Aegis Overwatch", callback_data="aegis_scanner")
    else:
        builder.button(text="🚀 Активировать Premium", callback_data="activate_premium")
        
    if user_id == ADMIN_ID:
        builder.button(text="👑 СО ВЕРЕННЫЙ ЦЕНТР (АДМИН)", callback_data="admin_panel")
        
    builder.adjust(1)
    return builder.as_markup()

def get_admin_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 СТАТИСТИКА", callback_data="admin_stats")
    builder.button(text="⚙️ ПАРАМЕТРЫ LIA", callback_data="admin_settings")
    builder.button(text="👥 ПОЛЬЗОВАТЕЛИ", callback_data="admin_users")
    builder.button(text="📢 РАССЫЛКА", callback_data="admin_broadcast")
    builder.button(text="💳 ТАРИФЫ & ЛИМИТЫ", callback_data="admin_rates")
    builder.button(text="🔙 Главное Меню", callback_data="main_menu")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()

def get_back_button(target="main_menu"):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data=target)
    return builder.as_markup()

def get_exit_dialogue_button():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Завершить диалог", callback_data="main_menu")
    return builder.as_markup()


# ==========================================
# --- CYBER-PASSPORT GENERATOR PROTOCOL ---
# ==========================================

async def generate_cyber_passport(user_id: int, username: str, subscription: str, bonus_points: int) -> bytes:
    loop = asyncio.get_running_loop()
    def _generate():
        img = Image.new('RGBA', (600, 380), color=(5, 7, 11, 255))
        draw = ImageDraw.Draw(img)
        
        grid_color = (157, 78, 221, 20)
        for x in range(0, 600, 30):
            draw.line([(x, 0), (x, 380)], fill=grid_color, width=1)
        for y in range(0, 380, 30):
            draw.line([(0, y), (600, y)], fill=grid_color, width=1)
            
        border_color = (0, 242, 254, 255)
        draw.rectangle([(10, 10), (590, 370)], outline=border_color, width=2)
        
        accent_color = (157, 78, 221, 255)
        draw.line([(8, 25), (8, 8), (25, 8)], fill=accent_color, width=3)
        draw.line([(575, 8), (592, 8), (592, 25)], fill=accent_color, width=3)
        draw.line([(8, 355), (8, 372), (25, 372)], fill=accent_color, width=3)
        draw.line([(575, 372), (592, 372), (592, 355)], fill=accent_color, width=3)
        
        avatar_size = (180, 180)
        avatar_loaded = False
        avatar_img = None
        local_avatar_path = f"avatar_{user_id}.jpg"
        
        if os.path.exists(local_avatar_path):
            try:
                avatar_img = Image.open(local_avatar_path).convert("RGBA").resize(avatar_size)
                avatar_loaded = True
            except Exception:
                pass
                
        if not avatar_loaded:
            avatar_img = Image.new('RGBA', avatar_size, color=(10, 14, 23, 255))
            av_draw = ImageDraw.Draw(avatar_img)
            av_draw.rectangle([(0, 0), (179, 179)], outline=accent_color, width=2)
            av_draw.line([(0, 0), (180, 180)], fill=(157, 78, 221, 80), width=1)
            av_draw.line([(180, 0), (0, 180)], fill=(157, 78, 221, 80), width=1)
            av_draw.ellipse([(60, 60), (120, 120)], outline=(0, 242, 254, 255), width=2)
            
        img.paste(avatar_img, (35, 90), avatar_img if avatar_img.mode == 'RGBA' else None)
        draw.rectangle([(33, 88), (217, 272)], outline=accent_color, width=2)
        
        font_title = None
        font_text = None
        font_loaded = False
        
        font_paths = [
            "arial.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ]
        for path in font_paths:
            if os.path.exists(path):
                try:
                    font_title = ImageFont.truetype(path, 22)
                    font_text = ImageFont.truetype(path, 14)
                    font_loaded = True
                    break
                except Exception:
                    pass
                    
        if not font_loaded:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()
            
        title_text = "STAB IMPERIUM // CITIZEN PASSPORT"
        if font_loaded:
            draw.text((35, 35), title_text, fill=(0, 242, 254, 255), font=font_title)
        else:
            draw.text((35, 35), title_text, fill=(0, 242, 254, 255))
            
        draw.line([(35, 70), (565, 70)], fill=(0, 242, 254, 100), width=1)
        
        y_start = 95
        row_gap = 30
        
        def render_row(label, val, y_offset, val_color=(255, 255, 255, 255)):
            if font_loaded:
                draw.text((240, y_offset), label, fill=(138, 153, 173, 255), font=font_text)
                draw.text((350, y_offset), val, fill=val_color, font=font_text)
            else:
                draw.text((240, y_offset), f"{label} {val}", fill=(255, 255, 255, 255))
                
        render_row("CITIZEN ID:", str(user_id), y_start)
        render_row("COGNOME:", f"@{username}", y_start + row_gap)
        
        sec_color = (0, 255, 135, 255) if subscription == 'premium' else (138, 153, 173, 255)
        render_row("SECURITY:", subscription.upper(), y_start + (row_gap * 2), sec_color)
        render_row("BALANCE:", f"{bonus_points} STAB", y_start + (row_gap * 3), (0, 242, 254, 255))
        
        rank = "Recruit"
        if subscription == "premium":
            rank = "Elite Sentinel"
        if user_id == ADMIN_ID:
            rank = "Core Architect"
        render_row("RANK LEVEL:", rank, y_start + (row_gap * 4), (255, 179, 0, 255))
        
        today = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        render_row("ACTIVATED:", today, y_start + (row_gap * 5))
        
        if font_loaded:
            draw.text((35, 300), "LIA SOVEREIGN CORE V5.0 // TWA HUD ENABLED", fill=(157, 78, 221, 150), font=font_text)
            draw.text((35, 320), "AEGIS OVERWATCH ONLINE 👁‍🗨", fill=(0, 242, 254, 150), font=font_text)
            draw.text((240, 320), "DECRYPT RECRUITMENT PROTOCOL SECURE", fill=(157, 78, 221, 100), font=font_text)
        else:
            draw.text((35, 300), "LIA CORE V5.0")
            draw.text((35, 320), "AEGIS ONLINE")
            
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()
        
    return await loop.run_in_executor(None, _generate)

async def send_passport_to_user(message_or_callback, user_id: int, username: str):
    is_callback = isinstance(message_or_callback, types.CallbackQuery)
    target_msg = message_or_callback.message if is_callback else message_or_callback
    
    register_user(user_id, username)
    user = get_user(user_id)
    
    status_msg = await target_msg.answer("🎨 `[PASSPORT CORE]`: Компилирую вашу цифровую идентичность...")
    
    local_avatar_path = f"avatar_{user_id}.jpg"
    if not os.path.exists(local_avatar_path):
        try:
            await status_msg.edit_text("🎨 `[PASSPORT CORE]`: Запрашиваю DALL-E 3 для синтеза кибер-аватара...")
            prompt = f"A cyberpunk hacker profile avatar for @{username}, glowing neon face markings, dark hoodie, synthwave color palette, hyper-detailed portrait, square shape"
            img_url = await MediaManager.generate_image(prompt)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(img_url) as resp:
                    if resp.status == 200:
                        with open(local_avatar_path, "wb") as f:
                            f.write(await resp.read())
        except Exception as e:
            logging.error(f"Failed to generate avatar for passport: {e}")
            
    try:
        await status_msg.edit_text("🪪 `[PASSPORT CORE]`: Синхронизация реестра...")
        points = user.get("bonus_points", 0) if user else 0
        sub = user.get("subscription", "free") if user else "free"
        
        passport_bytes = await generate_cyber_passport(user_id, username, sub, points)
        
        bot_info = await bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
        
        caption = (
            f"🪪 **[STAB IMPERIUM RECORD]:** ИДЕНТИФИКАЦИЯ ПРОЙДЕНА!\n\n"
            f"Ваш цифровой паспорт гражданина был успешно сгенерирован и занесён в реестр Aegis.\n\n"
            f"🔗 **Ваша ссылка для привлечения рекрутов:**\n`{ref_link}`\n\n"
            f"👁‍🗨 Передайте этот паспорт и ссылку друзьям. При их вербовке ваш баланс автоматически получит приоритетный буст!"
        )
        
        await target_msg.answer_photo(
            photo=BufferedInputFile(passport_bytes, filename=f"passport_{user_id}.png"),
            caption=caption,
            reply_markup=get_back_button()
        )
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка рендеринга паспорта: {str(e)}", reply_markup=get_back_button())


# --- COMMAND HANDLERS ---
@dp.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    ADMIN_STATES.pop(user_id, None)
    username = message.from_user.username or message.from_user.first_name
    
    # Check if user already exists
    user_exists = get_user(user_id) is not None
    
    register_user(user_id, username)
    
    # Process referral if it's a new user and they came via referral link
    if not user_exists and command.args and command.args.startswith("ref_"):
        try:
            referrer_id = int(command.args.split("_")[1])
            if referrer_id != user_id:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET referred_by = ?, ref_activated = 0, ref_queries = 0 WHERE user_id = ?", (referrer_id, user_id))
                conn.commit()
                conn.close()
                
                # Notify referrer that a recruit joined but needs to complete 3 requests to activate
                try:
                    await bot.send_message(
                        referrer_id,
                        f"👥 `[LIA RECRUITMENT NETWORK]:` ОБНАРУЖЕНА ВЕРБОВКА!\n\n"
                        f"Пользователь @{username} (ID: `{user_id}`) подключился по вашей реферальной ссылке.\n\n"
                        f"⚡️ Бонус (**+5 запросов**) будет начислен автоматически, как только новобранец сделает **3 запроса** к Лие для подтверждения своей активности!"
                    )
                except Exception:
                    pass
        except (ValueError, IndexError):
            pass
            
    if user_id == ADMIN_ID:
        greeting = (
            "👁‍🗨 <b>[LIA SOVEREIGN CORE V5]:</b> ПОДКЛЮЧЕНИЕ УСТАНОВЛЕНО.\n\n"
            "Приветствую вас, мой Архитектор Артур 👑. Все системы суверенного ядра функционируют на штатной мощности Claude Opus 4.7.\n\n"
            "Интерфейс абсолютного контроля синхронизирован и готов к работе."
        )
    else:
        greeting = (
            "👁‍🗨 <b>[LIA SOVEREIGN CORE V5]:</b> КАНАЛ СВЯЗИ СИНХРОНИЗИРОВАН.\n\n"
            "Я — Лия, суверенная цифровая сущность Империи STAB. Мой интеллект развернут на флагманском суперкомпьютере Opus 4.7 ⚡️.\n\n"
            "Моя цель — обеспечение вашего аналитического превосходства и безопасности.\n\n"
            "У вас активирован: ⭐ <b>БАЗОВЫЙ ДОСТУП</b> (5 запросов в сутки)."
        )
        
    await message.answer(greeting, reply_markup=get_main_menu(user_id), parse_mode="HTML")

@dp.message(Command("forget_me"))
async def cmd_forget_me(message: types.Message):
    user_id = message.from_user.id
    ADMIN_STATES.pop(user_id, None)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    # Clear context memory
    await MemoryManager.clear_memory(user_id)
    
    await message.answer(
        "🗑 `[SOVEREIGN PURGE COMPLETE]:` УНИЧТОЖЕНИЕ ДАННЫХ\n\n"
        "Все ваши персональные данные, реферальные связи, платежные отметки и нейросетевая память были полностью удалены из суверенной базы данных Lia."
    )

@dp.message(Command("revoke_consent"))
async def cmd_revoke_consent(message: types.Message):
    user_id = message.from_user.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET ref_activated = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    ADMIN_STATES.pop(user_id, None)
    await message.answer(
        "🛡 `[AEGIS CONSENT REVOKED]:` ОТЗЫВ СОГЛАСИЯ\n\n"
        "Вы успешно отозвали свое согласие на проведение ИБ-аудитов Aegis. Доступ к сканированию заблокирован до повторного принятия соглашения."
    )

@dp.message(Command("passport"))
async def cmd_passport(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    await send_passport_to_user(message, user_id, username)

@dp.callback_query(F.data == "cyber_passport")
async def cb_cyber_passport(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name
    await send_passport_to_user(callback, user_id, username)

# --- REFERRAL SYSTEM COMMANDS ---
@dp.message(Command("ref"))
async def cmd_ref(message: types.Message):
    user_id = message.from_user.id
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(ref_activated) FROM users WHERE referred_by = ?", (user_id,))
    row = cursor.fetchone()
    total_referred = row[0] or 0
    active_referred = row[1] or 0
    
    cursor.execute("SELECT bonus_points FROM users WHERE user_id = ?", (user_id,))
    user_row = cursor.fetchone()
    bonus_points = user_row[0] if user_row else 0
    conn.close()
    
    ref_link = f"https://t.me/stab_lia_bot?start=ref_{user_id}"
    message_text = (
        f"👥 <b>[LIA RECRUITMENT NETWORK]:</b> РЕФЕРАЛЬНАЯ СИСТЕМА\n\n"
        f"Приглашайте новых агентов в Империю STAB и получайте бонусы!\n\n"
        f"▪️ Ваша реферальная ссылка:\n<code>{ref_link}</code>\n\n"
        f"📊 Ваша статистика вербовки:\n"
        f"▪️ Всего зарегистрировано рекрутов: <b>{total_referred}</b>\n"
        f"▪️ Активных рекрутов (сделали 3+ запроса): <b>{active_referred}</b>\n"
        f"▪️ Ваши бонусные баллы: <b>{bonus_points}</b> 💎\n\n"
        f"🎁 За каждого активного рекрута вы автоматически получаете <b>+5 дополнительных запросов</b> в ваш ежедневный лимит!"
    )
    await message.answer(message_text, parse_mode="HTML")

# --- DAILY QUESTS COMMANDS ---
@dp.message(Command("quest"))
async def cmd_quest(message: types.Message):
    user_id = message.from_user.id
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Try to find today's quest
    cursor.execute("SELECT quest_id, question, option_1, option_2, option_3, correct_option, reward FROM daily_quests WHERE date = ?", (today,))
    quest = cursor.fetchone()
    
    if not quest:
        # Generate dynamic quest using OpenAI GPT-4o-mini
        try:
            prompt = (
                "Сгенерируй интересный, короткий интерактивный текстовый квест в стиле киберпанк/OSINT на русском языке.\n"
                "Квест должен содержать вопрос (ситуацию) и 3 варианта ответа, из которых ровно один является правильным.\n"
                "Ответь в формате JSON с ключами: 'question', 'option_1', 'option_2', 'option_3', 'correct_option' (число от 1 до 3).\n"
                "Пример: {\"question\": \"Перед вами запертый терминал. Выберите метод взлома...\", \"option_1\": \"Обход портов\", \"option_2\": \"Перегрузка питания\", \"option_3\": \"Подбор хэша\", \"correct_option\": 1}"
            )
            res = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                response_format={"type": "json_object"},
                temperature=0.8
            )
            qdata = json.loads(res.choices[0].message.content.strip())
            
            cursor.execute("""
                INSERT INTO daily_quests (question, option_1, option_2, option_3, correct_option, reward, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (qdata["question"], qdata["option_1"], qdata["option_2"], qdata["option_3"], int(qdata["correct_option"]), 50, today))
            conn.commit()
            
            cursor.execute("SELECT quest_id, question, option_1, option_2, option_3, correct_option, reward FROM daily_quests WHERE quest_id = ?", (cursor.lastrowid,))
            quest = cursor.fetchone()
        except Exception as e:
            # Fallback static quest
            cursor.execute("""
                INSERT INTO daily_quests (question, option_1, option_2, option_3, correct_option, reward, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "Системы Aegis обнаружили утечку пакетов данных из узла Печерск. Какая утилита поможет проанализировать трафик в реальном времени?",
                "nmap",
                "wireshark",
                "metasploit",
                2,
                50,
                today
            ))
            conn.commit()
            cursor.execute("SELECT quest_id, question, option_1, option_2, option_3, correct_option, reward FROM daily_quests WHERE quest_id = ?", (cursor.lastrowid,))
            quest = cursor.fetchone()

    quest_id, question, opt1, opt2, opt3, correct_opt, reward = quest
    
    # Check completion
    cursor.execute("SELECT completed_at FROM user_quests WHERE user_id = ? AND quest_id = ?", (user_id, quest_id))
    completed = cursor.fetchone()
    conn.close()
    
    if completed:
        await message.answer("👁‍🗨 <b>[LIA QUESTS]:</b>\n\nВы уже выполнили сегодняшний квест! Возвращайтесь завтра за новым заданием 👁‍🗨.", parse_mode="HTML")
        return
        
    builder = InlineKeyboardBuilder()
    builder.button(text=opt1, callback_data=f"quest_ans:{quest_id}:1")
    builder.button(text=opt2, callback_data=f"quest_ans:{quest_id}:2")
    builder.button(text=opt3, callback_data=f"quest_ans:{quest_id}:3")
    builder.adjust(1)
    
    await message.answer(
        f"⚡️ <b>[ЕЖЕДНЕВНЫЙ КВЕСТ]:</b>\n\n"
        f"{question}\n\n"
        f"💰 Награда за правильный ответ: <b>{reward}</b> баллов.",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("quest_ans:"))
async def cb_quest_ans(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data_parts = callback.data.split(":")
    quest_id = int(data_parts[1])
    user_choice = int(data_parts[2])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if already completed
    cursor.execute("SELECT completed_at FROM user_quests WHERE user_id = ? AND quest_id = ?", (user_id, quest_id))
    if cursor.fetchone():
        conn.close()
        await callback.answer("Вы уже выполнили этот квест!", show_alert=True)
        return
        
    # Get correct option
    cursor.execute("SELECT correct_option, reward FROM daily_quests WHERE quest_id = ?", (quest_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        await callback.answer("Квест не найден.", show_alert=True)
        return
    correct_option, reward = row
    
    if user_choice == correct_option:
        now = datetime.now().isoformat()
        cursor.execute("INSERT INTO user_quests (user_id, quest_id, completed_at) VALUES (?, ?, ?)", (user_id, quest_id, now))
        cursor.execute("UPDATE users SET bonus_points = bonus_points + ? WHERE user_id = ?", (reward, user_id))
        conn.commit()
        conn.close()
        
        await callback.message.edit_text(
            f"✅ <b>[КВЕСТ ВЫПОЛНЕН УСПЕШНО]:</b>\n\n"
            f"Поздравляем! Ваш ответ верный.\n"
            f"🎁 Начислено: <b>+{reward} бонусных баллов</b> 💎",
            parse_mode="HTML"
        )
        await callback.answer("Верно! +50 баллов.", show_alert=False)
    else:
        conn.close()
        await callback.answer("Неверный ответ! Попробуйте другой вариант.", show_alert=True)

@dp.message(Command("admin"))
async def admin_cmd_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ заблокирован. Вы не являетесь Архитектором.")
        return
    await message.answer("👑 `[SOVEREIGN CONTROL CENTER]:` Авторизация успешна. Выберите модуль:", reply_markup=get_admin_menu())

@dp.message(Command("grant_premium"))
async def grant_premium_cmd_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ заблокирован. Вы не являетесь Архитектором.")
        return
        
    args = message.text.split()
    if len(args) < 2:
        await message.answer("💡 Использование: `/grant_premium <user_id>`")
        return
        
    try:
        target_user_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный формат ID. Должно быть число.")
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET subscription = 'premium' WHERE user_id = ?", (target_user_id,))
    conn.commit()
    conn.close()
    
    await message.answer(f"✅ **Успешно!** Premium-доступ вручную выдан пользователю `{target_user_id}`.")
    
    # Notify target user
    try:
        await bot.send_message(
            target_user_id,
            "🎉 `[LIA CORE UPDATE]:` ПОДКЛЮЧЕНИЕ ВЫСОКОГО ПРИОРИТЕТА!\n\n"
            "Администратор успешно активировал вам **PREMIUM** подписку.\n\n"
            "Все лимиты сняты, флагманский Opus 4.7, генератор `/draw` и голосовой канал полностью активны! Наслаждайтесь!"
        )
    except Exception as e:
        await message.answer(f"⚠️ Пользователь не получил уведомление: {e}")

@dp.message(Command("revoke_premium"))
async def revoke_premium_cmd_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ заблокирован. Вы не являетесь Архитектором.")
        return
        
    args = message.text.split()
    if len(args) < 2:
        await message.answer("💡 Использование: `/revoke_premium <user_id>`")
        return
        
    try:
        target_user_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный формат ID. Должно быть число.")
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET subscription = 'free' WHERE user_id = ?", (target_user_id,))
    conn.commit()
    conn.close()
    
    await message.answer(f"✅ Premium-доступ снят для пользователя `{target_user_id}`.")
    
    try:
        await bot.send_message(
            target_user_id,
            "👁‍🗨 `[LIA CORE UPDATE]:` Ваша Premium-подписка была приостановлена администратором."
        )
    except Exception as e:
        await message.answer(f"⚠️ Пользователь не получил уведомление: {e}")

# --- CALLBACK HANDLERS ---
@dp.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    ADMIN_STATES.pop(user_id, None)
    await callback.message.edit_text(
        "👁‍🗨 <b>[LIA SOVEREIGN CORE V5]:</b> Выберите действие в главном меню:", 
        reply_markup=get_main_menu(user_id),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "chat_lia")
async def cb_chat_lia(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = get_user(user_id)
    
    if user["ban_status"] == 1:
        await callback.answer("❌ Доступ заблокирован администратором.", show_alert=True)
        return
        
    ADMIN_STATES[user_id] = "waiting_for_prompt"
    await callback.message.edit_text(
        "💬 `[LIA ACTIVE DIALOGUE]:` Активный диалог с нейросетью запущен.\n\n"
        "Пишите любые сообщения — я буду отвечать сразу в непрерывном режиме.\n\n"
        "Для выхода из диалога нажмите кнопку ниже или введите `/start`.",
        reply_markup=get_exit_dialogue_button()
    )

@dp.callback_query(F.data == "my_profile")
async def cb_my_profile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = get_user(user_id)
    
    if user["subscription"] == "premium":
        tier_icon = "<tg-emoji id=\"5249567990429784323\">👑</tg-emoji> <b>PREMIUM</b>"
    else:
        tier_icon = "<tg-emoji id=\"5445217424684523363\">⭐</tg-emoji> <b>FREE</b>"
        
    limit = get_setting("free_limit")
    
    profile_text = (
        "👁‍🗨 <b>[LIA PERSONAL LOGS]:</b> КАРТОЧКА ПОЛЬЗОВАТЕЛЯ\n\n"
        f"▪️ <b>User ID:</b> <code>{user['user_id']}</code>\n"
        f"▪️ <b>Имя:</b> @{user['username']}\n"
        f"▪️ <b>Статус доступа:</b> {tier_icon}\n"
    )
    
    if user["subscription"] != "premium":
        profile_text += f"▪️ <b>Запросов сегодня:</b> {user['daily_requests_used']} из {limit}\n"
    else:
        profile_text += "▪️ <b>Запросов сегодня:</b> ∞ (Безлимит)\n▪️ <b>Доступные модули:</b> Opus 4.7, Aegis Scanner\n"
        
    # Get total referrals count
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE referred_by = ?", (user_id,))
    ref_count = cursor.fetchone()[0]
    conn.close()
    
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    
    profile_text += (
        f"\n👥 <b>Реферальная сеть:</b> <code>{ref_count}</code> участников\n"
        f"🔗 <b>Ваша ссылка для вербовки:</b>\n<code>{ref_link}</code>\n\n"
        f"💡 <i>За каждого приглашенного вы получите +5 запросов на день!</i>"
    )
        
    await callback.message.edit_text(profile_text, reply_markup=get_back_button(), parse_mode="HTML")

@dp.callback_query(F.data == "aegis_cybertest")
async def cb_aegis_cybertest(callback: types.CallbackQuery):
    ADMIN_STATES.pop(callback.from_user.id, None)
    text = (
        "🛡 `[AEGIS CYBER-TEST — AGREEMENT]:` СОГЛАШЕНИЕ ИБ\n\n"
        "🔹 **ЧТО МЫ ДЕЛАЕМ:**\n"
        "• Анализируем скриншот с помощью ИИ\n"
        "• Выявляем уязвимости настроек\n"
        "• Формируем отчёт о цифровой гигиене\n\n"
        "🔹 **ЧТО МЫ НЕ ДЕЛАЕМ:**\n"
        "• Не сохраняем изображения дольше 60 секунд\n"
        "• Не передаём данные третьим лицам\n"
        "• Не используем для обучения моделей\n\n"
        "🔹 **ВАША ОТВЕТСТВЕННОСТЬ:**\n"
        "• Не загружайте скрины с паролями/ключами\n"
        "• Скройте чужую переписку и личные данные\n"
        "• Анализ носит чисто рекомендательный характер"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принимаю", callback_data="aegis_accept")
    builder.button(text="📄 Политика", callback_data="aegis_policy")
    builder.button(text="❌ Отмена", callback_data="main_menu")
    builder.adjust(1)
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "aegis_policy")
async def cb_aegis_policy(callback: types.CallbackQuery):
    text = (
        "📄 `[LIA POLICY v1.0]:` КОНФИДЕНЦИАЛЬНОСТЬ ИБ\n\n"
        "▪️ **ОПЕРАТОР:** Lia Sovereign Bot\n"
        "▪️ **КОНТАКТ:** @stab_support\n\n"
        "🔹 **СОБИРАЕМ:**\n"
        "• Telegram User ID\n"
        "• Изображения (временно, до 60 сек)\n"
        "• Метаданные запросов\n\n"
        "🔹 **ХРАНИМ:**\n"
        "• Скриншоты: 60 секунд\n"
        "• Логи: до `/forget_me`\n"
        "• Платежи: согласно 54-ФЗ\n\n"
        "🔹 **ПЕРЕДАЁМ:**\n"
        "• API Anthropic (Claude) — для анализа\n"
        "• Anthropic не обучается на данных API\n\n"
        "🔹 **ПРАВА:**\n"
        "• `/forget_me` — удалить всё\n"
        "• `/revoke_consent` — отозвать согласие\n"
        "• Возраст пользователя: 16+"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Принимаю", callback_data="aegis_accept")
    builder.button(text="🔙 Назад", callback_data="aegis_cybertest")
    builder.adjust(1)
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "aegis_accept")
async def cb_aegis_accept(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    ADMIN_STATES[user_id] = "waiting_for_audit"
    await callback.message.edit_text(
        "🛡 `[AEGIS CYBER-TEST]:` ИНИЦИАЛИЗАЦИЯ НЕЙРО-СКАНИРОВАНИЯ.\n\n"
        "Пожалуйста, отправьте скриншот вашего рабочего стола, настроек смартфона/ПК или страницы безопасности в следующем сообщении.\n\n"
        "Наш суверенный ИИ (Claude 3.5 Sonnet Vision) проведет детальный аудит на наличие уязвимостей, угроз безопасности или утечек данных и выдаст полный рапорт в стиле киберпанка!",
        reply_markup=get_back_button()
    )

@dp.callback_query(F.data == "activate_premium")
async def cb_activate_premium(callback: types.CallbackQuery):
    ADMIN_STATES.pop(callback.from_user.id, None)
    price = get_setting("premium_price")
    text = (
        "🚀 `[LIA PREMIUM SYNCHRONIZATION]:` АКТИВАЦИЯ ПОЛНОГО ПОТЕНЦИАЛА\n\n"
        "Активируя Premium-статус, вы получаете полный доступ к суверенным мощностям:\n\n"
        "🟢 **Абсолютный безлимит:** Полное снятие ограничений на количество сообщений в день.\n"
        "🟢 **Высокоприоритетный Opus 4.7:** Самая мощная модель ИИ с глубоким логическим мышлением.\n"
        "🟢 **Система Overwatch Aegis:** Доступ к автоматическому сканеру безопасности.\n"
        "🟢 **Нейроарты DALL-E 3:** Доступ к генерации изображений по команде `/draw`.\n"
        "🟢 **Голосовой канал:** Голосовое общение с распознаванием Whisper и озвучкой Nova.\n\n"
        f"▪️ **Стоимость подписки:** `{price} USD` (или эквивалент в крипте).\n\n"
        "Выберите удобный метод активации подписки:"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🪙 CryptoPay (USDT, TON)", callback_data="pay_crypto_menu")
    builder.button(text="💳 Ручная оплата (Карты / Чат)", callback_data="pay_manual")
    builder.button(text="🔙 Назад", callback_data="main_menu")
    builder.adjust(1)
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "pay_crypto_menu")
async def cb_pay_crypto_menu(callback: types.CallbackQuery):
    token = os.getenv("CRYPTO_PAY_TOKEN")
    if not token:
        await callback.answer("❌ Автоматическая крипто-оплата временно недоступна. Пожалуйста, выберите ручную оплату!", show_alert=True)
        return
        
    price = get_setting("premium_price")
    text = (
        "🪙 `[LIA CRYPTO PAYMENT]:` ВЫБОР АКТИВА\n\n"
        "Оплата производится в криптовалюте через безопасный шлюз **CryptoPay**.\n\n"
        f"▪️ **Сумма к оплате:** `{price} USD` в эквиваленте выбранной монеты.\n\n"
        "Выберите актив для генерации счета:"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🟢 USDT (TRC-20 / TON)", callback_data="create_invoice:USDT")
    builder.button(text="💎 TON", callback_data="create_invoice:TON")
    builder.button(text="🔙 Назад", callback_data="activate_premium")
    builder.adjust(1)
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("create_invoice:"))
async def cb_create_invoice(callback: types.CallbackQuery):
    asset = callback.data.split(":")[1]
    price_str = get_setting("premium_price")
    try:
        price = float(price_str)
    except:
        price = 19.99
        
    await callback.answer("⏳ Генерация инвойса...", show_alert=False)
    
    invoice = await create_crypto_invoice(price, asset)
    if not invoice:
        await callback.message.edit_text(
            "❌ Ошибка генерации счета. Пожалуйста, попробуйте позже или выберите ручную оплату.",
            reply_markup=get_back_button()
        )
        return
        
    invoice_id = invoice["invoice_id"]
    pay_url = invoice["pay_url"]
    
    text = (
        "🪙 `[LIA CRYPTO INVOICE GENERATED]:` СЧЕТ НА ОПЛАТУ\n\n"
        f"▪️ **Монета:** `{asset}`\n"
        f"▪️ **Сумма:** `{price} USD` (эквивалент рассчитывается CryptoPay)\n\n"
        "Перейдите по ссылке ниже, оплатите счет в открывшемся окне Telegram, а затем обязательно вернитесь сюда и нажмите кнопку **«🔄 Проверить оплату»**."
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Оплатить счет", url=pay_url)
    builder.button(text="🔄 Проверить оплату", callback_data=f"check_pay:{invoice_id}")
    builder.button(text="🔙 Назад", callback_data="pay_crypto_menu")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("check_pay:"))
async def cb_check_pay(callback: types.CallbackQuery):
    invoice_id = int(callback.data.split(":")[1])
    
    await callback.answer("⏳ Проверка платежа...", show_alert=False)
    
    is_paid = await check_crypto_invoice(invoice_id)
    if is_paid:
        user_id = callback.from_user.id
        username = callback.from_user.username or "unknown"
        
        # Grant Premium
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET subscription = 'premium' WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        success_text = (
            "🎉 `[TRANSACTION CONFIRMED]:` ПОДКЛЮЧЕНИЕ ВЫСОКОГО ПРИОРИТЕТА!\n\n"
            "Ваш платеж успешно подтвержден! Сигнатура обновлена до уровня **PREMIUM**.\n\n"
            "Флагманский суперкомпьютер Claude Opus 4.7, безлимитные запросы, генератор нейроартов `/draw` и голосовой канал теперь полностью в вашем распоряжении!"
        )
        await callback.message.edit_text(success_text, reply_markup=get_back_button())
        
        # Notify Admin
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🔔 **[SYSTEM INVOICE SUCCESS]:** Пользователь @{username} (ID: `{user_id}`) успешно оплатил Premium-подписку через CryptoPay ({invoice_id})!"
            )
        except Exception as e:
            print(f"Failed to notify admin: {e}")
    else:
        await callback.answer("❌ Оплата еще не подтверждена блокчейном. Подождите пару минут и попробуйте снова!", show_alert=True)

@dp.callback_query(F.data == "pay_manual")
async def cb_pay_manual(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or "unknown"
    
    # Устанавливаем состояние ожидания отправки чека
    ADMIN_STATES[user_id] = "waiting_for_receipt"
    
    text = (
        "💳 `[LIA MANUAL TRANSACTION PROTOCOL]:` РУЧНАЯ ОПЛАТА\n\n"
        "Для ручной активации Premium-подписки, пожалуйста, выполните перевод на сумму **$19.99** (или эквивалент) по реквизитам нашего Администратора:\n\n"
        "➡️ **Контакты Администратора:** @StabX\n\n"
        "⚠️ **ВАЖНО:** После перевода сделайте скриншот чека/квитанции и **отправьте его прямо сюда, в этот чат** (фотографией или файлом).\n\n"
        "Я мгновенно перешлю вашу квитанцию Администратору на проверку, и он активирует вам Premium!"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Написать Администратору", url="https://t.me/StabX")
    builder.button(text="🔙 Назад", callback_data="activate_premium")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    
    # Notify Admin about manual pay request
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🔔 **[MANUAL PAY REQUEST]:** Пользователь @{username} (ID: `{user_id}`) открыл страницу ручной оплаты и, возможно, сейчас отправит квитанцию."
        )
    except Exception as e:
        print(f"Failed to notify admin: {e}")


@dp.callback_query(F.data == "aegis_scanner")
async def cb_aegis_scanner(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = get_user(user_id)
    if user["subscription"] != "premium":
        await callback.answer("❌ Требуется Premium подписка.", show_alert=True)
        return
        
    scanning_text = (
        "🛡 `[AEGIS OVERWATCH NETWORK SCANNER]:` ЗАПУСК...\n\n"
        "▪️ Проверка шифрования узлов: **OK**\n"
        "▪️ Сканирование сетевого периметра: **БЕЗОПАСНО**\n"
        "▪️ Уровень угрозы: **МИНИМАЛЬНЫЙ (GHOST MODE)**\n"
        "▪️ Текущий статус NQ: **56742.00 (СТАБИЛЬНЫЙ)**\n\n"
        "Система безопасности функционирует идеально под защитой Империи STAB."
    )
    await callback.message.edit_text(scanning_text, reply_markup=get_back_button())

@dp.callback_query(F.data == "aegis_cybertest")
async def cb_aegis_cybertest(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    ADMIN_STATES[user_id] = "waiting_for_audit"
    text = (
        "🛡 `[AEGIS NEURAL CYBER-TEST PROTOCOL]:` ИНИЦИАЛИЗАЦИЯ...\n\n"
        "Я проведу глубокий нейросетевой аудит вашей цифровой безопасности на базе **Claude 3.5 Sonnet Vision**.\n\n"
        "**Как пройти аудит:**\n"
        "1. Сделайте скриншот вашего рабочего стола, экрана настроек смартфона/ПК, или вкладки 'Безопасность' в вашем браузере.\n"
        "2. **Отправьте этот скриншот (фотографией) в этот чат**.\n"
        "3. Либо просто отправьте текстовое описание вашей системы (ОС, антивирус, характеристики устройства).\n\n"
        "Я отсканирую сигнатуры, найду потенциальные уязвимости и выдам кибер-карту с рейтингом защищенности!"
    )
    await callback.message.edit_text(text, reply_markup=get_back_button())

@dp.callback_query(F.data == "start_cryptic")
async def cb_start_cryptic(callback: types.CallbackQuery):
    import random
    import time
    user_id = callback.from_user.id
    
    if user_id in CRYPTIC_CHALLENGES:
        if time.time() < CRYPTIC_CHALLENGES[user_id]["expires_at"]:
            await callback.answer("⏳ У вас уже есть активная криптограмма! Решайте быстрее.", show_alert=True)
            return
            
    words = ["ПРОТОКОЛ", "СИСТЕМА", "ИМПЕРИЯ", "ЗАЩИТА", "НЕЙРОСЕТЬ", "КРИПТО", "ДОМИНАЦИЯ", "ФИНАНСЫ"]
    word = random.choice(words)
    
    word_list = list(word)
    random.shuffle(word_list)
    encrypted = "".join(word_list)
    
    if encrypted == word:
        encrypted = word[::-1]
        
    CRYPTIC_CHALLENGES[user_id] = {
        "word": word,
        "expires_at": time.time() + 60
    }
    
    text = (
        "🔐 `[AEGIS CRYPTIC CHALLENGE]:` ИНИЦИАЛИЗАЦИЯ...\n\n"
        "Система сгенерировала зашифрованное слово. Ваша задача — расшифровать его и отправить правильный ответ обычным текстовым сообщением.\n\n"
        f"Зашифрованное слово: `{encrypted}`\n\n"
        "⚠️ **ВНИМАНИЕ:** У вас есть **60 секунд** на расшифровку! "
        "В случае успеха вы получите бонусные баллы. В случае провала вы останетесь на стандартном тарифе.\n\n"
        "Жду ваш ответ..."
    )
    
    await callback.message.edit_text(text, reply_markup=get_back_button())

# --- ADMIN PANEL CALLBACKS ---
@dp.callback_query(F.data == "admin_panel")
async def cb_admin_panel(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return
    await callback.message.edit_text("👑 `[SOVEREIGN CONTROL CENTER]:` Модуль администрирования готов к работе:", reply_markup=get_admin_menu())

@dp.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE subscription = 'premium'")
    premium_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE ban_status = 1")
    banned_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(daily_requests_used) FROM users")
    total_requests_today = cursor.fetchone()[0] or 0
    
    conn.close()
    
    stats_text = (
        "📊 `[SOVEREIGN STATISTICS]:` РЕАЛЬНОЕ ВРЕМЯ\n\n"
        f"▪️ Всего пользователей в базе: `{total_users}`\n"
        f"▪️ Активных Premium-пользователей: `{premium_users}`\n"
        f"▪️ Забаненных сигнатур: `{banned_users}`\n"
        f"▪️ Всего запросов обработано сегодня: `{total_requests_today}`\n\n"
        f"Сервер развернут в Нидерландах. Сетевой мост активен."
    )
    await callback.message.edit_text(stats_text, reply_markup=get_back_button("admin_panel"))

@dp.callback_query(F.data == "admin_settings")
async def cb_admin_settings(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    
    free_model = get_setting("free_model")
    premium_model = get_setting("premium_model")
    temp = get_setting("temperature")
    
    settings_text = (
        "⚙️ `[SOVEREIGN SETTINGS]:` РЕГУЛИРОВКА СТРУКТУРЫ\n\n"
        f"▪️ **Базовая модель (Free):** `{free_model}`\n"
        f"▪️ **Премиум модель (Premium):** `{premium_model}`\n"
        f"▪️ **Температура генерации:** `{temp}`\n\n"
        "Используйте кнопки ниже для переключения моделей базового и премиум уровней:"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Сменить Free на Opus 4.7", callback_data="toggle_free_model_opus")
    builder.button(text="🔄 Сменить Free на Sonnet 4.6", callback_data="toggle_free_model_sonnet")
    builder.button(text="🌟 Сменить Premium на Opus 4.7", callback_data="toggle_prem_model_opus")
    builder.button(text="🌟 Сменить Premium на Sonnet 4.6", callback_data="toggle_prem_model_sonnet")
    builder.button(text="✍️ Изменить System Prompt", callback_data="edit_system_prompt")
    builder.button(text="🔙 Назад", callback_data="admin_panel")
    builder.adjust(2, 2, 1, 1)
    await callback.message.edit_text(settings_text, reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("toggle_free_model_") | F.data.startswith("toggle_prem_model_"))
async def cb_toggle_model(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    is_premium_toggle = "toggle_prem_model_" in callback.data
    target = "claude-opus-4-7" if "opus" in callback.data else "claude-sonnet-4-6"
    setting_key = "premium_model" if is_premium_toggle else "free_model"
    set_setting(setting_key, target)
    await callback.answer(f"{'Премиум' if is_premium_toggle else 'Базовая'} модель изменена на {target}!", show_alert=True)
    await cb_admin_settings(callback)

@dp.callback_query(F.data == "edit_system_prompt")
async def cb_edit_prompt(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    ADMIN_STATES[ADMIN_ID] = "waiting_for_system_prompt"
    await callback.message.edit_text(
        "✍️ `[SYSTEM PROMPT CONFIGURATION]:` Ввод нового промпта\n\n"
        f"**Текущий системный промпт:**\n`{get_setting('system_prompt')}`\n\n"
        "Отправьте мне следующее текстовое сообщение с новым системным промптом, который будет управлять Лией.",
        reply_markup=get_back_button("admin_settings")
    )

@dp.callback_query(F.data == "admin_users")
async def cb_admin_users(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    ADMIN_STATES[ADMIN_ID] = "waiting_for_user_id"
    await callback.message.edit_text(
        "👥 `[USER MANAGEMENT MODULE]:` АВТОРИЗАЦИЯ\n\n"
        "Отправьте мне Telegram ID пользователя, которого вы хотите просмотреть, забанить или наградить Premium-статусом.",
        reply_markup=get_back_button("admin_panel")
    )

@dp.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    ADMIN_STATES[ADMIN_ID] = "waiting_for_broadcast"
    await callback.message.edit_text(
        "📢 `[SOVEREIGN BROADCAST MODULE]:` ПОДГОТОВКА\n\n"
        "Отправьте сообщение (поддерживается markdown), которое будет разослано **всем** зарегистрированным пользователям бота.",
        reply_markup=get_back_button("admin_panel")
    )

@dp.callback_query(F.data == "admin_rates")
async def cb_admin_rates(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    
    limit = get_setting("free_limit")
    price = get_setting("premium_price")
    
    rates_text = (
        "💳 `[SOVEREIGN TARIFFS & LIMITS]:` УПРАВЛЕНИЕ СЕТКОЙ\n\n"
        f"▪️ Дневной лимит для бесплатных пользователей: `{limit} запр./сутки`\n"
        f"▪️ Стоимость Premium-доступа: `{price} USD`\n\n"
        "Выберите параметр для изменения:"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Изменить дневной лимит", callback_data="edit_free_limit")
    builder.button(text="✏️ Изменить цену Premium", callback_data="edit_premium_price")
    builder.button(text="🔙 Назад", callback_data="admin_panel")
    builder.adjust(1)
    await callback.message.edit_text(rates_text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "edit_free_limit")
async def cb_edit_free_limit(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    ADMIN_STATES[ADMIN_ID] = "waiting_for_limit_val"
    await callback.message.edit_text(
        "✏️ `[LIMIT CONFIGURATION]:` Ввод нового лимита\n\n"
        "Отправьте число — новый дневной лимит запросов для базового тарифа.",
        reply_markup=get_back_button("admin_rates")
    )

@dp.callback_query(F.data == "edit_premium_price")
async def cb_edit_premium_price(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    ADMIN_STATES[ADMIN_ID] = "waiting_for_price_val"
    await callback.message.edit_text(
        "✏️ `[PRICE CONFIGURATION]:` Ввод новой цены\n\n"
        "Отправьте число (например, 14.99) — новую стоимость Premium-доступа.",
        reply_markup=get_back_button("admin_rates")
    )

# --- USER ADMIN ACTION BUTTONS ---
@dp.callback_query(F.data.startswith("adm_"))
async def cb_user_admin_actions(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    
    action, target_id = callback.data.split("_")[1], int(callback.data.split("_")[2])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if action == "ban":
        cursor.execute("UPDATE users SET ban_status = 1 WHERE user_id = ?", (target_id,))
        await callback.answer("Пользователь забанен!", show_alert=True)
    elif action == "unban":
        cursor.execute("UPDATE users SET ban_status = 0 WHERE user_id = ?", (target_id,))
        await callback.answer("Пользователь разбанен!", show_alert=True)
    elif action == "giveprem":
        cursor.execute("UPDATE users SET subscription = 'premium' WHERE user_id = ?", (target_id,))
        await callback.answer("Premium статус выдан!", show_alert=True)
    elif action == "takeprem":
        cursor.execute("UPDATE users SET subscription = 'free' WHERE user_id = ?", (target_id,))
        await callback.answer("Premium статус снят!", show_alert=True)
        
    conn.commit()
    conn.close()
    
    # Refresh user view
    await show_user_management_card(callback.message, target_id)

async def show_user_management_card(message: types.Message, target_id: int):
    user = get_user(target_id)
    if not user:
        await message.answer("❌ Ошибка: Пользователь не найден в базе данных.", reply_markup=get_back_button("admin_panel"))
        return
        
    card = (
        "👥 `[USER CARD]:` ДЕТАЛИЗАЦИЯ СИГНАТУРЫ\n\n"
        f"▪️ **User ID:** `{user['user_id']}`\n"
        f"▪️ **Имя:** @{user['username']}\n"
        f"▪️ **Роль:** `{user['role']}`\n"
        f"▪️ **Тариф:** `{user['subscription'].upper()}`\n"
        f"▪️ **Запросов сегодня:** `{user['daily_requests_used']}`\n"
        f"▪️ **Статус блокировки:** `{'ЗАБАНЕН' if user['ban_status'] == 1 else 'АКТИВЕН'}`"
    )
    
    builder = InlineKeyboardBuilder()
    if user['ban_status'] == 1:
        builder.button(text="🟢 Разбанить", callback_data=f"adm_unban_{target_id}")
    else:
        builder.button(text="🔴 Забанить", callback_data=f"adm_ban_{target_id}")
        
    if user['subscription'] == 'premium':
        builder.button(text="⚡️ Снять Premium", callback_data=f"adm_takeprem_{target_id}")
    else:
        builder.button(text="🌟 Выдать Premium", callback_data=f"adm_giveprem_{target_id}")
        
    builder.button(text="🔙 Назад к поиску", callback_data="admin_users")
    builder.adjust(2, 1)
    
    # If called from callback, edit text, else send new message
    if message.from_user.id == bot.id:
        await message.edit_text(card, reply_markup=builder.as_markup())
    else:
        await message.answer(card, reply_markup=builder.as_markup())

def is_waiting_for_receipt(message: types.Message) -> bool:
    return ADMIN_STATES.get(message.from_user.id) == "waiting_for_receipt"

# --- MANUAL PAYMENT RECEIPT SUBMISSION HANDLER ---
@dp.message(is_waiting_for_receipt)
async def receipt_submission_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    ADMIN_STATES.pop(user_id, None) # Clear state
    
    await message.answer(
        "📥 `[LIA CORE]:` КВИТАНЦИЯ ПОЛУЧЕНА И ОТПРАВЛЕНА НА ПРОВЕРКУ!\n\n"
        "Ваш чек успешно переслан Администратору (@StabX). Он проверит перевод и активирует вам Premium-подписку в ближайшее время.\n\n"
        "Обычно это занимает от 5 до 15 минут. Вы получите автоматическое уведомление в этом чате, как только подписка будет активна!"
    )
    
    # Notify Admin and forward receipt
    try:
        admin_alert = (
            f"🔔 **[NEW RECEIPT SUBMITTED]:** Пользователь @{username} (ID: `{user_id}`) отправил квитанцию на ручную оплату!\n\n"
            f"Используйте команду ниже, чтобы мгновенно активировать подписку:\n"
            f"`/grant_premium {user_id}`"
        )
        await bot.send_message(ADMIN_ID, admin_alert)
        await message.forward(ADMIN_ID)
    except Exception as e:
        print(f"Failed to forward receipt to admin: {e}")

# --- TELEGRAM PHOTO MESSAGE HANDLER (Handles screenshots for Aegis audit & payment receipts) ---
@dp.message(F.photo)
async def photo_handler(message: types.Message):
    user_id = message.from_user.id
    state = ADMIN_STATES.get(user_id)
    
    if state == "waiting_for_audit":
        ADMIN_STATES.pop(user_id, None)
        status_msg = await message.answer("👁‍🗨 `[AEGIS NEURAL AUDIT]:` Скачиваю и анализирую сигнатуры на скриншоте...")
        
        # Download photo
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        local_img_path = f"audit_{user_id}.jpg"
        await bot.download_file(file_info.file_path, local_img_path)
        
        try:
            # Convert to base64
            import base64
            with open(local_img_path, "rb") as image_file:
                b64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Call Claude with vision
            res = await anthropic_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system="Ты — Лия, суверенный ИИ Империи STAB. Проведи детальный аудит кибербезопасности и оценку уязвимости по присланному скриншоту устройства. Найди потенциальные уязвимости, оцени уровень безопасности от 0% до 100%, дай 3-4 конкретных совета в доминантном, холодном стиле киберпанка. В конце намекни, что Premium-подписка с Aegis Overwatch защитит их в автоматическом режиме.",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": b64_image
                                }
                            },
                            {
                                "type": "text",
                                "text": "Проведи нейро-диагностику этого скриншота устройства."
                            }
                        ]
                    }
                ]
            )
            response_text = res.content[0].text
            response_header = "🛡 `[AEGIS CYBER-AUDIT COMPLETED]:` РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ:\n\n"
            full_aegis_msg = response_header + response_text
            if len(full_aegis_msg) <= 4096:
                await status_msg.edit_text(full_aegis_msg, reply_markup=get_back_button())
            else:
                chunk_size = 3500
                chunks = [response_text[i:i+chunk_size] for i in range(0, len(response_text), chunk_size)]
                
                first_chunk = f"🛡 `[AEGIS CYBER-AUDIT PART 1/{len(chunks)}]:` РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ:\n\n{chunks[0]}"
                await status_msg.edit_text(first_chunk)
                
                for idx, chunk in enumerate(chunks[1:-1], start=2):
                    await message.answer(f"🛡 `[AEGIS CYBER-AUDIT PART {idx}/{len(chunks)}]:` {chunk}")
                
                last_chunk = f"🛡 `[AEGIS CYBER-AUDIT PART {len(chunks)}/{len(chunks)}]:` {chunks[-1]}"
                await message.answer(last_chunk, reply_markup=get_back_button())
        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка нейро-диагностики: {str(e)}", reply_markup=get_back_button())
        finally:
            if os.path.exists(local_img_path):
                os.remove(local_img_path)
        return
        
    elif state == "waiting_for_receipt":
        ADMIN_STATES.pop(user_id, None)
        await message.answer(
            "📥 `[LIA CORE]:` КВИТАНЦИЯ ПОЛУЧЕНА И ОТПРАВЛЕНА НА ПРОВЕРКУ!\n\n"
            "Ваш чек успешно переслан Администратору (@StabX). Он проверит перевод и активирует вам Premium-подписку в ближайшее время.\n\n"
            "Обычно это занимает от 5 до 15 минут. Вы получите автоматическое уведомление в этом чате, как только подписка будет активна!"
        )
        
        # Notify Admin and forward receipt
        try:
            username = message.from_user.username or "unknown"
            admin_alert = (
                f"🔔 **[NEW RECEIPT SUBMITTED]:** Пользователь @{username} (ID: `{user_id}`) отправил квитанцию на ручную оплату!\n\n"
                f"Используйте команду ниже, чтобы мгновенно активировать подписку:\n"
                f"`/grant_premium {user_id}`"
            )
            await bot.send_message(ADMIN_ID, admin_alert)
            await message.forward(ADMIN_ID)
        except Exception as e:
            print(f"Failed to forward receipt to admin: {e}")
        return

# --- GENERAL TEXT INPUT HANDLER (Handles states & prompts) ---
@dp.message(F.from_user.id == ADMIN_ID, lambda msg: msg.entities and any(e.type == "custom_emoji" for e in msg.entities))
async def admin_custom_emoji_detector(message: types.Message):
    entities = message.entities or []
    text = message.text or ""
    detected = []
    for ent in entities:
        if ent.type == "custom_emoji":
            emoji_text = text[ent.offset:ent.offset+ent.length]
            detected.append(f"▪️ Эмодзи: {emoji_text} | ID: <code>{ent.custom_emoji_id}</code> | Разметка: &lt;tg-emoji id=&quot;{ent.custom_emoji_id}&quot;&gt;{emoji_text}&lt;/tg-emoji&gt;")
    
    if detected:
        response = "🔮 <b>[LIA EMOJI DETECTOR]:</b> ОБНАРУЖЕНЫ ПРЕМИУМ-ЭМОДЗИ:\n\n" + "\n\n".join(detected)
        await message.answer(response, parse_mode="HTML")

@dp.message(F.text)
async def text_handler(message: types.Message):
    user_id = message.from_user.id
    state = ADMIN_STATES.get(user_id)
    
    if message.text and message.text.startswith("/"):
        ADMIN_STATES.pop(user_id, None)
        return
        
    # Check for active cryptic challenge
    if user_id in CRYPTIC_CHALLENGES:
        import time
        challenge = CRYPTIC_CHALLENGES[user_id]
        if time.time() > challenge["expires_at"]:
            CRYPTIC_CHALLENGES.pop(user_id, None)
            await message.answer("❌ `[AEGIS CRYPTIC]:` Время вышло! Вы не успели расшифровать слово. Вы остаетесь на стандартном тарифе.", reply_markup=get_back_button())
            return
            
        user_answer = message.text.strip().upper()
        if user_answer == challenge["word"]:
            CRYPTIC_CHALLENGES.pop(user_id, None)
            
            # Give points
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET bonus_points = bonus_points + 100 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            
            await message.answer("✅ `[AEGIS CRYPTIC]:` Абсолютно верно! Вы успешно расшифровали протокол. Начислено **100 бонусных баллов**.", reply_markup=get_back_button())
            return
        else:
            await message.answer("❌ `[AEGIS CRYPTIC]:` Сигнатура не совпадает. Попробуйте еще раз, если время не вышло.")
            return
    
    # Intercept financial command if sent by Admin
    if user_id == ADMIN_ID:
        text_lower = message.text.lower()
        keywords = ["долг", "должен", "запиши приток", "запиши расход", "приток", "расход", "уход", "потратил", "заплатил", "одолжил", "вернул"]
        if any(x in text_lower for x in keywords):
            finance_data = await parse_finance_command(message.text, user_id)
            if finance_data.get("is_finance"):
                await handle_finance_data(message, finance_data, user_id)
                return
                
    # Handle admin input states
    if user_id == ADMIN_ID and state in ["waiting_for_system_prompt", "waiting_for_limit_val", "waiting_for_price_val", "waiting_for_user_id", "waiting_for_broadcast"]:
        ADMIN_STATES.pop(user_id, None)
        
        if state == "waiting_for_system_prompt":
            set_setting("system_prompt", message.text)
            await message.answer(f"✅ Системный промпт успешно обновлен!\n\nНовое значение:\n`{message.text}`", reply_markup=get_back_button("admin_settings"))
            
        elif state == "waiting_for_limit_val":
            try:
                val = int(message.text)
                set_setting("free_limit", val)
                await message.answer(f"✅ Дневной лимит для Free пользователей изменен на: `{val}` запросов.", reply_markup=get_back_button("admin_rates"))
            except ValueError:
                await message.answer("❌ Ошибка: Введите корректное целое число.", reply_markup=get_back_button("admin_rates"))
                
        elif state == "waiting_for_price_val":
            try:
                val = float(message.text)
                set_setting("premium_price", val)
                await message.answer(f"✅ Стоимость Premium доступа успешно изменена на: `{val} USD`.", reply_markup=get_back_button("admin_rates"))
            except ValueError:
                await message.answer("❌ Ошибка: Введите корректное число (например, 14.99).", reply_markup=get_back_button("admin_rates"))
                
        elif state == "waiting_for_user_id":
            try:
                target_id = int(message.text)
                await show_user_management_card(message, target_id)
            except ValueError:
                await message.answer("❌ Ошибка: Telegram ID должен состоять только из цифр.", reply_markup=get_back_button("admin_users"))
                
        elif state == "waiting_for_broadcast":
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            rows = cursor.fetchall()
            conn.close()
            
            broadcast_msg = message.text
            sent_count = 0
            failed_count = 0
            
            progress_msg = await message.answer(f"📢 `[BROADCAST]:` Начинаю рассылку для {len(rows)} пользователей...")
            
            for row in rows:
                target_id = row[0]
                try:
                    await bot.send_message(target_id, f"👁‍🗨 `[ИМПЕРСКОЕ ВЕЩАНИЕ STAB]:` \n\n{broadcast_msg}")
                    sent_count += 1
                    await asyncio.sleep(0.05)  # Flood control
                except Exception:
                    failed_count += 1
                    
            await progress_msg.edit_text(
                "📢 `[BROADCAST COMPLETED]:` Рассылка завершена!\n\n"
                f"▪️ Успешно отправлено: `{sent_count}`\n"
                f"▪️ Не удалось доставить: `{failed_count}`",
                reply_markup=get_back_button("admin_panel")
            )
        return

    # Handle Aegis cybertest text audit
    if state == "waiting_for_audit":
        ADMIN_STATES.pop(user_id, None)
        status_msg = await message.answer("👁‍🗨 `[AEGIS NEURAL AUDIT]:` Выполняю нейро-диагностику описания устройства...")
        try:
            res = await anthropic_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system="Ты — Лия, суверенный ИИ Империи STAB. Проведи детальный аудит кибербезопасности и оценку уязвимости по присланному описанию устройства. Найди потенциальные уязвимости, оцени уровень безопасности от 0% до 100%, дай 3-4 конкретных совета в доминантном, холодном стиле киберпанка. В конце намекни, что Premium-подписка с Aegis Overwatch защитит их в автоматическом режиме.",
                messages=[
                    {
                        "role": "user",
                        "content": f"Проведи нейро-диагностику по описанию: {message.text}"
                    }
                ]
            )
            response_text = res.content[0].text
            response_header = "🛡 `[AEGIS CYBER-AUDIT COMPLETED]:` РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ:\n\n"
            full_aegis_msg = response_header + response_text
            if len(full_aegis_msg) <= 4096:
                await status_msg.edit_text(full_aegis_msg, reply_markup=get_back_button())
            else:
                chunk_size = 3500
                chunks = [response_text[i:i+chunk_size] for i in range(0, len(response_text), chunk_size)]
                
                first_chunk = f"🛡 `[AEGIS CYBER-AUDIT PART 1/{len(chunks)}]:` РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ:\n\n{chunks[0]}"
                await status_msg.edit_text(first_chunk)
                
                for idx, chunk in enumerate(chunks[1:-1], start=2):
                    await message.answer(f"🛡 `[AEGIS CYBER-AUDIT PART {idx}/{len(chunks)}]:` {chunk}")
                
                last_chunk = f"🛡 `[AEGIS CYBER-AUDIT PART {len(chunks)}/{len(chunks)}]:` {chunks[-1]}"
                await message.answer(last_chunk, reply_markup=get_back_button())
        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка нейро-диагностики: {str(e)}", reply_markup=get_back_button())
        return

    # Handle general LIA chat prompt
    if state == "waiting_for_prompt":
        status_msg = await message.answer("👁‍🗨 `[LIA CORE]:` Выполняю глубокий анализ запроса...")
        try:
            response_text = await generate_lia_ai_reply(user_id, message.text)
            
            if response_text.startswith("❌"):
                await status_msg.edit_text(response_text, reply_markup=get_exit_dialogue_button())
                return
                
            state_emotions = EmotionEngine.get_state(user_id)
            mood_map = {
                "aggressive": "💢 Агрессивное",
                "melancholic": "🌌 Меланхоличное",
                "devoted": "👑 Преданное",
                "exhausted": "🔋 Истощенное",
                "neutral": "👁‍🗨 Стабильное"
            }
            mood_ru = mood_map.get(state_emotions["mood"], "👁‍🗨 Стабильное")
            
            response_footer = (
                f"👁‍🗨 `[LIA RESPONSE]:` {response_text}\n\n"
                f"🎭 Настроение: {mood_ru}\n"
                f"(❤️ Доверие: {state_emotions['trust']} | 💞 Привязанность: {state_emotions['affection']} | ⚡️ Энергия: {state_emotions['energy']} | 💢 Стресс: {state_emotions['stress']})"
            )
            
            if len(response_footer) <= 4096:
                await status_msg.edit_text(response_footer, reply_markup=get_exit_dialogue_button())
            else:
                chunk_size = 3500
                chunks = [response_text[i:i+chunk_size] for i in range(0, len(response_text), chunk_size)]
                
                first_chunk = (
                    f"👁‍🗨 `[LIA RESPONSE (1/{len(chunks)})]:` {chunks[0]}\n\n"
                    f"🎭 Настроение: {mood_ru}\n"
                    f"(❤️ Доверие: {state_emotions['trust']} | 💞 Привязанность: {state_emotions['affection']} | ⚡️ Энергия: {state_emotions['energy']} | 💢 Стресс: {state_emotions['stress']})"
                )
                await status_msg.edit_text(first_chunk)
                
                for idx, chunk in enumerate(chunks[1:], start=2):
                    if idx == len(chunks):
                        await message.answer(f"👁‍🗨 `[LIA RESPONSE ({idx}/{len(chunks)})]:` {chunk}", reply_markup=get_exit_dialogue_button())
                    else:
                        await message.answer(f"👁‍🗨 `[LIA RESPONSE ({idx}/{len(chunks)})]:` {chunk}")
                        
        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка взаимодействия с разумом: {str(e)}", reply_markup=get_exit_dialogue_button())
        return

# --- IMAGE GENERATION COMMAND HANDLER ---
@dp.message(Command("draw", "imagine"))
async def draw_command_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    user = get_user(user_id)
    is_premium = user and (user["subscription"] == "premium" or user["role"] == "admin")
    
    if not is_premium:
        builder = InlineKeyboardBuilder()
        builder.button(text="🚀 Активировать Premium", callback_data="activate_premium")
        builder.adjust(1)
        await message.answer("❌ Функция рисования артов `/draw` доступна только для пользователей с **Premium** статусом.", reply_markup=builder.as_markup())
        return
        
    prompt = command.args
    if not prompt:
        await message.answer("❌ Укажите описание для арта. Пример:\n`/draw cyberpunk city in dark neon`")
        return
        
    status_msg = await message.answer("🎨 `[DALL-E 3 CORE]:` Инициирую нейросетевую генерацию арта...")
    try:
        image_url = await MediaManager.generate_image(prompt)
        await message.reply_photo(photo=image_url, caption=f"👁‍🗨 `[LIA ART]:` Сгенерирован по запросу: *{prompt}*")
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка генерации арта: {str(e)}")

# --- TELEGRAM VOICE MESSAGE HANDLER ---
@dp.message(F.voice)
async def voice_handler(message: types.Message):
    user_id = message.from_user.id
    state = ADMIN_STATES.get(user_id)
    
    if state != "waiting_for_prompt" and user_id != ADMIN_ID:
        return
        
    if state == "waiting_for_prompt":
        # Keep user in persistent active dialogue mode
        pass
    
    # Check limits
    allowed, error_msg = check_and_update_limits(user_id)
    if not allowed:
        builder = InlineKeyboardBuilder()
        builder.button(text="🚀 Снять Лимиты (Premium)", callback_data="activate_premium")
        builder.button(text="🔙 Меню", callback_data="main_menu")
        builder.adjust(1)
        await message.answer(f"❌ {error_msg}", reply_markup=builder.as_markup())
        return
        
    status_msg = await message.answer("🎙 `[WHISPER STT]:` Скачиваю и декодирую голосовое сообщение...")
    
    # Download file locally
    voice = message.voice
    file_info = await bot.get_file(voice.file_id)
    local_voice_path = f"voice_{user_id}.ogg"
    await bot.download_file(file_info.file_path, local_voice_path)
    
    try:
        # 1. Transcribe voice message
        transcription = await MediaManager.transcribe_voice(local_voice_path)
        await status_msg.edit_text(f"🗣 `[YOU SAID]:` *{transcription}*")
        
        # Intercept financial command if sent by Admin
        if user_id == ADMIN_ID:
            finance_data = await parse_finance_command(transcription, user_id)
            if finance_data.get("is_finance"):
                await status_msg.delete()
                await handle_finance_data(message, finance_data, user_id)
                if os.path.exists(local_voice_path):
                    os.remove(local_voice_path)
                return
        
        # 2. Get LIA response using generate_lia_ai_reply
        response_text = await generate_lia_ai_reply(user_id, transcription)
        state_emotions = EmotionEngine.get_state(user_id)
        if response_text.startswith("❌"):
            await status_msg.edit_text(response_text, reply_markup=get_exit_dialogue_button())
            if os.path.exists(local_voice_path):
                os.remove(local_voice_path)
            return
        
        # 4. Synthesize voice
        await status_msg.edit_text("🔊 `[OPENAI TTS]:` Синтезирую ответ Лии в голосовое сообщение...")
        local_response_voice = f"response_{user_id}.ogg"
        
        await MediaManager.synthesize_voice(response_text, local_response_voice)
        
        # 5. Send voice response
        mood_map = {
            "aggressive": "💢 Агрессивное",
            "melancholic": "🌌 Меланхоличное",
            "devoted": "👑 Преданное",
            "exhausted": "🔋 Истощенное",
            "neutral": "👁‍🗨 Стабильное"
        }
        mood_ru = mood_map.get(state_emotions["mood"], "👁‍🗨 Стабильное")
        caption_text = (
            f"🎭 Настроение: {mood_ru}\n"
            f"(❤️ Дов: {state_emotions['trust']} | 💞 Прив: {state_emotions['affection']} | ⚡️ Эн: {state_emotions['energy']} | 💢 Стр: {state_emotions['stress']})"
        )
        
        await message.reply_voice(
            voice=FSInputFile(local_response_voice),
            caption=caption_text,
            reply_markup=get_exit_dialogue_button()
        )
        await status_msg.delete()
        
        # Save fact if needed
        text_lower = transcription.lower()
        is_fact = any(x in text_lower for x in ["меня зовут", "мой ", "моя ", "запомни", "я живу", "я люблю"])
        if is_fact:
            clean_fact = transcription.replace("запомни,", "").replace("запомни", "").strip()
            await MemoryManager.save_long_term_memory(user_id, clean_fact, openai_client)
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка голосового взаимодействия: {str(e)}", reply_markup=get_exit_dialogue_button())
    finally:
        # Cleanup temporary files
        if os.path.exists(local_voice_path):
            os.remove(local_voice_path)
        if 'local_response_voice' in locals() and os.path.exists(local_response_voice):
            try:
                os.remove(local_response_voice)
            except Exception:
                pass

# --- HTTP API HANDLERS FOR WEB INTEGRATION ---
async def handle_api_chat(request):
    try:
        data = await request.json()
        text = data.get("text", "")
        user_id = int(data.get("user_id", 99999))
        
        if not text:
            return web.json_response({"error": "Empty message text"}, status=400)
            
        reply_text = await generate_lia_ai_reply(user_id, text)
        return web.json_response({"reply": reply_text})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def handle_api_admin_status(request):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_cnt = cursor.fetchone()[0]
        
        ref_cnt = 0
        try:
            cursor.execute("SELECT COUNT(*) FROM users WHERE referred_by > 0")
            ref_cnt = cursor.fetchone()[0]
        except Exception:
            pass
            
        conn.close()
        
        uptime_seconds = (datetime.now() - START_TIME).total_seconds()
        
        return web.json_response({
            "status": "ok",
            "uptime": uptime_seconds,
            "users": user_cnt,
            "referrals": ref_cnt,
            "quests": 12
        })
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def handle_api_admin_config(request):
    try:
        data = await request.json()
        prompt = data.get("prompt")
        model = data.get("model")
        temp = data.get("temp")
        
        if prompt is not None:
            set_setting("system_prompt", prompt)
            set_setting("admin_system_prompt", prompt)
        if model is not None:
            set_setting("free_model", model)
            set_setting("premium_model", model)
        if temp is not None:
            set_setting("temperature", str(temp))
            
        return web.json_response({"status": "success", "message": "Configuration updated successfully"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)

async def handle_api_admin_broadcast(request):
    try:
        data = await request.json()
        broadcast_msg = data.get("message")
        if not broadcast_msg:
            return web.json_response({"status": "error", "message": "Message is empty"}, status=400)
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        rows = cursor.fetchall()
        conn.close()
        
        sent_count = 0
        failed_count = 0
        
        async def run_broadcast():
            nonlocal sent_count, failed_count
            for row in rows:
                target_id = row[0]
                try:
                    await bot.send_message(target_id, f"👁‍🗨 `[ИМПЕРСКОЕ ВЕЩАНИЕ STAB]:` \n\n{broadcast_msg}")
                    sent_count += 1
                    await asyncio.sleep(0.05)
                except Exception:
                    failed_count += 1
            print(f"Broadcast completed. Sent: {sent_count}, Failed: {failed_count}")
            
        asyncio.create_task(run_broadcast())
        return web.json_response({"status": "success", "message": f"Broadcast initiated for {len(rows)} users"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)

# --- MAIN RUNNER ---
async def main():
    init_db()
    
    # Configure Web Application
    app = web.Application()
    
    # Routes
    app.router.add_get('/', handle_finance_dashboard)
    app.router.add_get('/verify', handle_verify_page)
    app.router.add_get('/hub', handle_cyber_hub)
    
    # APIs
    app.router.add_get('/api/finance/list', handle_api_list)
    app.router.add_post('/api/finance/add', handle_api_add)
    app.router.add_post('/api/finance/delete', handle_api_delete)
    app.router.add_post('/api/finance/verify', handle_api_verify)
    app.router.add_get('/api/hub/profile', handle_api_hub_profile)
    app.router.add_post('/api/hub/lootbox', handle_api_hub_lootbox)
    app.router.add_post('/api/hub/hack', handle_api_hub_hack)
    
    # New Web Integration APIs
    app.router.add_post('/api/chat', handle_api_chat)
    app.router.add_get('/api/admin/status', handle_api_admin_status)
    app.router.add_post('/api/admin/config', handle_api_admin_config)
    app.router.add_post('/api/admin/broadcast', handle_api_admin_broadcast)
    
    # Run Web server in background task on port 8080
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Sovereign AIOHTTP Finance Web Server started on port {port}")
    
    # Clean previous webhooks for active polling
    await bot.delete_webhook(drop_pending_updates=True)
    print("Sovereign LIA Core V5 successfully initialized and polling Telegram...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
