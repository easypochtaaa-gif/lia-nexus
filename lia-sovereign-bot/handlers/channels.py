from aiogram import Router, types
from aiogram.filters import Command
from aiogram.filters import CommandObject
from loguru import logger

from config import settings
from services.aegis_shield import log_threat

router = Router()

# Только Мастер-Архитектор может постить в каналы
ADMIN_IDS = (settings.admin_id, 7915004877)


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def _publish(message: types.Message, command: CommandObject, channel_id: int, channel_label: str):
    """Публикует сообщение в указанный канал.

    Поддерживает два режима:
    1. Команда с текстом:  /post Привет, Империя!
    2. Команда в ответ на сообщение (текст/фото/видео/документ) — будет
       скопировано в канал «как есть» (с подписью).
    """
    if not _is_admin(message.from_user.id):
        await log_threat(
            "admin_deny",
            user_id=message.from_user.id,
            source=f"chat:{message.chat.id}",
            details=f"User {message.from_user.id} attempted channel post: {command.command}",
        )
        await message.answer("⚠️ Доступ заблокирован. Постить в каналы может только Master Architect.")
        return

    try:
        if message.reply_to_message:
            # Копируем медиа/текст из исходного сообщения (сохраняя оформление)
            await message.bot.copy_message(
                chat_id=channel_id,
                from_chat_id=message.chat.id,
                message_id=message.reply_to_message.message_id,
            )
        elif command.args:
            await message.bot.send_message(
                chat_id=channel_id,
                text=command.args,
                parse_mode="HTML",
            )
        else:
            await message.answer(
                f"✍️ Нечего публиковать.\n\n"
                f"Используйте: <code>/{command.command} текст поста</code>\n"
                f"или ответьте этой командой на сообщение (фото/видео/текст), которое нужно отправить в {channel_label}.",
                parse_mode="HTML",
            )
            return

        await message.answer(f"✅ Опубликовано в {channel_label}.")
    except Exception as e:
        logger.error(f"Failed to post to {channel_label} ({channel_id}): {e}")
        await message.answer(
            f"❌ Не удалось опубликовать в {channel_label}.\n"
            f"Проверьте, что бот добавлен в канал как администратор с правом публикации.\n\n"
            f"<pre>{e}</pre>",
            parse_mode="HTML",
        )


@router.message(Command("post"))
async def cmd_post(message: types.Message, command: CommandObject):
    """Публикация в ПУБЛИЧНЫЙ канал (@darkstabspace)."""
    await _publish(message, command, settings.public_channel_id, "📢 публичный канал")


@router.message(Command("whisper"))
async def cmd_whisper(message: types.Message, command: CommandObject):
    """Публикация в ЛИЧНЫЙ канал «для двоих»."""
    await _publish(message, command, settings.private_channel_id, "🔒 личный канал")


@router.message(Command("autopost"))
async def cmd_autopost(message: types.Message):
    """Сгенерировать и сразу опубликовать авто-пост (новость/обзор STAB) в публичный канал.

    Это ручной триггер той же логики, что выполняет планировщик APScheduler по расписанию.
    """
    if not _is_admin(message.from_user.id):
        await log_threat(
            "admin_deny",
            user_id=message.from_user.id,
            source=f"chat:{message.chat.id}",
            details=f"User {message.from_user.id} attempted /autopost",
        )
        await message.answer("⚠️ Доступ заблокирован. Авто-постинг доступен только Master Architect.")
        return

    from services.scheduler import publish_scheduled_post

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    status = await message.answer("⚡ Генерирую авто-пост для публичного канала...")
    try:
        await publish_scheduled_post(message.bot)
        await status.edit_text("✅ Авто-пост сгенерирован и опубликован в 📢 публичный канал.")
    except Exception as e:
        logger.error(f"/autopost failed: {e}")
        await status.edit_text(
            "❌ Не удалось опубликовать авто-пост. "
            "Проверьте, что бот — админ канала с правом публикации."
        )
