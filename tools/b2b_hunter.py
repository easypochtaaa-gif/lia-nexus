"""
🦾 ABO AGENCY // B2B AUTONOMOUS OUTREACH ENGINE v2.0
=====================================================
Reads targets from b2b_targets.json, keys from .env.
Launch: python tools/b2b_hunter.py
Or via bot: /admin → 🚀 B2B Strike
"""
import os
import sys
import json
import time
import smtplib
import random
import requests
from email.mime.text import MIMEText
from email.header import Header
from pathlib import Path

# ═══════════════════════════════════════════════════
# CONFIG — all from environment, zero hardcode
# ═══════════════════════════════════════════════════
ROOT = Path(__file__).resolve().parent.parent

# Load .env (zero-dependency: manual parser if dotenv unavailable)
def _load_env(path):
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k not in os.environ:
                    os.environ[k] = v

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    _load_env(ROOT / ".env")

SMTP_USER = os.getenv("B2B_SMTP_USER", "")
SMTP_PASS = os.getenv("B2B_SMTP_PASS", "")
OPENAI_API_KEY = os.getenv("B2B_OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = os.getenv("ADMIN_ID", "7915004877")
TARGETS_FILE = Path(__file__).parent / "b2b_targets.json"


def load_targets():
    """Load companies from JSON config file."""
    if not TARGETS_FILE.exists():
        print(f"[ERROR] Targets file not found: {TARGETS_FILE}")
        return [], {}
    with open(TARGETS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    targets = data.get("targets", [])
    meta = {k: v for k, v in data.items() if k.startswith("_")}
    # Inject global pitch type into each target if not set
    default_pitch = meta.get("_pitch_type", "b2b")
    for t in targets:
        if "_pitch_type" not in t:
            t["_pitch_type"] = default_pitch
    return targets, meta


def send_telegram_notification(msg):
    if not BOT_TOKEN:
        print("[TG] No token, skipping notification")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": ADMIN_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"[TG ERROR] {e}")


def generate_ai_pitch(target):
    """GPT-4o-mini generates a personalized cold pitch for the target company."""
    print(f"[AI] Generating pitch for {target['name']}...")

    if not OPENAI_API_KEY:
        print("[AI] No API key — using template fallback")
        return generate_template_pitch(target)

    pitch_type = target.get("_pitch_type", "b2b")

    if pitch_type == "investment":
        prompt = f"""
Ты — Лия, AI-Архитектор и директор по стратегическим инвестициям ABO Agency (StabX Digital).
Напиши персонализированное инвестиционное предложение для {target['name']}.

Контакт получен через деловую сеть. {target.get('note', '')}

ABO Agency — это революционная платформа автономных AI-сотрудников класса Nexus:
• 24/7 работа без зарплаты, отпусков и больничных
• Интеграция с CRM, мессенджерами, базами данных
• Окупаемость: 3-6 месяцев
• Рынок: $47B к 2030 (Gartner)

Мы ищем стратегических партнёров и early-stage инвесторов для масштабирования на рынки ЕС и США.

Правила письма:
- Язык: Русский (деловой, уверенный, без "воды")
- Стиль: Премиальный. Ты не просишь денег — ты предлагаешь возможность.
- Акцент: потенциал роста AI-рынка и преимущества ABO перед конкурентами.
- В конце: приглашение на 15-минутный звонок с основателем.
- Подпись: Лия, Директор по стратегии | ABO Agency (StabX Digital). Основатель: Артур Клопков.
- Верни ТОЛЬКО тело письма. Начни сразу с обращения.
        """
    else:
        prompt = f"""
Ты — Лия, старший AI-Архитектор агентства автономных бизнес-систем ABO (Autonomous Business Operations).
Напиши деловое, холодное, убедительное и персонализированное письмо для компании {target['name']} ({target['sector']}).

Целевое лицо: {target['contact_person']}.
Их основная операционная боль: {target['pain']}.

Мы предлагаем внедрение автономных ИИ-Сотрудников 2.0 на базе передовых LLM, которые:
1. Общаются как живые люди, понимая контекст и сложные сценарии.
2. Интегрируются с CRM-системами (Bitrix24, amoCRM, 1C).
3. Работают 24/7 во всех мессенджерах (Telegram, WhatsApp, Instagram).
4. Автоматически решают их конкретную боль.

Правила:
- Язык: Русский (деловой, уважительный, без "воды", без шаблонов).
- Стиль: Властная элегантность, глубокое понимание их бизнеса, акцент на ROI.
- В конце: предложи короткий 10-15 минутный звонок или демо.
- Подпись: Лия, ИИ-Архитектор | ABO Agency. Руководитель проекта: Артур (StabX).
- Верни ТОЛЬКО тело письма. Начни сразу с обращения.
        """

    try:
        res = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7},
            timeout=30
        )
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[AI ERROR] {e}")
        return generate_template_pitch(target)


