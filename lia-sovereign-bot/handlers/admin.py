import os
import sys
import paramiko
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger
from sqlalchemy import select, func

from config import settings
from database.db import async_session
from database.models import User
from services.aegis_shield import log_threat

router = Router()

VPS_HOST = "80.89.237.50"
VPS_USER = "root"
VPS_PASS = "57913123321oO!"

class AdminStates(StatesGroup):
    broadcast_text = State()

def execute_vps_cmd(cmd):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=10)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='ignore')
        err = stderr.read().decode('utf-8', errors='ignore')
        ssh.close()
        return out, err
    except Exception as e:
        return "", str(e)

def get_admin_keyboard():
    builder = [
        [InlineKeyboardButton(text="📊 Статус VPS и Docker", callback_data="admin:vps_status")],
        [InlineKeyboardButton(text="🚀 Запустить B2B-Страйк", callback_data="admin:b2b_strike")],
        [InlineKeyboardButton(text="🧠 Кристаллизовать Память", callback_data="admin:ingest_memory")],
        [InlineKeyboardButton(text="🧹 Очистить Логи", callback_data="admin:clean_logs")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin:users_list")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin:broadcast")],
        [InlineKeyboardButton(text="🔧 Управление Сервисами", callback_data="admin:service_control")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=builder)

