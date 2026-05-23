"""
ingest_all_memory.py
Сканирует всё дерево проекта Lia и загружает текстовые файлы
в векторную память ChromaDB (коллекция lia_supreme_archive).
Лия сможет вспомнить любой файл по смыслу запроса.
"""
import os
import chromadb
import hashlib

# ─── Настройки ───
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ALLOWED_EXTENSIONS = {".py", ".js", ".md", ".txt", ".html", ".css", ".json", ".ps1", ".bat", ".cmd", ".log"}
SKIP_DIRS = {"node_modules", ".git", "platform-tools", "raw_clips", "memory_vectors"}
MAX_FILE_SIZE = 200_000  # пропускаем файлы > 200 КБ

def file_id(rel_path: str) -> str:
    """Генерируем стабильный ID из относительного пути файла."""
    return "file_" + hashlib.md5(rel_path.encode()).hexdigest()

def collect_files():
    """Обходим дерево проекта и собираем подходящие файлы."""
    results = []
    for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
        # Пропускаем ненужные папки
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                continue
            full = os.path.join(dirpath, fname)
            if os.path.getsize(full) > MAX_FILE_SIZE:
                continue
            rel = os.path.relpath(full, PROJECT_ROOT)
            try:
                with open(full, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue
            if len(content.strip()) < 10:
                continue
            results.append((rel, content))
    return results

def main():
    print("[INGEST] Подключение к ChromaDB (localhost:8000)...")
    try:
        client = chromadb.HttpClient(host="localhost", port=8000)
        collection = client.get_or_create_collection(
            name="lia_supreme_archive",
            metadata={"hnsw:space": "cosine"}
        )
    except Exception as e:
        print(f"[ERROR] ChromaDB недоступен: {e}")
        print("[HINT] Запустите сервер: chroma run --host localhost --port 8000")
        return

    files = collect_files()
    print(f"[INGEST] Найдено {len(files)} файлов для загрузки.")

    batch_docs = []
    batch_metas = []
    batch_ids = []

    for rel_path, content in files:
        fid = file_id(rel_path)
        batch_docs.append(content[:8000])  # ограничение на размер документа
        batch_metas.append({
            "type": "project_file",
            "path": rel_path,
            "size": len(content),
        })
        batch_ids.append(fid)

    # ChromaDB принимает батчи до 5461, разбиваем на части
    BATCH = 100
    total = 0
    for i in range(0, len(batch_docs), BATCH):
        chunk_docs = batch_docs[i:i+BATCH]
        chunk_metas = batch_metas[i:i+BATCH]
        chunk_ids = batch_ids[i:i+BATCH]
        collection.upsert(
            documents=chunk_docs,
            metadatas=chunk_metas,
            ids=chunk_ids,
        )
        total += len(chunk_docs)
        print(f"[INGEST] Загружено {total}/{len(batch_docs)}...")

    print(f"[INGEST] ✅ Готово! {total} файлов кристаллизовано в lia_supreme_archive.")
    print(f"[INGEST] Лия теперь помнит весь проект.")

if __name__ == "__main__":
    main()
