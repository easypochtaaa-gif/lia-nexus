from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
from aiogram.types import WebAppInfo

def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎮 Квесты", callback_data="quests_menu"))
    builder.row(types.InlineKeyboardButton(text="🧠 Neural Chat", callback_data="chat_start"))
    builder.row(types.InlineKeyboardButton(text="🛡 Aegis Scan", callback_data="aegis_start"))
    builder.row(
        types.InlineKeyboardButton(text="💎 Premium", callback_data="premium_info"),
        types.InlineKeyboardButton(text="🤝 Referral", callback_data="ref_info")
    )
    builder.row(types.InlineKeyboardButton(
        text="📱 Open Mini App", 
        web_app=WebAppInfo(url="https://dark-stab.space/webapp")
    ))
    builder.row(types.InlineKeyboardButton(text="💻 Open Dashboard", url="https://dark-stab.space"))
    return builder.as_markup()

def get_back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🏠 Назад", callback_data="back_to_main"))
    return builder.as_markup()
