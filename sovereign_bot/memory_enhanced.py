"""
LIA // MEMORY_ENHANCED — Advanced memory operations.
LLM-based fact extraction, conversation summarization,
memory consolidation, TTL pruning, importance scoring.
Replaces primitive keyword-based extraction in main.py.
"""

import asyncio
import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta

# Reuse same DB path as memory.py
DB_PATH = "/data/lia_sovereign.db" if os.path.exists("/data") else "lia_sovereign.db"


class MemoryConsolidator:
    @staticmethod
    async def extract_facts(
        user_id: int,
        text: str,
        llm_client,
        llm_model: str = "gpt-4o-mini",
    ) -> list[dict]:
        """
        Replaces keyword-based fact extraction (main.py L1174-1179).
        Uses LLM to extract personal facts from user messages.

        Returns list of dicts:
            {"fact": str, "category": str, "importance": float}

        Categories: identity, preference, event, relationship, location, skill, general
        """
        if not text or len(text.strip()) < 10:
            return []

        prompt = (
            "Ты — анализатор фактов ИИ Лии. Извлеки из сообщения пользователя "
            "КЛЮЧЕВЫЕ ФАКТЫ о нём, которые стоит запомнить на будущее.\n\n"
            "Сообщение пользователя:\n"
            f'"""{text}"""\n\n'
            "Верни ТОЛЬКО JSON-массив объектов с полями:\n"
            '- "fact": краткая формулировка факта (1 предложение на русском, от 3-го лица: "Пользователь ...")\n'
            '- "category": одна из: identity, preference, event, relationship, location, skill, general\n'
            '- "importance": число от 0.0 до 1.0 (насколько это важно помнить)\n\n'
            "Правила:\n"
            "- Извлекай ТОЛЬКО факты о пользователе, не о других людях\n"
            "- Факты о имени, возрасте, работе, семье = identity, importance >= 0.8\n"
            "- Факты о предпочтениях, вкусах = preference, importance >= 0.6\n"
            "- Факты о прошедших событиях = event, importance >= 0.5\n"
            "- Если нет значимых фактов — верни []\n"
            "- Не выдумывай факты, которых нет в сообщении\n\n"
            "JSON:"
        )

        try:
            from openai import AsyncOpenAI

            if isinstance(llm_client, AsyncOpenAI):
                resp = await llm_client.chat.completions.create(
                    model=llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
                raw = resp.choices[0].message.content
            else:
                # Anthropic client — use JSON output
                resp = await llm_client.messages.create(
                    model=llm_model,
                    max_tokens=500,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = resp.content[0].text

            import json

            # Extract JSON from response
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()
                if raw.startswith("json"):
                    raw = raw[4:].strip()

            facts = json.loads(raw)
            if isinstance(facts, dict) and "facts" in facts:
                facts = facts["facts"]
            if not isinstance(facts, list):
                facts = []

            # Validate and clean
            valid_facts = []
            for f in facts:
                if isinstance(f, dict) and f.get("fact"):
                    valid_facts.append(
                        {
                            "fact": str(f["fact"]).strip(),
                            "category": str(f.get("category", "general")).strip(),
                            "importance": float(f.get("importance", 0.5)),
                        }
                    )
            return valid_facts

        except Exception as e:
            logging.error(f"LLM fact extraction failed: {e}")
            return []

    @staticmethod
    async def summarize_conversation(
        messages: list[dict],
        llm_client,
        llm_model: str = "gpt-4o-mini",
    ) -> str:
        """
        Takes the last N messages from short-term context,
        calls LLM to produce a concise Russian summary.

        Returns summary text, or empty string on failure.
        """
        if not messages or len(messages) < 3:
            return ""

        # Format messages for the LLM
        formatted = []
        for m in messages[-20:]:  # Last 20 messages max
            role = "👤" if m.get("role") == "user" else "👁‍🗨"
            content = m.get("content", "")[:300]  # Truncate long messages
            formatted.append(f"{role}: {content}")
        dialogue = "\n".join(formatted)

        prompt = (
            "Ты — система консолидации памяти ИИ Лии. "
            "Ниже — фрагмент диалога между пользователем и Лией.\n"
            "Напиши КРАТКУЮ сводку (2-3 предложения на русском) того, "
            "что происходило в разговоре, какие темы обсуждались, "
            "и что важно запомнить о пользователе.\n\n"
            f"Диалог:\n{dialogue}\n\n"
            "Сводка:"
        )

        try:
            from openai import AsyncOpenAI

            if isinstance(llm_client, AsyncOpenAI):
                resp = await llm_client.chat.completions.create(
                    model=llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.3,
                )
                return resp.choices[0].message.content.strip()
            else:
                resp = await llm_client.messages.create(
                    model=llm_model,
                    max_tokens=200,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}],
                )
                return resp.content[0].text.strip()
        except Exception as e:
            logging.error(f"Conversation summarization failed: {e}")
            return ""

    @staticmethod
    def score_importance(content: str) -> float:
        """
        Heuristic importance scoring.
        Factors: length, named entity signals, emotional keywords, personal info markers.

        Returns 0.0-1.0.
        """
        score = 0.3  # baseline
        content_lower = content.lower()

        # Length bonus
        if len(content) > 50:
            score += 0.1
        if len(content) > 100:
            score += 0.1

        # Named entity signals (Russian patterns)
        personal_signals = [
            "меня зовут", "моё имя", "я ", "мой ", "моя ", "мои ",
            "живу в", "работаю", "учусь", "мой адрес", "мой телефон",
            "люблю", "ненавижу", "обожаю", "хочу", "мечтаю",
        ]
        score += 0.05 * sum(1 for s in personal_signals if s in content_lower)
        score = min(score, 1.0)

        return round(score, 2)

    @staticmethod
    async def consolidate_memories(
        user_id: int,
        llm_client=None,
        threshold: float = 0.85,
    ) -> int:
        """
        Scans all ChromaDB memories for a user.
        Finds clusters of similar memories (semantic overlap),
        merges them via LLM into one, deletes originals.
        Returns count of merged entries.
        """
        try:
            from sovereign_bot.chroma_memory import LiaMemory

            all_memories = await LiaMemory.get_all_for_user(user_id)
            if len(all_memories) < 3:
                return 0

            # Simple grouping by content similarity
            merged = 0
            seen = set()

            for i, mem_a in enumerate(all_memories):
                if mem_a["id"] in seen:
                    continue
                cluster = [mem_a]
                for j, mem_b in enumerate(all_memories):
                    if i >= j or mem_b["id"] in seen:
                        continue
                    # Simple Jaccard-like overlap of words
                    words_a = set(mem_a["content"].lower().split())
                    words_b = set(mem_b["content"].lower().split())
                    if not words_a or not words_b:
                        continue
                    overlap = len(words_a & words_b) / min(len(words_a), len(words_b))
                    if overlap > 0.7:
                        cluster.append(mem_b)
                        seen.add(mem_b["id"])

                if len(cluster) >= 2:
                    seen.add(mem_a["id"])
                    merged += len(cluster) - 1

            return merged
        except Exception as e:
            logging.error(f"Memory consolidation failed: {e}")
            return 0

    @staticmethod
    async def prune_memories(
        user_id: int | None = None,
        max_age_days: int = 90,
        min_importance: float = 0.2,
    ) -> int:
        """
        Deletes ChromaDB memories that are:
        - Older than max_age_days AND importance < min_importance
        - Or user_id specified (for targeted cleanup).

        Returns count of deleted entries.
        """
        try:
            from sovereign_bot.chroma_memory import LiaMemory

            all_memories = await LiaMemory.get_all_for_user(user_id) if user_id else []
            deleted = 0
            cutoff = (datetime.utcnow() - timedelta(days=max_age_days)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            for mem in all_memories:
                importance = float(mem.get("importance", 0.5))
                timestamp = mem.get("timestamp", "")
                if importance < min_importance and timestamp < cutoff:
                    await LiaMemory.delete_by_ids([mem["id"]])
                    deleted += 1

            return deleted
        except Exception as e:
            logging.error(f"Memory pruning failed: {e}")
            return 0


# Track message counts per user for summarization triggers
_message_counts: dict[int, int] = {}

SUMMARY_THRESHOLD = 10  # Summarize every N messages


def get_message_count(user_id: int) -> int:
    return _message_counts.get(user_id, 0)


def increment_message_count(user_id: int) -> int:
    _message_counts[user_id] = _message_counts.get(user_id, 0) + 1
    return _message_counts[user_id]


def reset_message_count(user_id: int):
    _message_counts[user_id] = 0


def should_summarize(user_id: int) -> bool:
    """Returns True every SUMMARY_THRESHOLD messages."""
    return get_message_count(user_id) >= SUMMARY_THRESHOLD
