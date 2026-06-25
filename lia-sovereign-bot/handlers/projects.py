from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from database.db import async_session
from database.models import Project

router = Router()

class ProjectStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_desc = State()

@router.message(Command("projects"))
async def cmd_projects(message: Message):
    async with async_session() as session:
        stmt = select(Project).where(Project.user_id == message.from_user.id)
        result = await session.execute(stmt)
        projects = result.scalars().all()
        
        if not projects:
            text = "📁 <b>У тебя пока нет активных проектов.</b>\nСоздай свой первый проект, чтобы структурировать наше взаимодействие."
        else:
            text = "📁 <b>Твои рабочие пространства (Проекты):</b>\n\n"
            for p in projects:
                text += f"• <b>{p.name}</b>: {p.description or 'Без описания'}\n"
        
        builder = [[InlineKeyboardButton(text="➕ Создать проект", callback_data="project_create")]]
        kb = InlineKeyboardMarkup(inline_keyboard=builder)
        
        await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "project_create")
async def project_create_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(ProjectStates.waiting_for_name)
    await cb.message.answer("🖋 <b>Введите название проекта:</b>", parse_mode="HTML")
    await cb.answer()

@router.message(ProjectStates.waiting_for_name)
async def project_name_received(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(ProjectStates.waiting_for_desc)
    await message.answer("📝 <b>Введите краткое описание или цели проекта:</b>", parse_mode="HTML")

@router.message(ProjectStates.waiting_for_desc)
async def project_desc_received(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data['name']
    desc = message.text
    
    async with async_session() as session:
        new_project = Project(user_id=message.from_user.id, name=name, description=desc)
        session.add(new_project)
        await session.commit()
    
    await state.clear()
    await message.answer(f"✅ <b>Проект '{name}' успешно создан!</b>\nТеперь я буду помнить контекст этого пространства.", parse_mode="HTML")
