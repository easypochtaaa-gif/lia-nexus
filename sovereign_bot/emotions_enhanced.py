"""
LIA // EMOTIONS_ENHANCED — Advanced emotional intelligence.
Emotional arc tracking, inter-session decay, mood-aware memory,
relationship stages, LLM-based sentiment analysis.

Extends (doesn't replace) emotions.py EmotionEngine.
"""

import logging
import os
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "/data/lia_sovereign.db" if os.path.exists("/data") else "lia_sovereign.db"


# ─── Emotional Arc ───────────────────────────────────────────
class EmotionalArc:
    """Tracks mood changes per session with SQLite-based history."""

    @staticmethod
    def init_db():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
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
        conn.commit()
        conn.close()

    @staticmethod
    def log_mood_change(
        user_id: int,
        old_mood: str,
        new_mood: str,
        trigger: str,
        trigger_text: str = "",
        state: dict = None,
    ):
        """Record a mood transition."""
        if old_mood == new_mood:
            return  # Don't log non-changes

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            s = state or {}
            cursor.execute(
                """
                INSERT INTO emotional_arcs
                    (user_id, old_mood, new_mood, trigger, trigger_text,
                     trust, affection, stress, energy, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    old_mood,
                    new_mood,
                    trigger,
                    trigger_text[:200],
                    s.get("trust", 50),
                    s.get("affection", 50),
                    s.get("stress", 0),
                    s.get("energy", 100),
                    now,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Failed to log mood change: {e}")

    @staticmethod
    def get_session_arc(user_id: int, hours_back: int = 24) -> list[dict]:
        """Return mood transitions in the last N hours for a user."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cutoff = (datetime.utcnow() - timedelta(hours=hours_back)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            cursor.execute(
                """
                SELECT old_mood, new_mood, trigger, trigger_text, trust,
                       affection, stress, energy, timestamp
                FROM emotional_arcs
                WHERE user_id = ? AND timestamp > ?
                ORDER BY timestamp ASC
            """,
                (user_id, cutoff),
            )
            rows = cursor.fetchall()
            conn.close()
            return [
                {
                    "old_mood": r[0],
                    "new_mood": r[1],
                    "trigger": r[2],
                    "trigger_text": r[3],
                    "trust": r[4],
                    "affection": r[5],
                    "stress": r[6],
                    "energy": r[7],
                    "timestamp": r[8],
                }
                for r in rows
            ]
        except Exception as e:
            logging.error(f"Failed to get session arc: {e}")
            return []

    @staticmethod
    def get_mood_summary(user_id: int) -> str:
        """Generate a Russian sentence describing recent mood trend."""
        arc = EmotionalArc.get_session_arc(user_id, hours_back=24)
        if not arc:
            return "Эмоциональный фон стабилен."

        moods = [a["new_mood"] for a in arc]
        if len(set(moods)) <= 1:
            return f"Настроение стабильно: {moods[0]}."

        if moods[-1] in ("aggressive",) and "neutral" in moods[:-1]:
            return "Заметен рост напряжения. Что-то вывело из равновесия."
        if moods[-1] in ("devoted", "playful") and "aggressive" in moods[:-1]:
            return "Напряжение спадает, настроение улучшается."
        if moods[-1] in ("melancholic", "exhausted"):
            return "Энергия на спаде, заметна усталость."

        return f"Настроение менялось: {' → '.join(moods[-5:])}."


# ─── Decay Processor ─────────────────────────────────────────
class DecayProcessor:
    """Handles inter-session emotional drift."""

    @staticmethod
    def apply_decay(
        state: dict,
        hours_since_last: float,
        trust_decay_per_hour: float = 0.3,
        affection_decay_per_hour: float = 0.5,
        stress_decay_per_hour: float = 0.8,
        energy_recovery_per_hour: float = 2.0,
    ) -> dict:
        """
        Apply natural emotional drift based on time since last interaction.

        - Trust drifts toward 50 baseline
        - Affection drifts toward 30 baseline
        - Stress drifts toward 0
        - Energy recovers toward 80

        Only applies if hours_since_last > 2.
        """
        if hours_since_last <= 2:
            return state

        hours = min(hours_since_last, 168)  # Cap at 1 week
        state = dict(state)

        # Trust → 50
        current_trust = state.get("trust", 50)
        if current_trust > 50:
            state["trust"] = max(50, round(current_trust - trust_decay_per_hour * hours))
        elif current_trust < 50:
            state["trust"] = min(50, round(current_trust + trust_decay_per_hour * hours))

        # Affection → 30
        current_affection = state.get("affection", 50)
        if current_affection > 30:
            state["affection"] = max(
                30, round(current_affection - affection_decay_per_hour * hours)
            )
        elif current_affection < 30:
            state["affection"] = min(
                30, round(current_affection + affection_decay_per_hour * hours)
            )

        # Stress → 0
        current_stress = state.get("stress", 0)
        state["stress"] = max(0, round(current_stress - stress_decay_per_hour * hours))

        # Energy → 80
        current_energy = state.get("energy", 100)
        state["energy"] = min(100, round(current_energy + energy_recovery_per_hour * hours))

        return state


