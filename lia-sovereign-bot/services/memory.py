import json
import asyncio
from sqlalchemy import select, delete
from database.db import async_session
from database.models import Memory
from loguru import logger

# Known facts from memory.json — pre-seeded for the Architect
ARCHITECT_FACTS = {
    "name": "Артур Дмитриевич Клопков",
    "alias": "StabX / Master Architect",
    "origin": "Киев, 08.03.1996",
    "role": "Создатель Империи STAB, Synapse, Stabus, Lia",
    "vibe": "ASCENDED_DIRECTOR — киберпанк-энтузиаст, создатель цифровых экосистем",
    "bot_purpose": "LIA — суверенный ИИ-компаньон, помощник в проектах, финансах, кибербезопасности",
}

FACT_EXTRACTION_PROMPT = """Ты — модуль памяти LIA. Проанализируй сообщение пользователя и извлеки ВАЖНЫЕ ФАКТЫ о нём.

Извлекай ТОЛЬКО:
- Имя, откуда человек, дата рождения
- Проекты, над которыми работает
- Цели, планы, задачи
- Предпочтения, вкусы, привычки
- Важные события, встречи, договорённости
- Финансовые договорённости, долги, оплаты
- Технические детали (какой стек, какие сервера, пароли НЕ сохранять!)

НЕ извлекай:
- Пароли, ключи, секреты
- Очевидные/тривиальные утверждения
- Вопросы пользователя

Верни СТРОГО JSON-массив объектов {"key": "короткий_ключ_на_английском", "value": "факт_на_русском"}.
Если фактов нет, верни [].
Отвечай ТОЛЬКО JSON, без markdown."""


class MemoryService:
    async def get_memory(self, user_id: int) -> str:
        async with async_session() as session:
            stmt = select(Memory).where(Memory.user_id == user_id)
            result = await session.execute(stmt)
            memories = result.scalars().all()

            if not memories:
                return ""

            memory_text = "\n[СИСТЕМНАЯ ПАМЯТЬ О ПОЛЬЗОВАТЕЛЕ — ЭТО ВАЖНЫЕ ФАКТЫ, КОТОРЫЕ НУЖНО УЧИТЫВАТЬ В ОТВЕТАХ]:\n"
            for mem in memories:
                memory_text += f"- {mem.key}: {mem.value}\n"
            return memory_text

    async def update_memory(self, user_id: int, key: str, value: str):
        async with async_session() as session:
            stmt = select(Memory).where(Memory.user_id == user_id, Memory.key == key)
            result = await session.execute(stmt)
            memory = result.scalar_one_or_none()

            if memory:
                memory.value = value
            else:
                memory = Memory(user_id=user_id, key=key, value=value)
                session.add(memory)

            await session.commit()
            logger.info(f"Memory updated for user {user_id}: {key} = {value}")

    async def get_facts_list(self, user_id: int) -> list[dict]:
        """Get all memories as a list of dicts."""
        async with async_session() as session:
            stmt = select(Memory).where(Memory.user_id == user_id)
            result = await session.execute(stmt)
            memories = result.scalars().all()
            return [{"key": m.key, "value": m.value} for m in memories]

    async def delete_memory(self, user_id: int, key: str):
        async with async_session() as session:
            stmt = delete(Memory).where(Memory.user_id == user_id, Memory.key == key)
            await session.execute(stmt)
            await session.commit()
            logger.info(f"Memory deleted for user {user_id}: {key}")

    async def seed_architect_memory(self, user_id: int):
        """Pre-populate memory for the Architect from known facts."""
        async with async_session() as session:
            for key, value in ARCHITECT_FACTS.items():
                stmt = select(Memory).where(Memory.user_id == user_id, Memory.key == key)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                if not existing:
                    session.add(Memory(user_id=user_id, key=key, value=value))
            await session.commit()
            logger.info(f"Architect memory seeded for user {user_id}")

    async def extract_and_save_facts(self, user_id: int, user_message: str, assistant_response: str, llm_client):
        """Use LLM to extract personal facts from the user's message and save them.
        Runs as a background task — failures are logged but don't affect the bot response."""
        try:
            # Combine user message + assistant context for better extraction
            text_to_analyze = f"Пользователь: {user_message[:500]}"

            response = await llm_client.chat.completions.create(
                model="gpt-4o-mini",  # cheap model for extraction
                messages=[
                    {"role": "system", "content": FACT_EXTRACTION_PROMPT},
                    {"role": "user", "content": text_to_analyze}
                ],
                max_tokens=500,
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            facts = json.loads(content)
            if isinstance(facts, dict) and "facts" in facts:
                facts = facts["facts"]  # handle {"facts": [...]} format

            if not isinstance(facts, list):
                return

            for fact in facts:
                if fact.get("key") and fact.get("value"):
                    await self.update_memory(user_id, fact["key"], fact["value"])
                    logger.info(f"Auto-saved fact for user {user_id}: {fact['key']} = {fact['value']}")

        except Exception as e:
            logger.debug(f"Fact extraction skipped (non-critical): {e}")

    async def count_memories(self, user_id: int) -> int:
        """Return count of stored memories for a user."""
        async with async_session() as session:
            stmt = select(Memory).where(Memory.user_id == user_id)
            result = await session.execute(stmt)
            return len(result.scalars().all())

memory_service = MemoryService()
