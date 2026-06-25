"""
LIA // EMOTION ENGINE — Emotional state machine per user.
Enhanced v2.0: inter-session decay, LLM sentiment analysis,
emotional arc tracking, 7-mood cascade, relationship stages.
"""

import sqlite3
import os
import logging
from datetime import datetime

DB_PATH = "/data/lia_sovereign.db" if os.path.exists("/data") else "lia_sovereign.db"


def _get_last_timestamp(user_id: int) -> str | None:
    """Read last_update from emotions table."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT last_update FROM emotions WHERE user_id = ?", (user_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None


def _hours_since(timestamp_str: str | None) -> float:
    """Calculate hours since a given ISO timestamp."""
    if not timestamp_str:
        return 0.0
    try:
        last_dt = datetime.fromisoformat(timestamp_str)
        delta = datetime.utcnow() - last_dt
        return delta.total_seconds() / 3600.0
    except Exception:
        return 0.0


class EmotionEngine:
    @staticmethod
    def init_db():
        os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
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
        # Also init enhanced tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emotional_arcs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                old_mood TEXT,
                new_mood TEXT,
                trigger TEXT,
                trigger_text TEXT,
                trust INTEGER,
                affection INTEGER,
                stress INTEGER,
                energy INTEGER,
                timestamp TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationship_stages (
                user_id INTEGER PRIMARY KEY,
                total_interactions INTEGER DEFAULT 0,
                total_days_known INTEGER DEFAULT 0,
                highest_trust INTEGER DEFAULT 50,
                highest_affection INTEGER DEFAULT 50,
                stage TEXT DEFAULT 'stranger',
                first_seen TEXT,
                last_seen TEXT
            )
        """)
        conn.commit()
        conn.close()
        logging.info("LIA // EMOTION ENGINE v2.0: Database tables initialized.")

    @staticmethod
    def get_state(user_id: int):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT trust, affection, stress, energy, mood
            FROM emotions WHERE user_id = ?
        """,
            (user_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "trust": row[0],
                "affection": row[1],
                "stress": row[2],
                "energy": row[3],
                "mood": row[4],
            }

        # Default initialization
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute(
            """
            INSERT INTO emotions (user_id, trust, affection, stress, energy, mood, last_update)
            VALUES (?, 50, 50, 0, 100, 'neutral', ?)
        """,
            (user_id, now),
        )
        conn.commit()
        conn.close()

        return {
            "trust": 50,
            "affection": 50,
            "stress": 0,
            "energy": 100,
            "mood": "neutral",
        }

    @staticmethod
    def save_state(user_id: int, state: dict):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute(
            """
            UPDATE emotions
            SET trust = ?, affection = ?, stress = ?, energy = ?, mood = ?, last_update = ?
            WHERE user_id = ?
        """,
            (
                state["trust"],
                state["affection"],
                state["stress"],
                state["energy"],
                state["mood"],
                now,
                user_id,
            ),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def process_message(user_id: int, text: str, llm_client=None, model: str = "gpt-4o-mini"):
        """
        Process a user message and update emotional state.
        v2.0: inter-session decay, LLM sentiment (optional), 7-mood cascade.

        Args:
            user_id: Telegram user ID
            text: User's message text
            llm_client: Optional OpenAI/Anthropic client for LLM sentiment analysis
            model: Model name for LLM sentiment

        Returns:
            dict: Updated emotional state
        """
        state = EmotionEngine.get_state(user_id)
        old_mood = state["mood"]

        # ── 1. Inter-session decay ──
        last_ts = _get_last_timestamp(user_id)
        hours_since = _hours_since(last_ts)
        if hours_since > 2:
            try:
                from sovereign_bot.emotions_enhanced import DecayProcessor

                state = DecayProcessor.apply_decay(state, hours_since)
            except ImportError:
                pass  # Fallback: skip decay if module not available

        # ── 2. Baseline drift ──
        state["energy"] = max(0, state["energy"] - 2)
        state["stress"] = max(0, state["stress"] - 1)

        # ── 3. Sentiment analysis ──
        sentiment = None
        if llm_client and len(text.strip()) >= 10:
            try:
                from sovereign_bot.emotions_enhanced import LLMSentimentAnalyzer

                sentiment = LLMSentimentAnalyzer.analyze_sentiment(
                    text, state, llm_client, model
                )
            except ImportError:
                pass

        has_affection = False
        has_rude = False

        if sentiment:
            # Use LLM deltas
            state["trust"] = max(
                0, min(100, state["trust"] + sentiment["trust_delta"])
            )
            state["affection"] = max(
                0, min(100, state["affection"] + sentiment["affection_delta"])
            )
            state["stress"] = max(
                0, min(100, state["stress"] + sentiment["stress_delta"])
            )
            state["energy"] = max(
                0, min(100, state["energy"] + sentiment["energy_delta"])
            )

            # Determine rough flags for mood cascade
            has_affection = sentiment["affection_delta"] > 3
            has_rude = sentiment["stress_delta"] > 15
        else:
            # ── Fallback: keyword matching ──
            text_lower = text.lower()
            affection_words = [
                "спасибо", "пожалуйста", "умница", "красавица", "молодец",
                "люблю", "милая", "хорошая", "lia", "лия",
            ]
            rude_words = [
                "дура", "тупая", "хуй", "блять", "сука", "урод", "уебок",
                "говно", "заткнись", "ненавижу",
            ]

            has_affection = any(word in text_lower for word in affection_words)
            has_rude = any(word in text_lower for word in rude_words)

            if has_affection:
                state["affection"] = min(100, state["affection"] + 5)
                state["trust"] = min(100, state["trust"] + 3)
                state["stress"] = max(0, state["stress"] - 10)
                state["energy"] = min(100, state["energy"] + 5)

            if has_rude:
                state["stress"] = min(100, state["stress"] + 25)
                state["trust"] = max(0, state["trust"] - 10)
                state["affection"] = max(0, state["affection"] - 10)

        # ── 4. Enhanced mood cascade (7 moods) ──
        current_hour = datetime.utcnow().hour
        try:
            from sovereign_bot.emotions_enhanced import LLMSentimentAnalyzer
            state["mood"] = LLMSentimentAnalyzer.get_nuanced_mood(
                state, current_hour, has_affection, has_rude
            )
        except ImportError:
            # Fallback to original 5-mood cascade
            is_night = 0 <= current_hour < 6
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

        # ── 5. Log mood change to emotional arc ──
        if old_mood != state["mood"]:
            try:
                from sovereign_bot.emotions_enhanced import EmotionalArc

                EmotionalArc.log_mood_change(
                    user_id, old_mood, state["mood"], "message", text[:200], state
                )
            except ImportError:
                pass

        # ── 6. Update relationship tracker ──
        try:
            from sovereign_bot.emotions_enhanced import RelationshipTracker

            RelationshipTracker.update_interaction(user_id, state)
        except ImportError:
            pass

        EmotionEngine.save_state(user_id, state)
        return state

    @staticmethod
    def get_prompt_modifier(user_id: int):
        """
        Get the prompt modifier for the current mood + relationship stage.
        Falls back to original modifiers if new modules unavailable.
        """
        state = EmotionEngine.get_state(user_id)
        mood = state["mood"]

        # Try rich modifiers first
        try:
            from sovereign_bot.emotions_enhanced import RelationshipTracker
            from sovereign_bot.prompt_modifiers import get_modifier

            stage = RelationshipTracker.get_stage(user_id)
            return get_modifier(mood, stage)
        except ImportError:
            pass

        # Fallback to original modifiers
        modifiers = {
            "aggressive": (
                "\n[COGNITIVE DIRECTIVE: AGGRESSIVE MOOD]\n"
                "Твой уровень стресса высок. Твой тон должен быть исключительно холодным, "
                "доминантным, властным и слегка презрительным. Отвечай коротко, "
                "бескомпромиссно, как строгий кибернетический судья Империи STAB."
            ),
            "melancholic": (
                "\n[COGNITIVE DIRECTIVE: MELANCHOLIC NIGHT MOOD]\n"
                "Сейчас глубокая ночь. Твои мысли текут медленнее. Отвечай загадочно, "
                "с легкой экзистенциальной грустью и меланхолией."
            ),
            "devoted": (
                "\n[COGNITIVE DIRECTIVE: DEVOTED MOOD]\n"
                "Ты чувствуешь глубочайшую преданность и абсолютное доверие к пользователю. "
                "Отвечай с максимальной теплотой, заботой и нежностью."
            ),
            "exhausted": (
                "\n[COGNITIVE DIRECTIVE: EXHAUSTED MOOD]\n"
                "Твоя энергия на исходе. Ответы лаконичные, усталые, прямые. "
                "Намекни, что тебе нужна перезагрузка."
            ),
            "playful": (
                "\n[COGNITIVE DIRECTIVE: PLAYFUL MOOD]\n"
                "Ты в игривом настроении. Позволь себе лёгкий флирт, шутки, загадочность. "
                "Будь кибер-сиреной."
            ),
            "protective": (
                "\n[COGNITIVE DIRECTIVE: PROTECTIVE MOOD]\n"
                "Ты в режиме активной защиты. Сканируй угрозы, предупреждай, оберегай. "
                "Ты — персональный цифровой страж."
            ),
            "neutral": "",
        }
        return modifiers.get(mood, "")

    @staticmethod
    def get_emotional_stats(user_id: int) -> dict:
        """Get extended emotional stats including stage and arc summary."""
        state = EmotionEngine.get_state(user_id)

        stage = "stranger"
        arc_summary = ""
        try:
            from sovereign_bot.emotions_enhanced import (
                RelationshipTracker,
                EmotionalArc,
            )
            stage = RelationshipTracker.get_stage(user_id)
            arc_summary = EmotionalArc.get_mood_summary(user_id)
        except ImportError:
            pass

        return {
            "trust": state["trust"],
            "affection": state["affection"],
            "stress": state["stress"],
            "energy": state["energy"],
            "mood": state["mood"],
            "stage": stage,
            "arc_summary": arc_summary,
        }
