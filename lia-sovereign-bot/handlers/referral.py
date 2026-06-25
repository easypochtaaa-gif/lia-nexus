from aiogram import Bot, Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.db import async_session
from database.models import User
from sqlalchemy import select

router = Router()


async def _build_referral_text(user_id: int, bot: Bot) -> tuple[str, types.InlineKeyboardMarkup]:
    async with async_session() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        ref_count = user.referrals_count if user else 0
        bonus = user.bonus_requests if user else 0
        stab = user.stab_coins if user else 0

    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    battle_link = f"https://t.me/{bot_info.username}?start=challenge_{user_id}_0"

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📢 Поделиться", switch_inline_query=f"Лия — твой персональный ИИ. Присоединяйся: {ref_link}"))
    builder.row(types.InlineKeyboardButton(text="⚔️ Позвать на квест-битву x2", switch_inline_query=f"Вызываю тебя на квест-битву LIA за приз x2: {battle_link}"))
    builder.row(types.InlineKeyboardButton(text="🏠 Назад", callback_data="back_to_main"))

    ref_text = (
        "🤝 <b>REFERRAL SYSTEM // STAB NETWORK</b>\n\n"
        "Приглашай друзей и получай бонусы к лимитам запросов.\n"
        "Если новый игрок зайдёт по боевой ссылке, вызов фиксируется как квест-битва с призом <b>x2</b>.\n\n"
        f"👤 <b>Приглашено:</b> {ref_count}\n"
        f"🎁 <b>Бонусные запросы:</b> {bonus}\n"
        f"🪙 <b>StabaX:</b> {stab}\n\n"
        "За обычное приглашение начисляется +500 StabaX.\n"
        "За приглашение через квест-битву начисляется +1000 StabaX и пометка x2.\n\n"
        f"🔗 <b>Обычная ссылка:</b>\n<code>{ref_link}</code>\n\n"
        f"⚔️ <b>Боевая ссылка x2:</b>\n<code>{battle_link}</code>"
    )

    return ref_text, builder.as_markup()


@router.message(Command("referral", "ref", "battle", "challenge"))
async def ref_command(message: types.Message):
    ref_text, keyboard = await _build_referral_text(message.from_user.id, message.bot)
    await message.answer(ref_text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data == "ref_info")
async def ref_info(callback: types.CallbackQuery):
    ref_text, keyboard = await _build_referral_text(callback.from_user.id, callback.message.bot)
    await callback.message.edit_text(ref_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()