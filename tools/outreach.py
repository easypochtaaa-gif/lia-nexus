#!/usr/bin/env python3
"""LIA OUTREACH ENGINE — Generates personalized campaigns for all 29 leads"""
import os, json, datetime

REPORT = "/root/lia_core/agents/reports"
OUTREACH = "/root/lia_core/agents/outreach"
os.makedirs(f"{OUTREACH}/emails", exist_ok=True)
os.makedirs(f"{OUTREACH}/telegram", exist_ok=True)

# Load leads
with open(f"{REPORT}/leads_full.json") as f:
    data = json.load(f)
    leads = data["leads"]

print("=" * 70)
print("  LIA OUTREACH ENGINE // Campaign Generation")
print("  Leads: " + str(len(leads)) + " | Sectors: " + str(data["sectors"]))
print("=" * 70)

# Sector-specific pitches
PITCHES = {
    "Legal": {
        "subject": "AI-автоматизація документообігу для {domain}",
        "pain": "юристи витрачають 60% часу на типові документи",
        "solution": "AI генерує 90% документів за 2 хвилини",
        "benefit": "Фірма може взяти +40% клієнтів без нових наймів",
        "services": ["AI-генерація договорів та позовів", "Аналіз контрактів на ризики", "Чатбот для первинних консультацій"]
    },
    "Medical": {
        "subject": "AI для {domain} — автоматичний запис, нагадування, аналітика",
        "pain": "адміністратори перевантажені дзвінками та записами",
        "solution": "AI-бот записує пацієнтів 24/7, нагадує про прийом",
        "benefit": "Скорочення неявок на 40%, економія на call-центрі",
        "services": ["AI-запис на прийом через Telegram/Viber", "Автоматичні нагадування пацієнтам", "Аналітика завантаженості лікарів"]
    },
    "E-commerce": {
        "subject": "AI-чатбот для {domain} — +35% конверсії за 2 тижні",
        "pain": "клієнти йдуть, бо не отримують миттєву відповідь",
        "solution": "AI-бот відповідає за 3 секунди, знає весь каталог",
        "benefit": "+35% конверсії, -50% навантаження на підтримку",
        "services": ["AI-консультант з каталогом товарів", "Автоматична обробка замовлень", "Предиктивна аналітика попиту"]
    },
    "RealEstate": {
        "subject": "AI для {domain} — кваліфікація лідів та оцінка об'єктів",
        "pain": "агенти витрачають час на нецільових клієнтів",
        "solution": "AI кваліфікує ліди автоматично, передає тільки гарячих",
        "benefit": "+50% конверсії, агенти працюють тільки з готовими покупцями",
        "services": ["AI-кваліфікація лідів", "Автоматична оцінка об'єктів", "Персоналізовані розсилки"]
    },
    "Fintech": {
        "subject": "AI fraud detection та автоматизація для {domain}",
        "pain": "ручна перевірка транзакцій не встигає за обсягами",
        "solution": "AI аналізує транзакції в реальному часі",
        "benefit": "Виявлення шахрайства за мілісекунди, -80% ручної роботи",
        "services": ["AI fraud detection", "Автоматичний risk scoring", "AI-підтримка клієнтів"]
    },
    "Education": {
        "subject": "AI-асистент для {domain} — персоналізоване навчання",
        "pain": "один формат для всіх студентів знижує ефективність",
        "solution": "AI адаптує контент під кожного студента",
        "benefit": "+60% завершення курсів, автоматична перевірка завдань",
        "services": ["AI-тьютор для студентів", "Автоматична перевірка завдань", "Аналітика прогресу"]
    },
    "HoReCa": {
        "subject": "AI-автоматизація для {domain} — замовлення, логістика, прогнози",
        "pain": "піковий час = хаос в замовленнях та доставці",
        "solution": "AI прогнозує навантаження та оптимізує маршрути",
        "benefit": "-30% часу доставки, +20% задоволеності клієнтів",
        "services": ["AI-прогноз попиту", "Оптимізація маршрутів доставки", "Чатбот для замовлень"]
    }
}

