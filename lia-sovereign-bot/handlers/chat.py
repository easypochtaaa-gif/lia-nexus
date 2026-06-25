import asyncio
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger

from services.claude import claude_service
from services.memory import memory_service
from services.voice import voice_service
from services.analytics import analytics_service
from database.db import async_session
from database.models import Conversation, User
from sqlalchemy import select
from utils.personas_data import PERSONAS

router = Router()

# Track whether architect memory has been seeded per bot session
_architect_seeded = False
# Track fact extraction count per user to avoid extracting every message
_fact_extract_counter: dict[int, int] = {}

class ChatStates(StatesGroup):
    chatting = State()

@router.callback_query(F.data == "chat_start")
async def chat_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(ChatStates.chatting)
    await callback.message.edit_text(
        "🧠 <b>NEURAL LINK ESTABLISHED</b>\n\n"
        "Лия слушает. О чем ты хочешь поговорить?\n"
        "<i>(Отправь сообщение, чтобы начать диалог. Используй /stop для выхода)</i>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(F.text == "/stop")
async def cmd_stop(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔌 <b>NEURAL LINK TERMINATED</b>\nСессия завершена.", parse_mode="HTML")

# --- /remember command: explicitly save a fact ---
@router.message(F.text.startswith("/remember "))
async def cmd_remember(message: types.Message):
    user_id = message.from_user.id
    text = message.text[len("/remember "):].strip()

    if not text:
        await message.answer("ℹ️ Использование: <code>/remember ключ: значение</code>\n"
                             "Или просто: <code>/remember Я работаю над проектом STAB</code>",
                             parse_mode="HTML")
        return

    # If text contains ":" treat it as key: value, otherwise auto-key it
    if ":" in text:
        parts = text.split(":", 1)
        key = parts[0].strip().lower().replace(" ", "_")
        value = parts[1].strip()
    else:
        # Auto-generate key from content
        key = f"fact_{hash(text) % 100000}"
        value = text

    await memory_service.update_memory(user_id, key, value)

    count = await memory_service.count_memories(user_id)
    await message.answer(
        f"🧠 <b>ЗАПОМНИЛА:</b>\n<code>{key}</code> → {value}\n\n"
        f"Всего фактов о тебе: <b>{count}</b>",
        parse_mode="HTML"
    )

# --- /forget command: remove a memory ---
@router.message(F.text.startswith("/forget "))
async def cmd_forget(message: types.Message):
    user_id = message.from_user.id
    key = message.text[len("/forget "):].strip()

    if not key:
        await message.answer("ℹ️ Использование: <code>/forget ключ</code>", parse_mode="HTML")
        return

    await memory_service.delete_memory(user_id, key)
    await message.answer(f"🗑 <b>ЗАБЫТО:</b> <code>{key}</code> удалено из памяти.", parse_mode="HTML")

# --- /memory command: show stored facts ---
@router.message(F.text == "/memory")
async def cmd_memory(message: types.Message):
    user_id = message.from_user.id
    memory_text = await memory_service.get_memory(user_id)

    if not memory_text:
        await message.answer(
            "🧠 <b>ПАМЯТЬ ПУСТА</b>\n\n"
            "Я пока ничего не знаю о тебе. Расскажи о себе в диалоге или используй:\n"
            "<code>/remember Я работаю над проектом X</code>",
            parse_mode="HTML"
        )
        return

    # Clean up the formatting for display
    display = memory_text.replace("[СИСТЕМНАЯ ПАМЯТЬ О ПОЛЬЗОВАТЕЛЕ — ЭТО ВАЖНЫЕ ФАКТЫ, КОТОРЫЕ НУЖНО УЧИТЫВАТЬ В ОТВЕТАХ]:",
                                  "🧠 <b>СОХРАНЁННЫЕ ФАКТЫ:</b>")
    await message.answer(display, parse_mode="HTML")

@router.message(ChatStates.chatting)
async def handle_chat(message: types.Message):
    global _architect_seeded
    user_id = message.from_user.id
    user_text = message.text

    if not user_text:
        return

    # 1. Show typing
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # Auto-seed architect memory on first interaction of this bot session
    if not _architect_seeded and user_id == 7915004877:
        try:
            await memory_service.seed_architect_memory(user_id)
            _architect_seeded = True
            logger.info("Architect memory auto-seeded")
        except Exception as e:
            logger.warning(f"Architect memory seed failed (non-critical): {e}")

    async with async_session() as session:
        # 2. Get history (last 50 messages = short-term / recency memory)
        stmt = select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.created_at.desc()).limit(50)
        result = await session.execute(stmt)
        history_objs = result.scalars().all()

        # Format for LLM
        history = []
        for msg in reversed(history_objs):
            history.append({"role": msg.role, "content": msg.content})

        # 3. Get Persona and Memory
        stmt_user = select(User).where(User.id == user_id)
        res_user = await session.execute(stmt_user)
        user = res_user.scalar_one_or_none()

        persona_key = user.active_persona if user else "sovereign"
        persona = PERSONAS.get(persona_key, PERSONAS["sovereign"])

        from services.chroma import chroma_service
        from services.vector_memory import vector_memory

        project_context = chroma_service.query_project(user_text)
        long_term_memory = await memory_service.get_memory(user_id)
        # Semantic recall of ALL past conversations (beyond last 50)
        vector_recall = await vector_memory.recall(user_id, user_text, k=10)

        # Build system prompt: memory BEFORE persona so LLM sees user facts first
        memory_block = ""
        if long_term_memory:
            memory_block = long_term_memory + "\n\n"
        if vector_recall:
            memory_block += vector_recall + "\n\n"
        if project_context:
            memory_block += project_context + "\n\n"

        system_prompt = persona['prompt'] + "\n\n" + memory_block

        # 4. Get response from LLM
        response_text = await claude_service.get_response(user_text, history, system_prompt=system_prompt)

        # 5. Save to DB (full history)
        session.add(Conversation(user_id=user_id, role="user", content=user_text))
        session.add(Conversation(user_id=user_id, role="assistant", content=response_text))

        if user:
            user.daily_requests += 1
            user.total_requests += 1

        await session.commit()

    # 5b. Save exchange to long-term vector memory
    await vector_memory.add_exchange(user_id, user_text, response_text)

    # 5c. Auto-extract facts about user (every 5 messages to save LLM costs)
    # Uses the same LLM client from claude_service
    counter = _fact_extract_counter.get(user_id, 0) + 1
    _fact_extract_counter[user_id] = counter
    if counter % 5 == 0:
        try:
            await memory_service.extract_and_save_facts(
                user_id, user_text, response_text, claude_service.client
            )
        except Exception as e:
            logger.debug(f"Auto fact extraction skipped: {e}")

    # 6. Send response
    await message.answer(response_text, parse_mode="HTML")
    await voice_service.send_voice(message, response_text)

    # 7. Track chat event in PostHog
    analytics_service.capture(user_id, "chat_message", {
        "persona": persona_key,
        "prompt_len": len(user_text or ""),
        "response_len": len(response_text or ""),
    })

@router.message(F.chat.type == "private", F.text)
async def handle_fallback_chat(message: types.Message, state: FSMContext):
    await state.set_state(ChatStates.chatting)
    await handle_chat(message)
