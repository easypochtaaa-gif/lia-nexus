"""Семантический поиск по архиву файлов проекта (опционально).
Переведён на embedded PersistentClient. Если архив (lia_supreme_archive) не загружен —
тихо возвращает пустую строку, без спама ошибок в логах."""
import os
import chromadb
from chromadb.config import Settings
from loguru import logger

CHROMA_PATH = os.getenv("CHROMA_PATH", "/app/database/chroma")


class ChromaService:
    def __init__(self):
        self._client = None
        self._collection = None
        self._tried = False

    def _connect(self):
        if self._tried:
            return
        self._tried = True
        try:
            os.makedirs(CHROMA_PATH, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=CHROMA_PATH,
                settings=Settings(anonymized_telemetry=False),
            )
            try:
                self._collection = self._client.get_collection(name="lia_supreme_archive")
            except Exception:
                self._collection = None  # архив не загружен — это нормально
        except Exception as e:
            logger.warning(f"Chroma project archive unavailable: {e}")

    def query_project(self, query: str, limit: int = 3) -> str:
        self._connect()
        if not self._collection:
            return ""
        try:
            results = self._collection.query(query_texts=[query], n_results=limit)
            if not results or not results.get("documents") or not results["documents"][0]:
                return ""
            context = "\n[СЕМАНТИЧЕСКИЙ КОНТЕКСТ ПРОЕКТА ИЗ ВЕКТОРНОЙ ПАМЯТИ LIA]:\n"
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                path = (meta or {}).get("path", "unknown")
                context += f"--- Файл: {path} ---\n{doc}\n\n"
            return context
        except Exception as e:
            logger.warning(f"ChromaDB project query skipped: {e}")
            return ""


chroma_service = ChromaService()
