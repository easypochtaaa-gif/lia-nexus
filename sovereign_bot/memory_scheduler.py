"""
LIA // MEMORY_SCHEDULER — Background periodic memory maintenance.
Runs consolidation and pruning on a configurable interval.
Started from main.py's main() as a background asyncio task.
"""

import asyncio
import logging
import os

DB_PATH = "/data/lia_sovereign.db" if os.path.exists("/data") else "lia_sovereign.db"


class MemoryScheduler:
    """Manages async background tasks for memory maintenance."""

    @staticmethod
    async def run_periodic_maintenance(
        interval_minutes: int = 60,
        openai_client=None,
        anthropic_client=None,
        max_age_days: int = 90,
        min_importance: float = 0.2,
    ):
        """
        Infinite loop that every `interval_minutes`:
        1. Runs memory consolidation for active users
        2. Prunes stale low-importance memories
        3. Logs maintenance stats

        Args:
            interval_minutes: How often to run maintenance
            openai_client: OpenAI client (for embeddings/LLM)
            anthropic_client: Anthropic client (alternative)
            max_age_days: Max age of low-importance memories before pruning
            min_importance: Memories below this importance score get pruned
        """
        logging.info(
            f"[MEMORY_SCHEDULER] Started. Running every {interval_minutes} min. "
            f"TTL={max_age_days}d, min_importance={min_importance}"
        )

        from sovereign_bot.memory_enhanced import MemoryConsolidator

        while True:
            try:
                await asyncio.sleep(interval_minutes * 60)

                logging.info("[MEMORY_SCHEDULER] Running maintenance cycle...")

                # 1. Prune old low-importance memories globally
                pruned = await MemoryConsolidator.prune_memories(
                    max_age_days=max_age_days,
                    min_importance=min_importance,
                )
                if pruned > 0:
                    logging.info(f"[MEMORY_SCHEDULER] Pruned {pruned} stale memories")

                # 2. Get active users from DB
                try:
                    import sqlite3

                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    # Try to get users with many memories
                    cursor.execute("""
                        SELECT user_id, COUNT(*) as cnt
                        FROM vector_memories
                        GROUP BY user_id
                        HAVING cnt > 50
                        ORDER BY cnt DESC
                        LIMIT 20
                    """)
                    heavy_users = cursor.fetchall()
                    conn.close()
                except Exception:
                    heavy_users = []

                # 3. Consolidate heavy users
                llm = openai_client or anthropic_client
                total_merged = 0
                for user_id, count in heavy_users:
                    try:
                        merged = await MemoryConsolidator.consolidate_memories(
                            user_id,
                            llm_client=llm,
                            threshold=0.85,
                        )
                        total_merged += merged
                    except Exception as e:
                        logging.error(
                            f"[MEMORY_SCHEDULER] Consolidation error for {user_id}: {e}"
                        )

                if total_merged > 0:
                    logging.info(
                        f"[MEMORY_SCHEDULER] Merged {total_merged} duplicate memories across {len(heavy_users)} users"
                    )

                logging.info("[MEMORY_SCHEDULER] Maintenance cycle complete.")

            except asyncio.CancelledError:
                logging.info("[MEMORY_SCHEDULER] Cancelled. Shutting down.")
                break
            except Exception as e:
                logging.error(f"[MEMORY_SCHEDULER] Cycle error: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
