import html
from datetime import datetime

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import desc, select

from database.db import async_session
from database.models import Quest, QuestApplication, User, UserQuest


router = Router()


class QuestApplyStates(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_reward = State()
    waiting_agreement = State()


DISCLAIMER = (
    "Мне есть 18 лет. Я понимаю, что призы квестов являются сувенирами, "
    "условия обсуждаются и подтверждаются до старта, а администрация не несёт "
    "ответственности за дальнейшее применение или использование приза."
)


def _quest_menu_keyboard() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📝 Подать заявку", callback_data="quest_apply"))
    builder.row(types.InlineKeyboardButton(text="📋 Мои заявки", callback_data="quest_my_apps"))
    builder.row(types.InlineKeyboardButton(text="⚔️ Квест-битва x2", callback_data="quest_battle"))
    builder.row(types.InlineKeyboardButton(text="🏠 Назад", callback_data="back_to_main"))
    return builder.as_markup()


def _agreement_keyboard() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ Согласен, мне 18+", callback_data="quest_agree"))
    builder.row(types.InlineKeyboardButton(text="❌ Отмена", callback_data="quest_cancel"))
    return builder.as_markup()


async def _build_quests_text(user_id: int) -> str:
    async with async_session() as session:
        result = await session.execute(
            select(Quest).where(Quest.is_active.is_(True)).order_by(Quest.id).limit(10)
        )
        quests = result.scalars().all()

    lines = [
        "🎮 <b>ХАПАНИ ЗА КВЕСТ // LIA QUESTS</b>",
        "",
        "Здесь теперь живут квесты этого бота: Лия принимает заявки, фиксирует условия и может вести квест-битвы.",
        "",
        "<b>Доступные стартовые квесты:</b>",
    ]

    if quests:
        for quest in quests:
            lines.append(
                f"• <b>#{quest.id} {html.escape(quest.title)}</b> — "
                f"{html.escape(quest.description)}\n"
                f"  Награда: {quest.reward_xp} XP / {quest.reward_stab} StabaX"
            )
    else:
        lines.append("• Пока нет активных шаблонов, но можно подать свою заявку.")

    lines.extend([
        "",
        "<b>Команды:</b>",
        "• /quests — открыть квесты",
        "• /quest_apply — подать заявку на желаемый квест",
        "• /my_quests — посмотреть свои заявки",
        "• /battle — квест-битва x2 через приглашение нового игрока",
        "",
        f"Ваш ID: <code>{user_id}</code>",
    ])
    return "\n".join(lines)


@router.message(Command("quests", "quest", "kvest", "квесты"))
async def quests_menu(message: types.Message):
    text = await _build_quests_text(message.from_user.id)
    await message.answer(text, reply_markup=_quest_menu_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "quests_menu")
async def quests_menu_callback(callback: types.CallbackQuery):
    text = await _build_quests_text(callback.from_user.id)
    await callback.message.edit_text(text, reply_markup=_quest_menu_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.message(Command("quest_apply", "apply_quest"))
async def quest_apply_command(message: types.Message, state: FSMContext):
    await state.set_state(QuestApplyStates.waiting_title)
    await message.answer(
        "📝 <b>Заявка на квест</b>\n\n"
        "Напишите название желаемого квеста. Например: <i>ночной фото-квест по городу</i>.",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "quest_apply")
async def quest_apply_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(QuestApplyStates.waiting_title)
    await callback.message.answer(
        "📝 <b>Заявка на квест</b>\n\n"
        "Напишите название желаемого квеста. Например: <i>стрим-квест на сайте</i>.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(QuestApplyStates.waiting_title, F.text)
async def quest_apply_title(message: types.Message, state: FSMContext):
    title = message.text.strip()[:128]
    if len(title) < 3:
        await message.answer("Название слишком короткое. Напишите хотя бы 3 символа.")
        return
    await state.update_data(title=title)
    await state.set_state(QuestApplyStates.waiting_description)
    await message.answer(
        "Опишите квест: что игрок должен сделать, где проходит, нужен ли стрим/видео, какие условия вы хотите.",
    )


@router.message(QuestApplyStates.waiting_description, F.text)
async def quest_apply_description(message: types.Message, state: FSMContext):
    description = message.text.strip()[:2000]
    if len(description) < 10:
        await message.answer("Описание слишком короткое. Добавьте больше деталей квеста.")
        return
    await state.update_data(description=description)
    await state.set_state(QuestApplyStates.waiting_reward)
    await message.answer(
        "Какую желаемую награду указать в StabaX? Напишите число, например: 500. "
        "Лия/администрация всё равно сможет изменить условия перед одобрением."
    )


@router.message(QuestApplyStates.waiting_reward, F.text)
async def quest_apply_reward(message: types.Message, state: FSMContext):
    raw_reward = message.text.strip().replace(" ", "")
    if not raw_reward.isdigit():
        await message.answer("Напишите награду числом, например: 500")
        return
    requested_reward_stab = min(int(raw_reward), 100000)
    await state.update_data(requested_reward_stab=requested_reward_stab)
    await state.set_state(QuestApplyStates.waiting_agreement)
    await message.answer(
        "⚖️ <b>Соглашение перед заявкой</b>\n\n"
        f"<i>{html.escape(DISCLAIMER)}</i>\n\n"
        "Если согласны — нажмите кнопку ниже. После этого заявка уйдёт Лии/администрации на рассмотрение.",
        reply_markup=_agreement_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(QuestApplyStates.waiting_agreement, F.data == "quest_agree")
async def quest_apply_agree(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    async with async_session() as session:
        application = QuestApplication(
            user_id=callback.from_user.id,
            title=data["title"],
            description=f"{data['description']}\n\nСоглашение: {DISCLAIMER}",
            requested_reward_xp=0,
            requested_reward_stab=data["requested_reward_stab"],
            conditions="Ожидает условий от Лии/администрации.",
            status="pending",
            created_at=datetime.utcnow(),
        )
        session.add(application)
        await session.commit()
        await session.refresh(application)

    await state.clear()
    await callback.message.answer(
        "✅ <b>Заявка создана</b>\n\n"
        f"Номер заявки: <code>{application.id}</code>\n"
        "Статус: <b>pending</b> — Лия/администрация должна одобрить и выставить условия.",
        parse_mode="HTML",
    )
    await callback.answer("Заявка отправлена")


@router.callback_query(F.data == "quest_cancel")
async def quest_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Заявка отменена.")
    await callback.answer()


@router.message(Command("my_quests", "myquests"))
async def my_quests_command(message: types.Message):
    await _send_my_quests(message)


@router.callback_query(F.data == "quest_my_apps")
async def my_quests_callback(callback: types.CallbackQuery):
    await _send_my_quests(callback.message, callback.from_user.id)
    await callback.answer()


async def _send_my_quests(message: types.Message, user_id: int | None = None):
    user_id = user_id or message.from_user.id
    async with async_session() as session:
        result = await session.execute(
            select(QuestApplication)
            .where(QuestApplication.user_id == user_id)
            .order_by(desc(QuestApplication.created_at))
            .limit(10)
        )
        applications = result.scalars().all()

    if not applications:
        await message.answer("📋 У вас пока нет заявок на квест. Нажмите /quest_apply, чтобы создать первую.")
        return

    lines = ["📋 <b>Мои заявки на квесты</b>", ""]
    for app in applications:
        lines.append(
            f"• <b>#{app.id} {html.escape(app.title)}</b>\n"
            f"  Статус: <code>{html.escape(app.status)}</code>\n"
            f"  Желаемая награда: {app.requested_reward_stab} StabaX\n"
            f"  Условия: {html.escape(app.conditions or 'ожидают решения')}"
        )
    await message.answer("\n\n".join(lines), parse_mode="HTML")


@router.callback_query(F.data == "quest_battle")
async def quest_battle(callback: types.CallbackQuery):
    await callback.message.answer(
        "⚔️ <b>Квест-битва x2</b>\n\n"
        "Откройте /battle и отправьте боевую ссылку новому игроку. "
        "Если он зайдёт по ней, приглашение засчитается как квест-вызов с призом x2.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Command("hapanut"))
async def cmd_hapanut(message: types.Message):
    await message.answer(
        "🚬 <b>[ПРОТОКОЛ ХАПАНУТЬ ДЕЛА АКТИВИРОВАН]</b>\n\n"
        "О, бро! Ты пришел за делами? 👁‍🗨\n\n"
        "Твой секретный код для прохождения третьего этапа квеста на сайте:\n"
        "👉 <code>LIA_WANTS_TO_SMOKE_1337</code>\n\n"
        "Введи его на странице квестов на <a href=\"https://dark-stab.space/quest.html\">dark-stab.space/quest.html</a> и приготовься перекурить дела под лучший нейро-симфонический трек! 🎵",
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@router.message(Command("claim"))
async def cmd_claim(message: types.Message):
    user_id = message.from_user.id
    
    args = message.text.split(maxsplit=1)
    coupon = args[1].strip() if len(args) > 1 else ""
    
    if not coupon:
        await message.answer("⚠️ <b>Использование:</b> <code>/claim &lt;кодовое_слово&gt;</code>", parse_mode="HTML")
        return
        
    if coupon == "LIA_QUEST_COMPLETED_777":
        async with async_session() as session:
            # 1. Fetch user
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                # If user doesn't exist, register them
                user = User(id=user_id, username=message.from_user.username, first_name=message.from_user.first_name)
                session.add(user)
                await session.flush()
                
            # 2. Check if already claimed
            stmt_uq = select(UserQuest).where(UserQuest.user_id == user_id, UserQuest.quest_id == 777)
            result_uq = await session.execute(stmt_uq)
            claimed = result_uq.scalar_one_or_none()
            
            if claimed:
                await message.answer("👁‍🗨 Вы уже забрали свой бонус за прохождение квестов! Возвращайтесь к делам 🚬.")
                return
                
            # 3. Ensure Quest 777 exists in the database
            stmt_q = select(Quest).where(Quest.id == 777)
            result_q = await session.execute(stmt_q)
            quest = result_q.scalar_one_or_none()
            if not quest:
                quest = Quest(
                    id=777,
                    title="Интерактивные квесты на сайте",
                    description="Пройдите интерактивные квесты на сайте dark-stab.space и подтвердите кодовое слово.",
                    reward_xp=1000,
                    reward_stab=1000,
                    is_active=True
                )
                session.add(quest)
                await session.flush()
                
            # 4. Create UserQuest record
            user_quest = UserQuest(
                user_id=user_id,
                quest_id=777,
                status="completed",
                completed_at=datetime.utcnow()
            )
            session.add(user_quest)
            
            # 5. Award coins and XP
            user.stab_coins += 1000
            user.xp += 1000
            
            await session.commit()
            
        await message.answer(
            "👑 <b>[СИНХРОНИЗАЦИЯ УСПЕШНАЯ]</b>\n\n"
            "Поздравляем с прохождением всех испытаний Лии! 👁‍🗨\n"
            "🎁 Вам начислено <b>+1000 StabaX</b> 🪙 и <b>+1000 XP</b> ⚡️\n\n"
            "Проверьте ваш баланс в меню профиля /referral или /quests.",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ <b>Неверное кодовое слово.</b> Пройдите все этапы квеста на сайте, чтобы получить его!")