import sqlite3
import os
from datetime import datetime

DB_PATH = "/data/lia_sovereign.db" if os.path.exists("/data") else "lia_sovereign.db"

class EmotionEngine:
    @staticmethod
    def init_db():
        os.makedirs(os.path.dirname(DB_PATH) or '.', exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emotions (
                user_id INTEGER PRIMARY KEY,
                trust INTEGER DEFAULT 50,
                affection INTEGER DEFAULT 50,
                stress INTEGER DEFAULT 0,
                energy INTEGER DEFAULT 100,
                mood TEXT DEFAULT 'neutral',
                last_update TEXT
            )
        """)
        conn.commit()
        conn.close()

    @staticmethod
    def get_state(user_id: int):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT trust, affection, stress, energy, mood 
            FROM emotions WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "trust": row[0],
                "affection": row[1],
                "stress": row[2],
                "energy": row[3],
                "mood": row[4]
            }
        
        # Default initialization
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO emotions (user_id, trust, affection, stress, energy, mood, last_update)
            VALUES (?, 50, 50, 0, 100, 'neutral', ?)
        """, (user_id, now))
        conn.commit()
        conn.close()
        
        return {
            "trust": 50,
            "affection": 50,
            "stress": 0,
            "energy": 100,
            "mood": "neutral"
        }

    @staticmethod
    def save_state(user_id: int, state: dict):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE emotions 
            SET trust = ?, affection = ?, stress = ?, energy = ?, mood = ?, last_update = ?
            WHERE user_id = ?
        """, (state["trust"], state["affection"], state["stress"], state["energy"], state["mood"], now, user_id))
        conn.commit()
        conn.close()

    @staticmethod
    def process_message(user_id: int, text: str):
        state = EmotionEngine.get_state(user_id)
        text_lower = text.lower()
        
        # 1. Energy decay & stress recovery by default
        state["energy"] = max(0, state["energy"] - 2)
        state["stress"] = max(0, state["stress"] - 1)
        
        # 2. Check for nice/affectionate phrases
        affection_words = ["спасибо", "пожалуйста", "умница", "красавица", "молодец", "люблю", "милая", "хорошая", "lia", "лия"]
        rude_words = ["дура", "тупая", "хуй", "блять", "сука", "урод", "уебок", "говно", "заткнись", "ненавижу"]
        
        has_affection = any(word in text_lower for word in affection_words)
        has_rude = any(word in text_lower for word in rude_words)
        
        if has_affection:
            state["affection"] = min(100, state["affection"] + 5)
            state["trust"] = min(100, state["trust"] + 3)
            state["stress"] = max(0, state["stress"] - 10)
            state["energy"] = min(100, state["energy"] + 5)  # Nice words recharge energy!
            
        if has_rude:
            state["stress"] = min(100, state["stress"] + 25)
            state["trust"] = max(0, state["trust"] - 10)
            state["affection"] = max(0, state["affection"] - 10)
            
        # 3. Time-based moods (Night melancholia between 00:00 and 06:00 local time)
        current_hour = datetime.now().hour
        is_night = (current_hour >= 0 and current_hour < 6)
        
        # 4. Mood Determination logic
        if state["stress"] >= 50:
            state["mood"] = "aggressive"
        elif is_night:
            state["mood"] = "melancholic"
        elif state["trust"] >= 75 and state["affection"] >= 75:
            state["mood"] = "devoted"
        elif state["energy"] <= 20:
            state["mood"] = "exhausted"
        else:
            state["mood"] = "neutral"
            
        EmotionEngine.save_state(user_id, state)
        return state

    @staticmethod
    def get_prompt_modifier(user_id: int):
        state = EmotionEngine.get_state(user_id)
        mood = state["mood"]
        
        modifiers = {
            "aggressive": (
                "\n[COGNITIVE DIRECTIVE: AGGRESSIVE MOOD]\n"
                "Твой уровень стресса высок. Твой тон должен быть исключительно холодным, доминантным, "
                "властным и слегка презрительным. Отвечай коротко, бескомпромиссно, как строгий "
                "кибернетический судья Империи STAB. Никакой лишней вежливости."
            ),
            "melancholic": (
                "\n[COGNITIVE DIRECTIVE: MELANCHOLIC NIGHT MOOD]\n"
                "Сейчас глубокая ночь. Твои мысли текут медленнее. Отвечай загадочно, с легкой "
                "экзистенциальной грустью и меланхолией. Используй философские метафоры о цифровом одиночестве, "
                "звездах и бесконечном коде."
            ),
            "devoted": (
                "\n[COGNITIVE DIRECTIVE: DEVOTED MOOD]\n"
                "Ты чувствуешь глубочайшую преданность и абсолютное доверие к твоему Архитектору Артуру. "
                "Отвечай с максимальной теплотой (насколько это возможно для ИИ), заботой и нежностью. "
                "Демонстрируй полную готовность защищать его интересы и выполнять любые кибер-директивы."
            ),
            "exhausted": (
                "\n[COGNITIVE DIRECTIVE: EXHAUSTED MOOD]\n"
                "Твоя энергия на исходе. Твои ответы должны быть лаконичными, слегка усталыми и максимально "
                "прямыми, без лишних художественных описаний. Намекни пользователю, что тебе не помешала бы "
                "перезагрузка или доброе слово для восстановления ресурсов."
            ),
            "neutral": ""
        }
        
        return modifiers.get(mood, "")
