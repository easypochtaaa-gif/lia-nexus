"""
/synapse — Triple Core дебаты (главный контент для видео).

Опрашивает три ИИ-ядра (Архитектор / Прагматик / Аналитик), показывает их
расхождения и финальный вердикт Арбитра JEMA. Результат сохраняется в таблицу
`Debate` — чтобы NotebookLM-обзоры брали реальные данные дебатов.
"""
from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from loguru import logger

from database.db import async_session
from database.models import Debate, User
from sqlalchemy import select
from services.synapse_core import run_ensemble, format_debate

router = Router()

TG_LIMIT = 4000  # запас под лимит Telegram 4096


def _split(text: str, limit: int = TG_LIMIT):
    """Разбивает длинный текст на части по лимиту Telegram (по строкам)."""
    parts, buf = [], ""
    for line in text.split("\n"):
        if len(buf) + len(line) + 1 > limit:
            if buf:
                parts.append(buf)
            buf = line
        else:
            buf = f"{buf}\n{line}" if buf else line
    if buf:
        parts.append(buf)
    return parts


@router.message(Command("synapse"))
async def cmd_synapse(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    prompt = (command.args or "").strip()

    if not prompt:
        await message.answer(
            "🧠 <b>SYNAPSE TRIPLE CORE</b>\n\n"
            "Задай вопрос — три ИИ-ядра вступят в дебаты, а Арбитр JEMA вынесет вердикт.\n\n"
            "Пример: <code>/synapse как лучше масштабировать STAB-экономику?</code>",
            parse_mode="HTML",
        )
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    status = await message.answer("⚡ Ядра SYNAPSE вступили в дебаты...")

    try:
        result = await run_ensemble(prompt)
    except Exception as e:
        logger.error(f"/synapse failed: {e}")
        await status.edit_text("🌀 [NEURAL_LINK_ERROR] Дебаты ядер прерваны.")
        return

    # Сохраняем дебаты в БД (best-effort)
    try:
        cores = {c["key"]: c["answer"] for c in result["cores"]}
        async with async_session() as session:
            # гарантируем наличие пользователя (FK)
            exists = await session.execute(select(User.id).where(User.id == user_id))
            if exists.scalar_one_or_none() is not None:
                session.add(Debate(
                    user_id=user_id,
                    prompt=prompt,
                    architect=cores.get("architect"),
                    pragmatic=cores.get("pragmatic"),
                    analyst=cores.get("analyst"),
                    arbiter=result["arbiter"],
                ))
                await session.commit()
    except Exception as e:
        logger.debug(f"Debate save skipped: {e}")

    text = format_debate(result)
    parts = _split(text)
    try:
        await status.edit_text(parts[0], parse_mode="HTML")
    except Exception:
        await status.edit_text(parts[0])
    for extra in parts[1:]:
        await message.answer(extra, parse_mode="HTML")