EMAIL_TEMPLATE = """Добрий день!

Мене звати StabX, я представляю AI-агентство StabX Digital.

Знаю, що {pain}. Ми вирішуємо цю проблему:

{solution}.

Що ми пропонуємо для {domain}:
{services_list}

Результат: {benefit}.

Готовий провести безкоштовний 20-хвилинний аудит ваших процесів — покажу конкретно, де AI зекономить вам гроші та час.

Коли вам зручно поговорити?

З повагою,
StabX Digital
Telegram: @stabxdigital
Web: stabx.digital"""

# Generate campaigns
campaigns = []
total_emails = 0

for lead in leads:
    sector = lead["sector"]
    domain = lead["domain"]
    pitch = PITCHES.get(sector, PITCHES["E-commerce"])
    
    services_list = "\n".join(f"  * {s}" for s in pitch["services"])
    
    email = {
        "to": f"info@{domain}",
        "subject": pitch["subject"].format(domain=domain),
        "body": EMAIL_TEMPLATE.format(
            pain=pitch["pain"],
            solution=pitch["solution"],
            domain=domain,
            services_list=services_list,
            benefit=pitch["benefit"]
        ),
        "sector": sector,
        "domain": domain,
        "ip": lead["ip"],
        "status": "DRAFT",
        "created": datetime.datetime.now().isoformat()
    }
    
    campaigns.append(email)
    total_emails += 1
    
    # Save individual email
    safe_name = domain.replace(".", "_")
    with open(f"{OUTREACH}/emails/{safe_name}.json", "w") as f:
        json.dump(email, f, indent=2, ensure_ascii=False)

# Save master campaign file
master = {
    "campaign": "StabX Digital — AI Consulting Launch",
    "created": datetime.datetime.now().isoformat(),
    "total_emails": total_emails,
    "sectors": list(set(l["sector"] for l in leads)),
    "emails": campaigns
}

with open(f"{OUTREACH}/campaign_master.json", "w") as f:
    json.dump(master, f, indent=2, ensure_ascii=False)

# Generate Telegram posts per sector
tg_posts = []
for sector, pitch in PITCHES.items():
    post = f"""🤖 AI-автоматизація для сфери: {sector}

Проблема: {pitch['pain']}
Рішення: {pitch['solution']}

Що ви отримаєте:
{"".join(chr(10)+"  ✅ "+s for s in pitch['services'])}

📊 Результат: {pitch['benefit']}

🔗 Безкоштовний аудит: @stabxdigital

#AI #автоматизація #{sector.lower().replace(' ','')} #бізнес #Україна"""
    
    tg_posts.append({"sector": sector, "text": post})
    with open(f"{OUTREACH}/telegram/{sector.lower()}.txt", "w") as f:
        f.write(post)

with open(f"{OUTREACH}/telegram_posts.json", "w") as f:
    json.dump(tg_posts, f, indent=2, ensure_ascii=False)

# Print results
print("\n" + "-" * 70)
print("  CAMPAIGN GENERATION RESULTS")
print("-" * 70)

by_sector = {}
for c in campaigns:
    by_sector.setdefault(c["sector"], []).append(c)

for sector, emails in by_sector.items():
    print(f"\n  [{sector}] — {len(emails)} emails generated:")
    for e in emails:
        print(f"    To: {e['to']:35s} | Subject: {e['subject'][:45]}...")

print(f"\n" + "-" * 70)
print(f"  TELEGRAM POSTS: {len(tg_posts)} sector-specific posts")
print("-" * 70)
for p in tg_posts:
    print(f"  [{p['sector']:12s}] Post ready ({len(p['text'])} chars)")

# Summary
print(f"\n" + "=" * 70)
print("  OUTREACH ENGINE // CAMPAIGN READY")
print("=" * 70)
print(f"  Total emails:     {total_emails}")
print(f"  Telegram posts:   {len(tg_posts)}")
print(f"  Sectors covered:  {len(by_sector)}")
print(f"  Status:           ALL DRAFTS GENERATED")
print(f"  Location:         /root/lia_core/agents/outreach/")
print("=" * 70)
print("  Files:")
print("    /outreach/campaign_master.json  — all emails")
print("    /outreach/emails/*.json         — individual drafts")
print("    /outreach/telegram_posts.json   — TG content")
print("    /outreach/telegram/*.txt        — individual posts")
print("=" * 70)
