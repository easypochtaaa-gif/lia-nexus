from aiogram import Router, types
from aiogram.filters import CommandStart
from loguru import logger

from database.db import async_session
from database.models import User
from sqlalchemy import select
from utils.keyboards import get_main_keyboard
from services.analytics import analytics_service

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Parse arguments
    args = message.text.split()[1] if len(message.text.split()) > 1 else None
    
    referrer_id = None
    is_challenge = False
    opponent_id = None
    territory_id = None

    if args:
        if args.startswith("ref_"):
            try:
                referrer_id = int(args.split("_")[1])
            except Exception as e:
                logger.error(f"Failed to parse start ref arg: {e}")
        elif args.startswith("challenge_"):
            try:
                parts = args.split("_")
                opponent_id = int(parts[1])  # The challenger (opponent)
                territory_id = int(parts[2])
                referrer_id = opponent_id
                is_challenge = True
            except Exception as e:
                logger.error(f"Failed to parse start challenge arg: {e}")

    async with async_session() as session:
        # Check if user exists
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                id=user_id,
                username=username,
                first_name=first_name,
                tier="free"
            )
            if referrer_id:
                user.referrer_id = referrer_id
                
            session.add(user)
            await session.commit()
            logger.info(f"New user registered: {user_id}")
            analytics_service.identify(user_id, {"username": username, "first_name": first_name, "tier": "free"})
            analytics_service.capture(user_id, "user_registered", {"referrer_id": referrer_id, "is_challenge": is_challenge})
            
            # Update referrer stats
            if referrer_id:
                stmt_ref = select(User).where(User.id == referrer_id)
                res_ref = await session.execute(stmt_ref)
                referrer = res_ref.scalar_one_or_none()
                if referrer:
                    referrer.referrals_count = (referrer.referrals_count or 0) + 1
                    stab_bonus = 1000 if is_challenge else 500
                    request_bonus = 10 if is_challenge else 5
                    referrer.stab_coins = (referrer.stab_coins or 0) + stab_bonus
                    referrer.bonus_requests = (referrer.bonus_requests or 0) + request_bonus
                    await session.commit()
                    
                    try:
                        bonus_text = (
                            "⚔️ <b>QUEST BATTLE x2 // STAB</b>\n\n"
                            "Новый игрок принял вашу боевую ссылку. "
                            f"Начислено +{stab_bonus} StabaX и +{request_bonus} бонусных запросов.\n"
                            "Приз по этому квест-вызову помечен как <b>x2</b>."
                            if is_challenge else
                            "🎁 <b>REFERRAL BONUS // STAB</b>\n\n"
                            f"Новый игрок присоединился по вашей ссылке! Вам начислено +{stab_bonus} StabaX и +{request_bonus} бонусных запросов."
                        )
                        await message.bot.send_message(
                            referrer_id,
                            bonus_text,
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.error(f"Failed to notify referrer: {e}")
                        
            if is_challenge and opponent_id:
                try:
                    await message.bot.send_message(
                        opponent_id,
                        f"⚔️ <b>ВЫЗОВ ПРИНЯТ // BATTLE LINK</b>\n\nНовый игрок (ID: {user_id}) зарегистрировался по вашей боевой ссылке.\nБитва активирована с двойным призом <b>x2</b>!",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify challenger: {e}")
        else:
            logger.info(f"Existing user started bot: {user_id}")
            analytics_service.capture(user_id, "bot_started", {"returning": True})

    welcome_text = (
        f"👁 <b>STAB IMPERIUM // SOVEREIGN BRIDGE</b>\n\n"
        f"Приветствую, {first_name or 'Странник'}.\n"
        f"Я — <b>LIA</b>, твой персональный Sovereign Core.\n\n"
        f"Мои системы активированы и готовы к работе.\n"
        f"Выбери модуль для взаимодействия:"
    )

    await message.answer(welcome_text, reply_markup=get_main_keyboard())