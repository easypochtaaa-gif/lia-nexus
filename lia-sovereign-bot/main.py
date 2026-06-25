import asyncio
import sys
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

from config import settings
from database.db import init_db
from handlers import start, chat, aegis, premium, referral, webapp_handler, personas, projects, admin, security, quests, channels, synapse

async def seed_quests():
    from database.db import async_session
    from database.models import Quest
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(select(Quest))
        quests = result.scalars().all()

        if not quests:
            logger.info("Seeding initial RPG quests into database...")
            initial_quests = [
                Quest(
                    id=1,
                    title="Подключить Кошелек",
                    description="Свяжите Web3 кошелек (MetaMask/Phantom) с профилем для синхронизации активов.",
                    reward_xp=100,
                    reward_stab=500,
                    is_active=True
                ),
                Quest(
                    id=2,
                    title="Первый Контакт",
                    description="Проведите первую диалоговую сессию с суверенным разумом LIA.",
                    reward_xp=250,
                    reward_stab=100,
                    is_active=True
                ),
                Quest(
                    id=3,
                    title="Пригласить Рекрута",
                    description="Пригласите 1 друга в Империю по вашей уникальной реферальной ссылке.",
                    reward_xp=500,
                    reward_stab=1000,
                    is_active=True
                )
            ]
            session.add_all(initial_quests)
            await session.commit()
            logger.info("RPG quests successfully seeded.")

async def on_startup():
    from services.analytics import analytics_service
    logger.info(f"PostHog analytics enabled: {analytics_service.enabled}")
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized.")
    try:
        await seed_quests()
    except Exception as e:
        logger.error(f"Failed to seed quests: {e}")

async def main():
    # Configure logging
    logger.remove()
    logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

    # Initialize bot and dispatcher
    bot = Bot(token=settings.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # Register startup handler
    dp.startup.register(on_startup)

    # Include routers — ORDER MATTERS: specific commands first, catch-all chat last
    dp.include_router(start.router)       # /start
    dp.include_router(admin.router)       # /admin (must be before chat catch-all!)
    dp.include_router(aegis.router)       # /aegis
    dp.include_router(premium.router)     # /premium etc
    dp.include_router(referral.router)    # /referral
    dp.include_router(webapp_handler.router)  # /wallet + webapp data
    dp.include_router(personas.router)
    dp.include_router(projects.router)
    dp.include_router(security.router)     # /security /sec /osint /ble
    dp.include_router(quests.router)       # /quests /quest_apply /my_quests
    dp.include_router(channels.router)     # /post (публичный) /whisper (личный)
    dp.include_router(synapse.router)      # /synapse — Triple Core дебаты
    dp.include_router(chat.router)        # catch-all: must be LAST

    # ── HTTP API Server for n8n integration ──
    import api_server
    api_server.bot_instance = bot
    api_app = api_server.create_app()
    api_runner = web.AppRunner(api_app)
    await api_runner.setup()
    api_site = web.TCPSite(api_runner, "0.0.0.0", 8080)
    await api_site.start()
    logger.info("LIA HTTP API server started on 0.0.0.0:8080")

    # ── Auto-post scheduler (APScheduler) ──
    from services.scheduler import start_scheduler, stop_scheduler
    try:
        start_scheduler(bot)
    except Exception as e:
        logger.error(f"Failed to start auto-post scheduler: {e}")

    logger.info("LIA Sovereign Core starting...")

    try:
        await dp.start_polling(bot)
    finally:
        from services.analytics import analytics_service
        analytics_service.shutdown()
        stop_scheduler()
        await api_runner.cleanup()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("LIA Sovereign Core stopped.")