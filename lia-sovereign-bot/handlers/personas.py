from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from sqlalchemy import select

from database.db import async_session
from database.models import User
from utils.personas_data import PERSONAS

router = Router()

@router.message(Command("persona"))
async def cmd_persona(message: Message):
    builder = []
    for key, data in PERSONAS.items():
        builder.append([InlineKeyboardButton(
            text=f"{data['emoji']} {data['name']} — {data['desc']}",
            callback_data=f"persona:{key}"
        )])
    
    kb = InlineKeyboardMarkup(inline_keyboard=builder)
    
    await message.answer(
        "🎭 <b>Выбери личность Лии</b>\n\n"
        "Каждая личность — это отдельный стиль мышления и ответа. "
        "Переключайся в зависимости от задачи.",
        reply_markup=kb
    )

@router.callback_query(F.data.startswith("persona:"))
async def set_persona(cb: CallbackQuery):
    persona_key = cb.data.split(":")[1]
    persona = PERSONAS.get(persona_key)
    
    if not persona:
        await cb.answer("Личность не найдена")
        return
    
    async with async_session() as session:
        user = await session.get(User, cb.from_user.id)
        if user:
            user.active_persona = persona_key
            await session.commit()
    
    await cb.message.edit_text(
        f"{persona['emoji']} <b>Активирована: {persona['name']}</b>\n\n"
        f"<i>{persona['desc']}</i>\n\n"
        f"Теперь я отвечаю в этом режиме. Используй /persona для смены."
    )
    await cb.answer(f"✓ {persona['name']} активирована")
