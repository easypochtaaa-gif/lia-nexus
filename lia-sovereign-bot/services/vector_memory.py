"""Долговременная векторная память диалогов LIA (embedded ChromaDB + OpenAI embeddings).
Хранит каждый обмен (user/assistant) и возвращает семантически релевантные фрагменты
прошлых бесед конкретного пользователя. Данные персистятся в /app/database/chroma
(смонтированный том -> переживают пересборку контейнера)."""
import os
import time
import asyncio

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from loguru import logger

from config import settings

CHROMA_PATH = os.getenv("CHROMA_PATH", "/app/database/chroma")


class VectorMemory:
    def __init__(self):
        self._col = None
        self._error_logged = False

    def _collection(self):
        if self._col is not None:
            return self._col
        try:
            os.makedirs(CHROMA_PATH, exist_ok=True)
            client = chromadb.PersistentClient(
                path=CHROMA_PATH,
                settings=Settings(anonymized_telemetry=False, allow_reset=False),
            )
            ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.openai_api_key.get_secret_value(),
                model_name="text-embedding-3-small",
            )
            self._col = client.get_or_create_collection(
                name="conversations", embedding_function=ef
            )
            logger.info("VectorMemory ready at {} (docs={})", CHROMA_PATH, self._col.count())
        except Exception as e:
            if not self._error_logged:
                logger.error("VectorMemory init failed: {}", e)
                self._error_logged = True
            self._col = None
        return self._col

    def _add_exchange_sync(self, user_id, user_text, assistant_text):
        col = self._collection()
        if col is None:
            return
        try:
            ts = time.time()
            base = f"{user_id}-{int(ts * 1000)}"
            docs, metas, ids = [], [], []
            if user_text:
                docs.append(user_text)
                metas.append({"user_id": int(user_id), "role": "user", "ts": ts})
                ids.append(base + "-u")
            if assistant_text:
                docs.append(assistant_text)
                metas.append({"user_id": int(user_id), "role": "assistant", "ts": ts})
                ids.append(base + "-a")
            if docs:
                col.add(documents=docs, metadatas=metas, ids=ids)
        except Exception as e:
            logger.error("VectorMemory add failed: {}", e)

    def _recall_sync(self, user_id, query, k=5):
        col = self._collection()
        if col is None or not query:
            return ""
        try:
            res = col.query(
                query_texts=[query],
                n_results=k,
                where={"user_id": int(user_id)},
            )
            docs = (res.get("documents") or [[]])[0]
            metas = (res.get("metadatas") or [[]])[0]
            if not docs:
                return ""
            lines = []
            for d, m in zip(docs, metas):
                who = "Пользователь" if (m or {}).get("role") == "user" else "Лия"
                lines.append(f"- {who}: {d[:400]}")
            return (
                "\n[ДОЛГОВРЕМЕННАЯ ПАМЯТЬ ДИАЛОГОВ — релевантные фрагменты прошлых бесед]:\n"
                + "\n".join(lines)
                + "\n"
            )
        except Exception as e:
            logger.error("VectorMemory recall failed: {}", e)
            return ""

    async def add_exchange(self, user_id, user_text, assistant_text):
        await asyncio.to_thread(self._add_exchange_sync, user_id, user_text, assistant_text)

    async def recall(self, user_id, query, k=5):
        return await asyncio.to_thread(self._recall_sync, user_id, query, k)


vector_memory = VectorMemory()
