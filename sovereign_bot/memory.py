import json
import os
import struct
import sqlite3
from datetime import datetime
import redis.asyncio as redis

# Paths
DB_PATH = "/data/lia_sovereign.db" if os.path.exists("/data") else "lia_sovereign.db"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

# Fallback in-memory cache for local testing without Redis
IN_MEMORY_CONTEXTS = {}

class MemoryManager:
    @staticmethod
    def init_db():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vector_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content TEXT,
                embedding BLOB,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

    # --- REDIS SHORT-TERM CONTEXT ---
    @staticmethod
    async def get_redis_client():
        try:
            client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True, socket_timeout=1.0)
            await client.ping()
            return client
        except Exception:
            return None

    @staticmethod
    async def get_recent_context(user_id: int):
        client = await MemoryManager.get_redis_client()
        if client:
            try:
                key = f"chat:{user_id}"
                messages_raw = await client.lrange(key, 0, -1)
                await client.close()
                return [json.loads(msg) for msg in messages_raw]
            except Exception:
                pass
        
        # Fallback to local in-memory context
        return IN_MEMORY_CONTEXTS.get(user_id, [])

    @staticmethod
    async def save_recent_message(user_id: int, role: str, content: str):
        client = await MemoryManager.get_redis_client()
        message_obj = {"role": role, "content": content}
        
        if client:
            try:
                key = f"chat:{user_id}"
                await client.rpush(key, json.dumps(message_obj))
                await client.ltrim(key, -15, -1)  # Limit to last 15 messages
                await client.close()
                return
            except Exception:
                pass
        
        # Fallback to local in-memory context
        if user_id not in IN_MEMORY_CONTEXTS:
            IN_MEMORY_CONTEXTS[user_id] = []
        IN_MEMORY_CONTEXTS[user_id].append(message_obj)
        IN_MEMORY_CONTEXTS[user_id] = IN_MEMORY_CONTEXTS[user_id][-15:]  # Sliding window of 15

    # --- SQLITE LIGHTWEIGHT VECTOR LONG-TERM MEMORY ---
    @staticmethod
    def pack_embedding(vectors: list) -> bytes:
        return struct.pack(f"{len(vectors)}f", *vectors)

    @staticmethod
    def unpack_embedding(blob: bytes) -> list:
        num_floats = len(blob) // 4
        return list(struct.unpack(f"{num_floats}f", blob))

    @staticmethod
    def dot_product(v1: list, v2: list) -> float:
        return sum(x*y for x, y in zip(v1, v2))

    @staticmethod
    def cosine_similarity(v1: list, v2: list) -> float:
        mag1 = sum(x*x for x in v1) ** 0.5
        mag2 = sum(x*x for x in v2) ** 0.5
        if not mag1 or not mag2:
            return 0.0
        return MemoryManager.dot_product(v1, v2) / (mag1 * mag2)

    @staticmethod
    async def save_long_term_memory(user_id: int, content: str, openai_client):
        """Generates OpenAI embedding for a fact or conversation snippet and stores it in SQLite."""
        if not content.strip():
            return
        
        try:
            # Generate embedding using OpenAI API
            response = await openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=content
            )
            embedding = response.data[0].embedding
            blob = MemoryManager.pack_embedding(embedding)
            
            # Save to SQLite database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO vector_memories (user_id, content, embedding, timestamp)
                VALUES (?, ?, ?, ?)
            """, (user_id, content, blob, now))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving long term memory: {e}")

    @staticmethod
    async def retrieve_relevant_memories(user_id: int, query: str, openai_client, limit: int = 3, threshold: float = 0.4):
        """Searches SQLite for the most semantically relevant memories to the query using cosine similarity."""
        if not query.strip():
            return []
            
        try:
            # Generate embedding for the search query
            response = await openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=query
            )
            query_vector = response.data[0].embedding
            
            # Fetch all stored memories for the user
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT content, embedding, timestamp FROM vector_memories WHERE user_id = ?
            """, (user_id,))
            rows = cursor.fetchall()
            conn.close()
            
            results = []
            for content, blob, timestamp in rows:
                vector = MemoryManager.unpack_embedding(blob)
                sim = MemoryManager.cosine_similarity(query_vector, vector)
                if sim >= threshold:
                    results.append((content, timestamp, sim))
                    
            # Sort by similarity descending
            results.sort(key=lambda x: x[2], reverse=True)
            return results[:limit]
        except Exception as e:
            print(f"Error retrieving memory: {e}")
            return []
