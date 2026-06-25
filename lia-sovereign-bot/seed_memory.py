"""Run once to pre-populate Architect memory from known facts.
Usage: python seed_memory.py
Can be run inside the Docker container: docker exec lia-sovereign-bot python seed_memory.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.memory import memory_service
from database.db import init_db

async def main():
    await init_db()
    ADMIN_ID = 7915004877
    await memory_service.seed_architect_memory(ADMIN_ID)
    count = await memory_service.count_memories(ADMIN_ID)
    print(f"✅ Architect memory seeded: {count} facts stored for user {ADMIN_ID}")

    # Show what was stored
    mem_text = await memory_service.get_memory(ADMIN_ID)
    print(mem_text)

if __name__ == "__main__":
    asyncio.run(main())
