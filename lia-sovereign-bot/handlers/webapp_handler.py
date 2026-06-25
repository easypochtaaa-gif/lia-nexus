import json
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from loguru import logger

from handlers.chat import chat_start
from handlers.aegis import aegis_start
from handlers.premium import premium_info

router = Router()

@router.message(Command("wallet"))
async def cmd_wallet(message: types.Message):
    """Ручная привязка кошелька через чат"""
    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "💎 <b>ПРИВЯЗКА WEB3 КОШЕЛЬКА</b>\n\n"
            "Отправь адрес своего кошелька командой:\n"
            "<code>/wallet ТВОЙ_АДРЕС</code>\n\n"
            "Поддерживаются:\n"
            "• USDT TRC-20 (T...) \n"
            "• Ethereum (0x...) \n"
            "• Solana (...)\n\n"
            "<i>Или используй кнопку «Кошелёк» в Mini App.</i>",
            parse_mode="HTML"
        )
        return

    wallet = args[1].strip()
    if len(wallet) < 20:
        await message.answer("❌ Некорректный адрес. Проверь и попробуй снова.")
        return

    from database.db import async_session
    from database.models import User
    from sqlalchemy import select

    async with async_session() as session:
        stmt = select(User).where(User.id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            was_connected = bool(user.wallet_address)
            user.wallet_address = wallet
            if not was_connected:
                user.xp = (user.xp or 0) + 100
                user.stab_coins = (user.stab_coins or 0) + 500
            await session.commit()
            logger.info(f"User {message.from_user.id} saved wallet via /wallet: {wallet}")
            bonus_msg = "\n🎁 <b>Бонус:</b> +100 XP, +500 StabaX!" if not was_connected else ""
            await message.answer(
                f"🔗 <b>КОШЕЛЁК ПРИВЯЗАН</b>\n"
                f"<code>{wallet}</code>{bonus_msg}",
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Профиль не найден. Сначала отправь /start.")

@router.message(F.web_app_data)
async def handle_webapp_data(message: types.Message, state: FSMContext):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get("action")
        
        logger.info(f"Received Web App data: {action} from user {message.from_user.id}")
        
        if action == "chat_start":
            # We need to simulate a callback query or call the function directly
            # Since chat_start expects a CallbackQuery, we might need to adapt it
            await message.answer("🧠 <b>NEURAL LINK ESTABLISHED</b>\nЛия слушает.", parse_mode="HTML")
            from handlers.chat import ChatStates
            await state.set_state(ChatStates.chatting)
            
        elif action == "aegis_start":
            from handlers.aegis import AegisStates
            await state.set_state(AegisStates.waiting_for_scan)
            await message.answer("🛡 <b>AEGIS PROTOCOL ACTIVATED</b>\nПришли скриншот для анализа.", parse_mode="HTML")
            
        elif action == "premium_info":
            # Similar to chat_start, we just send the message
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.row(types.InlineKeyboardButton(text="⚡️ LITE", callback_data="pay_lite"))
            builder.row(types.InlineKeyboardButton(text="💎 PRO", callback_data="pay_pro"))
            builder.row(types.InlineKeyboardButton(text="♾ ULTRA", callback_data="pay_ultra"))
            
            await message.answer("💎 <b>PREMIUM ACCESS</b>\nВыбери тариф:", reply_markup=builder.as_markup(), parse_mode="HTML")
        elif action == "wallet_connect":
            wallet = data.get("wallet")
            if wallet:
                from database.db import async_session
                from database.models import User
                from sqlalchemy import select
                async with async_session() as session:
                    stmt = select(User).where(User.id == message.from_user.id)
                    result = await session.execute(stmt)
                    user = result.scalar_one_or_none()
                    if user:
                        user.wallet_address = wallet
                        await session.commit()
                        logger.info(f"User {message.from_user.id} connected wallet {wallet}")
                        await message.answer(f"🔗 <b>WEB3 LINK ESTABLISHED</b>\nКошелек <code>{wallet}</code> успешно привязан.", parse_mode="HTML")
            else:
                await message.answer("❌ Ошибка привязки: адрес кошелька не получен.")
                
    except Exception as e:
        logger.error(f"Error processing Web App data: {e}")
        await message.answer("❌ Ошибка при обработке данных из Mini App.")
