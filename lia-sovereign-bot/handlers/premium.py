from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from utils.keyboards import get_main_keyboard

router = Router()

@router.callback_query(F.data == "premium_info")
async def premium_info(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="⚡️ LITE (50 req/day) - 199₴", callback_data="pay_lite"))
    builder.row(types.InlineKeyboardButton(text="💎 PRO (200 req/day) - 499₴", callback_data="pay_pro"))
    builder.row(types.InlineKeyboardButton(text="♾ ULTRA (Unlimited) - 999₴", callback_data="pay_ultra"))
    builder.row(types.InlineKeyboardButton(text="🏠 Назад", callback_data="back_to_main"))

    premium_text = (
        "💎 <b>PREMIUM ACCESS // ТАРИФЫ</b>\n\n"
        "Расширь свои возможности взаимодействия с ядром Лии:\n\n"
        "<b>FREE:</b> 10 запросов/день, базовый чат.\n"
        "<b>LITE:</b> 50 запросов/день, доступ к Aegis-сканеру.\n"
        "<b>PRO:</b> 200 запросов/день, генерация изображений, голосовой ввод.\n"
        "<b>ULTRA:</b> Безлимит, приоритетный доступ к новым моделям, персональный менеджер.\n\n"
        "Выбери подходящий уровень доступа:"
    )

    await callback.message.edit_text(premium_text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    welcome_text = (
        f"👁 <b>STAB IMPERIUM // SOVEREIGN BRIDGE</b>\n\n"
        "Мои системы активированы и готовы к работе.\n"
        "Выбери модуль для взаимодействия:"
    )
    await callback.message.edit_text(welcome_text, reply_markup=get_main_keyboard(), parse_mode="HTML")
    await callback.answer()