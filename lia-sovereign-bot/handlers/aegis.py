from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger
import base64
import io

from services.claude import claude_service
from utils.prompts import AEGIS_SCAN_PROMPT

router = Router()

class AegisStates(StatesGroup):
    waiting_for_scan = State()

@router.callback_query(F.data == "aegis_start")
async def aegis_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AegisStates.waiting_for_scan)
    await callback.message.edit_text(
        "🛡 <b>AEGIS PROTOCOL ACTIVATED</b>\n\n"
        "Пришли скриншот системы, лог или подозрительный файл для мгновенного анализа на угрозы.\n"
        "<i>(Отправь изображение для начала сканирования)</i>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AegisStates.waiting_for_scan, F.photo)
async def handle_aegis_photo(message: types.Message, state: FSMContext):
    # 1. Download photo
    photo = message.photo[-1]
    photo_file = await message.bot.get_file(photo.file_id)
    
    # Use io.BytesIO to avoid saving to disk
    photo_bytes = io.BytesIO()
    await message.bot.download_file(photo_file.file_path, photo_bytes)
    
    # 2. Convert to base64
    base64_image = base64.b64encode(photo_bytes.getvalue()).decode('utf-8')
    
    # 3. Show scanning action
    scan_msg = await message.answer("🔍 <b>SCANNING...</b>\nАнализирую нейронную структуру изображения на наличие аномалий.", parse_mode="HTML")
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # 4. Get response from Claude with vision
    # We need to update claude_service to handle vision
    try:
        response_text = await claude_service.get_vision_response(
            prompt=AEGIS_SCAN_PROMPT,
            image_base64=base64_image,
            image_media_type="image/jpeg"
        )
        await scan_msg.edit_text(response_text)
    except Exception as e:
        logger.error(f"Aegis scan error: {e}")
        await scan_msg.edit_text("❌ <b>SCAN ERROR</b>\nНе удалось завершить анализ. Проверьте системные логи.")
    
    await state.clear()

@router.message(AegisStates.waiting_for_scan)
async def aegis_wrong_format(message: types.Message):
    await message.answer("⚠️ Пожалуйста, отправь скриншот (изображение) для анализа Aegis.")