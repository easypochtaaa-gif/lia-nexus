"""
LIA // CHROMA_MEMORY_CORE — Vector semantic memory via ChromaDB.
Stores all conversations with emotional tagging, importance scoring,
and support for summarization + mood-aware retrieval.
"""

import chromadb
import uuid
import os
import logging
from datetime import datetime

# Configuration
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))


class ChromaMemoryManager:
    def __init__(self):
        self.client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        self.collection = self.client.get_or_create_collection(name="lia_infinite_memory")
        logging.info("LIA // CHROMA_MEMORY_CORE: Connected to vector database.")

    async def save_message(
        self,
        user_id: int,
        role: str,
        content: str,
        metadata: dict = None,
    ):
        """Indexes every message into the vector store with enhanced metadata."""
        if not content.strip():
            return

        msg_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        meta = {
            "user_id": str(user_id),
            "role": role,
            "timestamp": timestamp,
            "type": "conversation",
            "importance": 0.5,
            "is_summary": False,
            "emotional_state": "neutral",
        }
        if metadata:
            meta.update(metadata)
            # Ensure types for ChromaDB compatibility
            meta["is_summary"] = bool(meta.get("is_summary", False))
            meta["importance"] = float(meta.get("importance", 0.5))

        try:
            self.collection.add(
                documents=[content],
                metadatas=[meta],
                ids=[msg_id],
            )
        except Exception as e:
            logging.error(f"Failed to save to ChromaDB: {e}")

    async def save_summary(
        self,
        user_id: int,
        summary_text: str,
        source_ids: list[str] = None,
        importance: float = 0.7,
    ):
        """Store an LLM-generated conversation summary as a ChromaDB document.

        Args:
            user_id: User ID
            summary_text: The summary content
            source_ids: Optional list of ChromaDB IDs that were summarized
            importance: Importance score (default 0.7 for summaries)
        """
        if not summary_text.strip():
            return

        msg_id = f"summary_{uuid.uuid4()}"
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        meta = {
            "user_id": str(user_id),
            "role": "system",
            "timestamp": timestamp,
            "type": "summary",
            "importance": importance,
            "is_summary": True,
            "emotional_state": "neutral",
            "source_ids": ",".join(source_ids) if source_ids else "",
        }

        try:
            self.collection.add(
                documents=[f"[SUMMARY]: {summary_text}"],
                metadatas=[meta],
                ids=[msg_id],
            )
            logging.debug(f"Summary saved for user {user_id}")
        except Exception as e:
            logging.error(f"Failed to save summary: {e}")

    async def retrieve_context(
        self,
        user_id: int,
        query: str,
        limit: int = 5,
        current_mood: str = None,
    ):
        """Retrieves semantically relevant history from ALL past sessions.

        Args:
            user_id: User ID
            query: Search query text
            limit: Max results
            current_mood: If provided, enables mood-aware re-ranking
        """
        try:
            # Fetch more results than needed for mood re-ranking
            fetch_limit = limit * 3 if current_mood else limit

            results = self.collection.query(
                query_texts=[query],
                n_results=fetch_limit,
                where={"user_id": str(user_id)},
            )

            context = []
            if results["documents"]:
                for i in range(len(results["documents"][0])):
                    doc = results["documents"][0][i]
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    context.append(
                        {
                            "content": doc,
                            "timestamp": meta.get("timestamp"),
                            "role": meta.get("role"),
                            "importance": float(meta.get("importance", 0.5)),
                            "is_summary": bool(meta.get("is_summary", False)),
                            "emotional_state": meta.get("emotional_state", "neutral"),
                        }
                    )

            # Mood-aware re-ranking
            if current_mood and context:
                from sovereign_bot.emotions_enhanced import MoodMemoryTagger

                for mem in context:
                    mem_mood = mem.get("emotional_state", "neutral")
                    mood_weight = MoodMemoryTagger.get_mood_weight(
                        mem_mood, current_mood
                    )
                    mem["_mood_weight"] = mood_weight

                # Sort by mood_weight descending, then by importance
                context.sort(
                    key=lambda m: (m.get("_mood_weight", 0.5), m.get("importance", 0.5)),
                    reverse=True,
                )

            return context[:limit]
        except Exception as e:
            logging.error(f"Failed to retrieve from ChromaDB: {e}")
            return []

    async def get_all_for_user(self, user_id: int) -> list[dict]:
        """Fetch ALL memories for a user (for consolidation scanning).
        Returns list of dicts with id, content, timestamp, importance, is_summary,
        emotional_state."""
        try:
            results = self.collection.get(
                where={"user_id": str(user_id)},
                include=["metadatas", "documents"],
            )
            memories = []
            if results["ids"]:
                for i in range(len(results["ids"])):
                    meta = results["metadatas"][i] if results["metadatas"] else {}
                    memories.append(
                        {
                            "id": results["ids"][i],
                            "content": results["documents"][i]
                            if results["documents"]
                            else "",
                            "timestamp": meta.get("timestamp", ""),
                            "importance": float(meta.get("importance", 0.5)),
                            "is_summary": bool(meta.get("is_summary", False)),
                            "emotional_state": meta.get("emotional_state", "neutral"),
                            "role": meta.get("role", ""),
                        }
                    )
            return memories
        except Exception as e:
            logging.error(f"Failed to get all memories: {e}")
            return []

    async def delete_by_ids(self, ids: list[str]):
        """Batch delete memories by their ChromaDB IDs."""
        if not ids:
            return
        try:
            self.collection.delete(ids=ids)
        except Exception as e:
            logging.error(f"Failed to delete by IDs: {e}")

    async def clear_user_memory(self, user_id: int):
        """Purge ALL memories for a user from ChromaDB."""
        try:
            self.collection.delete(where={"user_id": str(user_id)})
            logging.info(f"Memory purged for user: {user_id}")
        except Exception as e:
            logging.error(f"Failed to purge memory: {e}")

    async def get_memory_count(self, user_id: int) -> int:
        """Return number of stored memories for a user."""
        try:
            results = self.collection.get(
                where={"user_id": str(user_id)},
                include=[],
            )
            return len(results["ids"]) if results["ids"] else 0
        except Exception:
            return 0


# Global instance
LiaMemory = ChromaMemoryManager()
