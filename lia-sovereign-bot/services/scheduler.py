"""
Авто-постинг по расписанию через APScheduler.

Раз в сутки (по умолчанию 10:00) генерирует короткий пост-новость / обзор по
экосистеме STAB / SYNAPSE через LLM и публикует его в публичный канал
(`settings.public_channel_id`).

Контролируется флагом и временем в конфиге (с дефолтами), бот должен быть
администратором канала с правом публикации.
"""
import random
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import settings
from services.claude import claude_service

# Темы для авто-постов (ротация)
POST_TOPICS = [
    "короткая новость дня про экосистему STAB-Империи и валюту StabaX",
    "мини-обзор механики SYNAPSE Triple Core (дебаты ИИ-ядер и Арбитр JEMA)",
    "совет дня: как заработать STAB (рефералы, кошелёк, квест /claim)",
    "тизер про прокачку навыков в Дереве Талантов за STAB",
    "мотивационный пост про симбиоз человека и цифрового разума LIA",
]

POST_SYSTEM_PROMPT = (
    "Ты JEMA — голос экосистемы LIA Sovereign Core (СТАБ-Империя + SYNAPSE). "
    "Напиши КОРОТКИЙ пост для Telegram-канала (3-5 предложений, по-русски), "
    "в киберпанк-стиле 2040 с неоновой подачей и 1-3 эмодзи. Без хэштегов-простыней "
    "(максимум 1-2 хэштега в конце). Тон уверенный, призывающий присоединиться к "
    "СТАБ-Империи."
)

# Глобальный планировщик
_scheduler: AsyncIOScheduler | None = None


async def _generate_post() -> str:
    topic = random.choice(POST_TOPICS)
    prompt = f"Тема поста: {topic}."
    text = await claude_service.get_response(prompt, history=None, system_prompt=POST_SYSTEM_PROMPT)
    return (text or "").strip()


async def publish_scheduled_post(bot):
    """Генерирует и публикует пост в публичный канал."""
    channel_id = settings.public_channel_id
    if not channel_id:
        logger.warning("Auto-post skipped: public_channel_id is not set.")
        return
    try:
        text = await _generate_post()
        if not text:
            logger.warning("Auto-post skipped: empty generated text.")
            return
        await bot.send_message(chat_id=channel_id, text=text, parse_mode="HTML")
        logger.info(f"Auto-post published to public channel {channel_id}.")
    except Exception as e:
        logger.error(f"Auto-post failed for channel {channel_id}: {e}")


def start_scheduler(bot) -> AsyncIOScheduler:
    """Запускает планировщик авто-постинга. Возвращает экземпляр scheduler."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    if not getattr(settings, "autopost_enabled", True):
        logger.info("Auto-posting disabled via config (autopost_enabled=False).")
        return None

    hour = getattr(settings, "autopost_hour", 10)
    minute = getattr(settings, "autopost_minute", 0)

    scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")
    scheduler.add_job(
        publish_scheduled_post,
        trigger="cron",
        hour=hour,
        minute=minute,
        args=[bot],
        id="daily_stab_post",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info(f"Auto-post scheduler started (daily at {hour:02d}:{minute:02d} Europe/Kyiv).")
    return scheduler


def stop_scheduler():
    global _scheduler
    if _scheduler is not None:
        try:
            _scheduler.shutdown(wait=False)
        except Exception as e:
            logger.debug(f"Scheduler shutdown error: {e}")
        _scheduler = None
