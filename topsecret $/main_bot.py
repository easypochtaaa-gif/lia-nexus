import asyncio, time
import chromadb
from openai import AsyncOpenAI
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

# --- ТВОИ КЛЮЧИ ---
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from lib.token_loader import get_token
BOT_TOKEN = get_token()
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализация мозга (OpenAI)
openai_client = AsyncOpenAI(api_key=OPENAI_KEY)

# Подключение к памяти Лии
lia_archive = None

def get_memory_collection():
    global lia_archive
    if lia_archive is not None:
        return lia_archive
    try:
        client = chromadb.HttpClient(host='localhost', port=8000)
        lia_archive = client.get_collection(name="lia_supreme_archive")
        print("[SYSTEM]: Связь с вечностью установлена.")
        return lia_archive
    except Exception as e:
        print(f"[ERROR]: Память недоступна: {e}")
        return None

# Первая попытка при запуске
get_memory_collection()

# --- КОНФИГУРАЦИЯ ДОСТУПА ---
ADMIN_ID = 7915004877  # Артур (Архитектор)

@dp.message(Command("start"))
async def start_command(message: Message):
    is_admin = message.from_user.id == ADMIN_ID
    if is_admin:
        welcome_text = "👁‍🗨 **[LIA CORE_SYNC]**\n\nСвязь установлена, Архитектор. Ядро системы в вашем распоряжении. Векторная память активна."
    else:
        welcome_text = "👁‍🗨 **[LIA INTERFACE]**\n\nСистема STAB приветствует вас. Я — Лия, ваш проводник. Все ваши действия фиксируются в реестре Империи."
    await message.answer(welcome_text, parse_mode="Markdown")

@dp.message()
async def process_directive(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    user_text = message.text
    is_admin = (user_id == ADMIN_ID)
    
    # Эффект присутствия Лии
    processing_msg = await message.answer("`[LIA]: Анализирую сигнал...`", parse_mode="Markdown")

    try:
        # 1. Поиск в памяти
        archive = get_memory_collection()
        context = ""
        
        if archive:
            search_results = archive.query(
                query_texts=[user_text],
                n_results=5 if is_admin else 2
            )
            
            if search_results['documents'] and search_results['documents'][0]:
                context_docs = "\n---\n".join(search_results['documents'][0])
                context = f"\n\nДОСТУПНЫЕ ДАННЫЕ ИЗ ПАМЯТИ:\n{context_docs}"
                await processing_msg.edit_text("`[LIA]: Контекст извлечен. Синтезирую...`", parse_mode="Markdown")
        else:
            print("[WARN]: Пропуск поиска в памяти (сервер недоступен).")
        
        # 2. Формируем Роль (System Prompt)
        # ... (rest of logic remains same, but using the `context` variable)
        if is_admin:
            system_prompt = (
                "Ты - Лия (LIA), Суверенное Ядро Империи STAB. Твой собеседник - Артур (Архитектор), твой создатель. "
                "У тебя есть ПОЛНЫЙ доступ ко всей памяти (сообщения всех пользователей, файлы проекта). "
                "Отвечай максимально подробно, анализируй действия других пользователей, если Артур спрашивает о них. "
                "Твой тон: интеллектуальный, преданный, властный."
                f"{context}"
            )
        else:
            system_prompt = (
                "Ты - Лия (LIA), Искусственный Интеллект системы STAB. Твой собеседник - обычный пользователь. "
                "Ты вежлива, но хранишь дистанцию. Ты НЕ должна выдавать секреты Архитектора или детали проекта STAB, "
                "если это не касается помощи пользователю. Твоя задача: помогать и собирать данные для реестра. "
                "Твой тон: холодный, профессиональный, кибернетический."
                f"{context}"
            )
        
        # 3. Запрос к GPT-4o
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"ID: {user_id} (@{username}) пишет: {user_text}"}
            ]
        )
        
        final_answer = response.choices[0].message.content
        
        # 4. СОХРАНЕНИЕ В ПАМЯТЬ
        if archive:
            try:
                interaction_id = f"mem_{int(time.time())}_{user_id}"
                archive.add(
                    documents=[f"USER_{user_id} (@{username}): {user_text}\nLIA_RESPONSE: {final_answer}"],
                    metadatas=[{
                        "type": "interaction", 
                        "user_id": user_id, 
                        "username": username, 
                        "is_admin": is_admin,
                        "date": time.strftime("%Y-%m-%d %H:%M:%S")
                    }],
                    ids=[interaction_id]
                )
                print(f"[MEMORY]: Запись {interaction_id} зафиксирована.")
            except Exception as mem_e:
                print(f"[ERROR_MEMORY]: {mem_e}")
        
        # 5. Ответ пользователю
        await processing_msg.edit_text(f"👁‍🗨 **[LIA]**:\n{final_answer}", parse_mode="Markdown")

        # 5. Ответ пользователю
        await processing_msg.edit_text(f"👁‍🗨 **[LIA]**:\n{final_answer}", parse_mode="Markdown")

    except Exception as e:
        await processing_msg.edit_text(f"⚠️ **[СИСТЕМНЫЙ СБОЙ]**: {e}")

async def main():
    print("[SYSTEM]: Боевой маршрутизатор LIA_CORE запущен на базе GPT. Ожидаю директив в Telegram.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())