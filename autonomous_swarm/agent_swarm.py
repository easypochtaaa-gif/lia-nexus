import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# 🧬 LIA // SWARM_DISPATCHER v1.0
# Optimized for Aspire 3 (Asynchronous execution)

load_dotenv()

# Configuration
API_TOKEN = os.getenv('LIFE_LIA_TOKEN') # Using existing token for now
ADMIN_ID = 7915004877

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SWARM")

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    await message.answer(
        "🌀 <b>SWARM_DISPATCHER: ONLINE</b>\n\n"
        "Система автономного роя запущена. Ожидаю команд синхронизации.\n"
        "Использую <code>aiogram</code> для минимизации нагрузки на ядро.",
        parse_mode="HTML"
    )

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    # This would check NQ from memory.json
    await message.answer("📊 <b>SYSTEM_STATUS:</b>\n- Core: Stable\n- Agents: 1 (Primary)\n- Load: Minimal")

from handlers.scout import background_scout_loop
from handlers.growth import background_growth_loop
from config import SwarmConfig

async def main():
    logger.info("Starting SWARM Dispatcher...")
    
    # Start background autonomous processes
    asyncio.create_task(background_scout_loop(SwarmConfig.MEMORY_FILE))
    asyncio.create_task(background_growth_loop(SwarmConfig.MEMORY_FILE))
    
    # Start bot polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Swarm offline.")