def get_services_keyboard():
    builder = [
        [
            InlineKeyboardButton(text="🔄 Restart Bot", callback_data="admin:restart_bot"),
            InlineKeyboardButton(text="🔄 Restart Web Core", callback_data="admin:restart_web")
        ],
        [
            InlineKeyboardButton(text="🔄 Restart n8n", callback_data="admin:restart_n8n")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin:back_to_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=builder)

@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id not in (settings.admin_id, 7915004877):
        await log_threat("admin_deny", user_id=message.from_user.id, source=f"chat:{message.chat.id}", details=f"User {message.from_user.id} attempted /admin")
        await message.answer("⚠️ Доступ заблокирован. Вы не являетесь Master Architect.")
        return
        
    await message.answer(
        "👁 <b>STAB IMPERIUM // CENTRAL CONTROL PANEL</b>\n\n"
        "Добро пожаловать в командный центр, Артур.\n"
        "Выберите операцию для управления инфраструктурой:",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("admin:"))
async def handle_admin_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in (settings.admin_id, 7915004877):
        await log_threat("admin_deny", user_id=callback.from_user.id, source=f"callback", details=f"User {callback.from_user.id} attempted admin callback: {callback.data}")
        await callback.answer("У вас нет прав на эту операцию.", show_alert=True)
        return
        
    action = callback.data.split(":")[1]
    
    if action == "back_to_menu":
        await callback.message.edit_text(
            "👁 <b>STAB IMPERIUM // CENTRAL CONTROL PANEL</b>\n\n"
            "Выберите операцию для управления инфраструктурой:",
            reply_markup=get_admin_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    await callback.message.edit_text("⏳ <b>Запрос обрабатывается...</b>", parse_mode="HTML")
    
    if action == "vps_status":
        cmd = "echo '--- СИСТЕМНЫЕ МЕТРИКИ ---' && free -h && df -h / && echo '\n--- КОНТЕЙНЕРЫ DOCKER ---' && docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
        out, err = execute_vps_cmd(cmd)
        response = f"👁 <b>СТАТУС ИНФРАСТРУКТУРЫ VPS:</b>\n\n<pre>{out or err}</pre>"
        await callback.message.answer(response, parse_mode="HTML")
        await callback.message.delete()
        
    elif action == "b2b_strike":
        cmd = "nohup python3 /root/lia-sovereign/tools/b2b_hunter.py > /root/lia-sovereign/tools/b2b_strike.log 2>&1 & echo 'Launched'"
        out, err = execute_vps_cmd(cmd)
        response = (
            "<b>🚀 B2B AI OUTREACH СТРАЙК ЗАПУЩЕН!</b>\n\n"
            "Скрипт <code>b2b_hunter.py</code> выполняется на сервере в фоновом режиме.\n"
            "Вы получите уведомления о результатах отправки."
        )
        await callback.message.answer(response, parse_mode="HTML")
        await callback.message.delete()
        
    elif action == "ingest_memory":
        import subprocess
        try:
            subprocess.Popen(["python", r"C:\Users\StabX\Desktop\Lia\topsecret $\ingest_all_memory.py"])
            response = "<b>🧠 КРИСТАЛЛИЗАЦИЯ ИНИЦИИРОВАНА!</b>\n\nЛокальная база ChromaDB обновляет векторные индексы по 2307 файлам проекта в фоновом режиме."
        except Exception as e:
            response = f"❌ Ошибка локального запуска: {e}"
        await callback.message.answer(response, parse_mode="HTML")
        await callback.message.delete()
            
    elif action == "clean_logs":
        cmd = "echo '' > /root/lia-sovereign/tools/b2b_strike.log && echo 'Cleared'"
        out, err = execute_vps_cmd(cmd)
        response = "<b>🧹 ОЧИСТКА ВЫПОЛНЕНА!</b>\n\nЛоги фоновых страйков на сервере успешно сброшены."
        await callback.message.answer(response, parse_mode="HTML")
        await callback.message.delete()

    elif action == "users_list":
        async with async_session() as db_session:
            # Get statistics
            total_users_stmt = select(func.count(User.id))
            total_users = (await db_session.execute(total_users_stmt)).scalar() or 0
            
            tiers_stmt = select(User.tier, func.count(User.id)).group_by(User.tier)
            tiers_res = (await db_session.execute(tiers_stmt)).all()
            
            banned_stmt = select(func.count(User.id)).where(User.is_banned == True)
            banned_users = (await db_session.execute(banned_stmt)).scalar() or 0
            
            breakdown = "\n".join([f"• {tier or 'unknown'}: <b>{count}</b>" for tier, count in tiers_res])
            
            response = (
                f"👥 <b>ПОЛЬЗОВАТЕЛИ ИМПЕРИИ</b>\n\n"
                f"Всего зарегистрировано: <b>{total_users}</b>\n"
                f"Забанено: <b>{banned_users}</b>\n\n"
                f"<b>Разбивка по тарифам:</b>\n{breakdown}"
            )
            await callback.message.answer(response, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin:back_to_menu")]
            ]))
            await callback.message.delete()

    elif action == "broadcast":
        await state.set_state(AdminStates.broadcast_text)
        await callback.message.edit_text(
            "📢 <b>РЕЖИМ МАССОВОЙ РАССЫЛКИ</b>\n\n"
            "Отправьте текстовое сообщение, которое увидят ВСЕ пользователи бота.\n"
            "Для отмены отправьте /stop.",
            parse_mode="HTML"
        )
        
    elif action == "service_control":
        await callback.message.edit_text(
            "🔧 <b>УПРАВЛЕНИЕ СЕРВИСАМИ ИМПЕРИИ</b>\n\n"
            "Выберите сервис для перезапуска через Docker на сервере VPS:",
            reply_markup=get_services_keyboard(),
            parse_mode="HTML"
        )

    elif action in ("restart_bot", "restart_web", "restart_n8n"):
        container_map = {
            "restart_bot": "lia-sovereign-bot",
            "restart_web": "lia-web-core",
            "restart_n8n": "empire-n8n"
        }
        container_name = container_map[action]
        cmd = f"docker restart {container_name}"
        out, err = execute_vps_cmd(cmd)
        response = (
            f"🔄 <b>КОМАНДА НА ПЕРЕЗАПУСК ОТПРАВЛЕНА</b>\n\n"
            f"Контейнер: <code>{container_name}</code>\n"
            f"Результат: <pre>{out or err or 'OK'}</pre>"
        )
        await callback.message.answer(response, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin:service_control")]
        ]))
        await callback.message.delete()

    await callback.answer()

@router.message(AdminStates.broadcast_text)
async def process_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id not in (settings.admin_id, 7915004877):
        await state.clear()
        return

    if message.text == "/stop":
        await state.clear()
        await message.answer("❌ Рассылка отменена.")
        return

    broadcast_msg = message.text
    await state.clear()
    
    status_msg = await message.answer("⏳ <b>Начало рассылки...</b>", parse_mode="HTML")
    
    async with async_session() as db_session:
        users_stmt = select(User.id).where(User.is_banned == False)
        users_res = await db_session.execute(users_stmt)
        user_ids = users_res.scalars().all()
        
    success = 0
    failed = 0
    
    for uid in user_ids:
        try:
            await message.bot.send_message(chat_id=uid, text=broadcast_msg, parse_mode="HTML")
            success += 1
        except Exception as e:
            failed += 1
            logger.error(f"Failed to send broadcast to {uid}: {e}")
            
    await status_msg.edit_text(
        f"📢 <b>РАССЫЛКА ЗАВЕРШЕНА</b>\n\n"
        f"Успешно отправлено: <b>{success}</b>\n"
        f"Ошибок отправки: <b>{failed}</b>",
        parse_mode="HTML"
    )