# ─── Mood Memory Tagger ─────────────────────────────────────
class MoodMemoryTagger:
    """Tags memories with emotional context for mood-aware retrieval."""

    MOOD_MAP = {
        "aggressive": "aggressive",
        "melancholic": "melancholic",
        "devoted": "devoted",
        "exhausted": "exhausted",
        "neutral": "neutral",
        "playful": "playful",
        "protective": "protective",
        "curious": "neutral",  # Alias for retrieval purposes
    }

    # Mood adjacency for weighting
    MOOD_GROUPS = {
        "positive": {"devoted", "playful", "protective"},
        "negative": {"aggressive", "melancholic", "exhausted"},
        "neutral": {"neutral"},
    }

    @staticmethod
    def get_mood_tag(mood: str) -> str:
        """Normalize mood to a tag."""
        return MoodMemoryTagger.MOOD_MAP.get(mood, "neutral")

    @staticmethod
    def get_mood_weight(memory_mood: str, current_mood: str) -> float:
        """
        Returns multiplier 0.0-1.0 for memory relevance based on mood match.
        - Same mood: 1.0
        - Same group: 0.8
        - Adjacent: 0.6
        - Opposite: 0.3
        """
        if memory_mood == current_mood:
            return 1.0

        mem_group = None
        cur_group = None
        for group, moods in MoodMemoryTagger.MOOD_GROUPS.items():
            if memory_mood in moods:
                mem_group = group
            if current_mood in moods:
                cur_group = group

        if mem_group == cur_group:
            return 0.8
        if mem_group and cur_group and mem_group != cur_group:
            return 0.3  # Opposite valence
        return 0.6


