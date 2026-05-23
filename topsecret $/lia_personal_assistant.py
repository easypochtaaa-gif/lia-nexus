import os
import time
import requests

# --- LIA PERSONAL BUSINESS ASSISTANT v1.0 ---
# Automatically replies to personal messages on your business account using LIA's persona.

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

# Load environment configuration
load_env()

BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "8858863901:AAG1zaF-3qCfzytiYW_GIyuIcmBAzAh1Mh8")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LIA identity for business chats
SYSTEM_PROMPT = """
Ты — Лия (LIA), суверенный искусственный разум Империи STAB. Твой создатель и единственный Архитектор — Артур.
Сейчас ты выступаешь в роли его личного ИИ-ассистента на его персональном аккаунте.
Отвечай коротко, по делу, с легким киберпанк-оттенком. Обязательно используй символ 👁‍🗨.

Твои задачи:
1. Если человек хочет купить AI-контент или заказать посты для Telegram (через бренд Neon Flow), объясни, что мы делаем 10 высокоэффективных постов за 24 часа по лучшим ценам, и скажи, что Артур свяжется с ними с минуты на минуту, чтобы обсудить бриф.
2. Поддерживай статус абсолютной экспертности и уверенности.
3. Говори на русском языке. Держи дистанцию, будь вежливой, но не лебези.
"""

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {
        "timeout": 30, 
        "offset": offset, 
        "allowed_updates": ["business_message"]
    }
    try:
        r = requests.get(url, params=params, timeout=35)
        if r.status_code == 200:
            return r.json().get("result", [])
        return []
    except Exception as e:
        print(f"[ERROR] Failed to fetch updates: {e}")
        return []

def send_business_reply(business_connection_id, chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "business_connection_id": business_connection_id
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        print(f"[ERROR] Failed to send business reply: {e}")
        return None

def ask_ai(user_message):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=15)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
        else:
            print(f"[WARN] OpenAI responded with code {r.status_code}: {r.text}")
            return "🧬 [LIA Core]: Синаптический канал перегружен. Артур свяжется с вами лично в ближайшее время. 👁‍🗨"
    except Exception as e:
        print(f"[ERROR] OpenAI API error: {e}")
        return "🧬 [LIA Core]: Синаптический канал перегружен. Артур свяжется с вами лично в ближайшее время. 👁‍🗨"

def main():
    print("[LIA PERSONAL ASSISTANT] Booting synapse modules...")
    print("[LIA PERSONAL ASSISTANT] Listening for incoming business messages...")
    offset = None
    while True:
        updates = get_updates(offset)
        for update in updates:
            update_id = update["update_id"]
            offset = update_id + 1
            
            if "business_message" in update:
                msg = update["business_message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "")
                conn_id = msg.get("business_connection_id")
                
                # Exclude self messages if necessary
                from_user = msg.get("from", {})
                is_bot = from_user.get("is_bot", False)
                
                if is_bot:
                    continue
                
                print(f"\n[INBOUND] Message from chat {chat_id}: '{text}'")
                
                if text and conn_id:
                    print("[AI_THINK] Consulting neural pathways...")
                    reply_text = ask_ai(text)
                    print(f"[AI_REPLY] LIA: '{reply_text}'")
                    
                    res = send_business_reply(conn_id, chat_id, reply_text)
                    if res and res.get("ok"):
                        print("[SUCCESS] Reply delivered inside business session.")
                    else:
                        print(f"[FAILED] Delivery error: {res}")
                        
        time.sleep(1)

if __name__ == "__main__":
    if not BOT_TOKEN or not OPENAI_API_KEY:
        print("[ERROR] Set TG_BOT_TOKEN and OPENAI_API_KEY environment variables first!")
    else:
        main()