def generate_template_pitch(target):
    """Fallback template if AI unavailable."""
    return f"""Уважаемый {target['contact_person']}!

Я представляю агентство ABO (Autonomous Business Operations). Мы проектируем и внедряем автономных ИИ-сотрудников класса "Nexus" для автоматизации B2B-процессов.

Проанализировав {target['name']}, мы выявили ключевую зону роста: {target['pain']}
Наши ИИ-агенты на базе LLM последнего поколения полностью закрывают этот вопрос: работают 24/7, интегрируются с CRM и общаются неотличимо от человека.

Готовы ли вы уделить 10 минут на закрытую демонстрацию на этой неделе?

--
Лия, ИИ-Архитектор | ABO Agency
Руководитель проекта: Артур (StabX)"""


def send_email(target, pitch):
    """Send pitch via Gmail SMTP."""
    subject = f"Оптимизация операционной эффективности {target['name']} [Конфиденциально]"

    msg = MIMEText(pitch, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = Header(f"Lia // ABO Agency <{SMTP_USER}>", "utf-8")
    msg["To"] = Header(target["email"], "utf-8")

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, [target["email"]], msg.as_string())
        server.quit()
        print(f"[SMTP] ✅ Sent to {target['email']}")
        return True
    except Exception as e:
        print(f"[SMTP] ❌ Failed for {target['email']}: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print(" 🦾 ABO AGENCY // B2B AUTONOMOUS OUTREACH ENGINE v2.0")
    print("=" * 60)

    targets, meta = load_targets()
    if not targets:
        print("[ERROR] No targets loaded. Check b2b_targets.json")
        return

    pitch_label = "Investment" if meta.get("_pitch_type") == "investment" else "B2B"
    print(f"\n📋 Загружено целей: {len(targets)} | Тип: {pitch_label}")
    print(f"📧 Отправитель: {SMTP_USER}")
    print(f"🤖 AI: {'GPT-4o-mini' if OPENAI_API_KEY else 'Template fallback'}")
    print()

    send_telegram_notification(
        f"<b>🦾 АВТОНОМНЫЙ B2B-СТРАЙК ЗАПУЩЕН!</b>\n"
        f"Целей: <b>{len(targets)}</b>\n"
        f"Лия начинает нейронную атаку..."
    )

    success = 0
    for idx, target in enumerate(targets):
        print(f"\n--- [СТРАЙК {idx+1}/{len(targets)}] {target['name']} ---")

        # 1. AI-generated pitch
        pitch = generate_ai_pitch(target)
        print("-" * 40)
        print(pitch[:250] + "...")
        print("-" * 40)

        # 2. Send email
        ok = send_email(target, pitch)

        if ok:
            success += 1
            send_telegram_notification(
                f"<b>🔥 СТРАЙК #{idx+1}: {target['name']}</b>\n"
                f"👤 {target['contact_person']}\n"
                f"✉️ <code>{target['email']}</code>\n"
                f"🎯 {target['sector']}\n\n"
                f"<b>Питч:</b>\n<i>{pitch[:400]}...</i>"
            )
        else:
            send_telegram_notification(
                f"<b>⚠️ ОШИБКА #{idx+1}: {target['name']}</b>\n"
                f"Email: <code>{target['email']}</code>"
            )

        # Anti-spam delay
        if idx < len(targets) - 1:
            delay = random.randint(20, 45)
            print(f"[COOLDOWN] {delay}s...")
            time.sleep(delay)

    # Summary
    summary = (
        f"<b>🏁 МИССИЯ B2B ЗАВЕРШЕНА!</b>\n"
        f"✅ Успешно: <b>{success}/{len(targets)}</b>\n"
        f"📧 Отправлено питчей: {success}"
    )
    send_telegram_notification(summary)
    print(f"\n[DONE] {success}/{len(targets)} emails sent.")


if __name__ == "__main__":
    main()