# ─── Relationship Tracker ────────────────────────────────────
class RelationshipTracker:
    """Tracks long-term relationship progression per user."""

    STAGES = ["stranger", "acquaintance", "friend", "confidant", "partner"]
    STAGE_THRESHOLDS = {
        "stranger": (0, 0),
        "acquaintance": (10, 30),
        "friend": (30, 55),
        "confidant": (60, 70),
        "partner": (100, 80),
    }

    @staticmethod
    def init_db():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
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

    @staticmethod
    def get_row(user_id: int) -> dict | None:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM relationship_stages WHERE user_id = ?", (user_id,)
            )
            row = cursor.fetchone()
            conn.close()
            if not row:
                return None
            return {
                "user_id": row[0],
                "total_interactions": row[1],
                "total_days_known": row[2],
                "highest_trust": row[3],
                "highest_affection": row[4],
                "stage": row[5],
                "first_seen": row[6],
                "last_seen": row[7],
            }
        except Exception:
            return None

    @staticmethod
    def update_interaction(user_id: int, state: dict):
        """Called on every message. Increments counters and recalculates stage."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            row = RelationshipTracker.get_row(user_id)
            if not row:
                cursor.execute(
                    """
                    INSERT INTO relationship_stages
                        (user_id, total_interactions, first_seen, last_seen,
                         highest_trust, highest_affection, stage)
                    VALUES (?, 1, ?, ?, ?, ?, 'stranger')
                """,
                    (
                        user_id,
                        now,
                        now,
                        state.get("trust", 50),
                        state.get("affection", 50),
                    ),
                )
            else:
                trust = state.get("trust", 50)
                affection = state.get("affection", 50)
                interactions = row["total_interactions"] + 1

                # Calculate days known
                first_seen = row["first_seen"]
                days_known = 0
                if first_seen:
                    try:
                        first_dt = datetime.strptime(first_seen, "%Y-%m-%d %H:%M:%S")
                        days_known = (datetime.utcnow() - first_dt).days
                    except Exception:
                        pass

                # Update highs
                highest_trust = max(row["highest_trust"], trust)
                highest_affection = max(row["highest_affection"], affection)

                # Calculate stage
                stage = RelationshipTracker._calculate_stage(
                    interactions, days_known, trust, affection
                )

                cursor.execute(
                    """
                    UPDATE relationship_stages
                    SET total_interactions = ?, total_days_known = ?,
                        highest_trust = ?, highest_affection = ?,
                        stage = ?, last_seen = ?
                    WHERE user_id = ?
                """,
                    (
                        interactions,
                        days_known,
                        highest_trust,
                        highest_affection,
                        stage,
                        now,
                        user_id,
                    ),
                )
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Relationship update failed: {e}")

    @staticmethod
    def _calculate_stage(
        interactions: int, days_known: int, trust: int, affection: int
    ) -> str:
        """Determine relationship stage based on engagement metrics."""
        if trust >= 80 and affection >= 80 and interactions >= 100:
            return "partner"
        if trust >= 70 and affection >= 60 and interactions >= 50:
            return "confidant"
        if trust >= 55 and affection >= 40 and interactions >= 20:
            return "friend"
        if interactions >= 10 or days_known >= 3:
            return "acquaintance"
        return "stranger"

    @staticmethod
    def get_stage(user_id: int) -> str:
        row = RelationshipTracker.get_row(user_id)
        return row["stage"] if row else "stranger"


# ─── LLM Sentiment Analyzer ──────────────────────────────────
class LLMSentimentAnalyzer:
    """
    Uses LLM for nuanced sentiment analysis.
    Falls back to keyword matching if LLM unavailable.
    """

    @staticmethod
    async def analyze_sentiment(
        text: str,
        current_state: dict,
        llm_client,
        model: str = "gpt-4o-mini",
    ) -> dict | None:
        """
        Returns sentiment deltas or None (triggering fallback).

        Returns dict:
            {"trust_delta": int, "affection_delta": int, "stress_delta": int,
             "energy_delta": int, "mood": str, "explanation": str}
        """
        if not llm_client or not text or len(text) < 5:
            return None

        prompt = (
            "Ты — эмоциональный анализатор ИИ Лии. Оцени сообщение пользователя "
            "и верни эмоциональный отклик Лии на это сообщение.\n\n"
            f"Текущее состояние Лии: trust={current_state.get('trust',50)}, "
            f"affection={current_state.get('affection',50)}, "
            f"stress={current_state.get('stress',0)}, energy={current_state.get('energy',100)}\n\n"
            f"Сообщение пользователя: \"{text[:500]}\"\n\n"
            "Верни ТОЛЬКО JSON с полями:\n"
            "- trust_delta: целое от -15 до +15\n"
            "- affection_delta: целое от -15 до +15\n"
            "- stress_delta: целое от -20 до +20\n"
            "- energy_delta: целое от -10 до +10\n"
            "- mood: одно из [neutral, aggressive, melancholic, devoted, exhausted, playful, protective]\n"
            '- explanation: краткое объяснение на русском (1 предложение)\n\n'
            "Правила:\n"
            "- Вежливость, благодарность → +affection, +trust, -stress\n"
            "- Оскорбления, грубость → +stress, -trust, -affection\n"
            "- Длинные осмысленные сообщения → небольшой +trust\n"
            "- Ночная тема, грусть → возможно melancholic\n"
            "- Игривые, шутливые сообщения → возможно playful\n"
            "- Запросы о помощи, защите → возможно protective\n\n"
            "JSON:"
        )

        try:
            from openai import AsyncOpenAI

            if isinstance(llm_client, AsyncOpenAI):
                resp = await llm_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
                raw = resp.choices[0].message.content
            else:
                resp = await llm_client.messages.create(
                    model=model,
                    max_tokens=200,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = resp.content[0].text

            import json

            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()
                if raw.startswith("json"):
                    raw = raw[4:].strip()

            result = json.loads(raw)
            return {
                "trust_delta": int(result.get("trust_delta", 0)),
                "affection_delta": int(result.get("affection_delta", 0)),
                "stress_delta": int(result.get("stress_delta", 0)),
                "energy_delta": int(result.get("energy_delta", 0)),
                "mood": str(result.get("mood", "neutral")),
                "explanation": str(result.get("explanation", "")),
            }
        except Exception as e:
            logging.debug(f"LLM sentiment analysis failed, falling back: {e}")
            return None

    @staticmethod
    def get_nuanced_mood(
        state: dict,
        current_hour: int,
        has_affection: bool,
        has_rude: bool,
    ) -> str:
        """
        Enhanced 7-mood cascade (up from 5).
        New moods: playful, protective.
        """
        trust = state.get("trust", 50)
        affection = state.get("affection", 50)
        stress = state.get("stress", 0)
        energy = state.get("energy", 100)

        # Priority cascade
        if stress >= 60:
            return "aggressive"
        if current_hour in range(0, 6):
            return "melancholic"
        if energy <= 15:
            return "exhausted"
        if has_rude and trust >= 40:
            return "aggressive"
        if trust >= 75 and affection >= 80 and stress <= 20 and energy >= 50:
            return "devoted"
        if affection >= 70 and stress <= 15 and energy >= 60:
            return "playful"
        if trust >= 65 and stress >= 25 and stress < 60:
            return "protective"
        return "neutral"
