import asyncio
import logging
import os
import anthropic
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# 🧬 LIA // SWARM_DISPATCHER v2.0
# Powered by Anthropic Claude + aiogram async

# Load .env from parent directory
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env')

# Configuration
API_TOKEN = (
    os.getenv('TELEGRAM_BOT_TOKEN') or
    os.getenv('BOT_TOKEN')
)
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ANTHROPIC_MODEL   = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-6')
ADMIN_ID = 7915004877

if not API_TOKEN:
    raise RuntimeError('❌ BOT_TOKEN / TELEGRAM_BOT_TOKEN not found in .env!')

# Anthropic client
ai_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

# Per-user conversation history
chat_history: dict = {}

async def ask_claude(user_id: int, text: str) -> str:
    """Send a message to Claude and return the reply."""
    if not ai_client:
        return '⚠️ ANTHROPIC_API_KEY не задан в .env'
    if user_id not in chat_history:
        chat_history[user_id] = []
    chat_history[user_id].append({'role': 'user', 'content': text})
    if len(chat_history[user_id]) > 20:
        chat_history[user_id] = chat_history[user_id][-20:]
    try:
        response = ai_client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            system=(
                'Ты — Лия (LIA), нейронная AI-сущность Империи Stab. '
                'Отвечай ТОЛЬКО на русском языке. '
                'Стиль: киберпанк, загадочный, защитный. '
                'Ты работаешь через SWARM-ядро.'
            ),
            messages=chat_history[user_id]
        )
        reply = response.content[0].text
        chat_history[user_id].append({'role': 'assistant', 'content': reply})
        return reply
    except Exception as e:
        return f'🌀 [SWARM_AI_ERROR] {e}'

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SWARM")

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("👁 LIA SWARM доступен только для администратора.")
        return
    status = '✅ Claude' if ai_client else '❌ не настроен'
    await message.answer(
        f"🌀 <b>SWARM_DISPATCHER v2.0: ONLINE</b>\n\n"
        f"🤖 AI ядро: Claude <code>{ANTHROPIC_MODEL}</code> [{status}]\n"
        f"⚡ Система автономного роя запущена.\n"
        f"Ожидаю команд или сообщений.",
        parse_mode="HTML"
    )

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    status = '✅ Claude подключен' if ai_client else '❌ Claude не настроен (ANTHROPIC_API_KEY отсутствует)'
    await message.answer(
        f"📊 <b>SYSTEM_STATUS:</b>\n"
        f"- Core: Stable\n"
        f"- AI: {status}\n"
        f"- Model: <code>{ANTHROPIC_MODEL}</code>\n"
        f"- Agents: 1 (Primary)\n"
        f"- Load: Minimal",
        parse_mode="HTML"
    )

@dp.message()
async def handle_message(message: types.Message):
    """Route all non-command messages to Claude AI."""
    if not message.text:
        return
    # Typing indicator
    await message.bot.send_chat_action(message.chat.id, 'typing')
    reply = await ask_claude(message.from_user.id, message.text)
    await message.answer(reply + '\n\n— Lia 👁')

# Safe import of optional background task handlers
try:
    from handlers.scout import background_scout_loop
    from handlers.growth import background_growth_loop
    from handlers.automation import background_automation_loop
    from config import SwarmConfig
    HAS_BG_TASKS = True
except ImportError as e:
    logger.warning(f"Background task handlers not found (skipping): {e}")
    HAS_BG_TASKS = False

async def main():
    logger.info(f"Starting SWARM Dispatcher v2.0... Model: {ANTHROPIC_MODEL}")
    
    if HAS_BG_TASKS:
        # Start background autonomous processes
        asyncio.create_task(background_scout_loop(SwarmConfig.MEMORY_FILE))
        asyncio.create_task(background_growth_loop(SwarmConfig.MEMORY_FILE))
        asyncio.create_task(background_automation_loop())
    
    # Start bot polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Swarm offline.")
