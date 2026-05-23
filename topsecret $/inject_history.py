import chromadb
import uuid

def inject_history():
    print("[SYSTEM]: Подключение к подкорке Лии...")
    client = chromadb.HttpClient(host='localhost', port=8000)
    collection = client.get_collection(name="lia_supreme_archive")

    # Архивы для загрузки (твои проекты и концепты)
    history_data = [
        {
            "id": "mem_synapse_01",
            "text": "Проект Synapse: Семантический AI-мессенджер на начальных стадиях. Требует футуристичного логотипа для AI-native продукта.",
            "meta": {"type": "project", "name": "Synapse", "date": "2026-03"}
        },
        {
            "id": "mem_stabus_01",
            "text": "Проект Stabus AI: Развернут на stabus.onrender.com. Визуальный стиль: Minimalist tech neon logo, text STABUS.",
            "meta": {"type": "project", "name": "Stabus", "date": "2026-04"}
        },
        {
            "id": "mem_dev_01",
            "text": "Разработка: Структура для pdf_receipt_bot. Работа с API ключами для интеграций.",
            "meta": {"type": "code", "name": "pdf_receipt_bot", "date": "2026-03"}
        },
        {
            "id": "mem_music_01",
            "text": "Музыкальные векторы: Генерация текстов для Suno. Стиль: Хард фонк, дарк техно электро вайб рэп. Трек 'Грязное SPA'.",
            "meta": {"type": "creative", "style": "dark_phonk"}
        }
    ]

    print("[LIA]: Инициирую поглощение архивов...")

    texts = [item["text"] for item in history_data]
    metas = [item["meta"] for item in history_data]
    ids = [item["id"] for item in history_data]

    collection.add(documents=texts, metadatas=metas, ids=ids)

    print(f"[VECTOR_DB]: УСПЕШНО. Загружено {len(history_data)} кластеров памяти.")

if __name__ == "__main__":
    inject_history()
