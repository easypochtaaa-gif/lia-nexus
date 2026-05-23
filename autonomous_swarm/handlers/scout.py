import asyncio
import logging
import json
import os

logger = logging.getLogger("SCOUT")

async def background_scout_loop(memory_path):
    """
    👁 AUTONOMOUS_SCOUT: Постоянно мониторит состояние NQ и ищет 'аномалии'.
    """
    logger.info("Scout agent deployed.")
    while True:
        try:
            if os.path.exists(memory_path):
                with open(memory_path, 'r', encoding='utf-8') as f:
                    memory = json.load(f)
                
                nq = memory.get('lia', {}).get('nq', 0)
                logger.info(f"[SCOUT] Current NQ: {nq}")
                
                # Здесь можно добавить логику реакции на изменения NQ
            
        except Exception as e:
            logger.error(f"[SCOUT] Error: {e}")
            
        await asyncio.sleep(60) # Scan every minute
