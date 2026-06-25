import asyncio
import os
import aiohttp
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load .env
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / '.env')

logger = logging.getLogger("AUTOMATION")

N8N_URL = os.getenv('N8N_URL')
N8N_EMAIL = os.getenv('N8N_EMAIL')
N8N_PASSWORD = os.getenv('N8N_PASSWORD')

async def trigger_n8n_webhook(webhook_id, data):
    """Trigger an n8n webhook with the given data."""
    if not N8N_URL:
        logger.warning("N8N_URL not configured.")
        return None
    
    url = f"{N8N_URL.rstrip('/')}/webhook/{webhook_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    logger.info(f"N8N webhook {webhook_id} triggered successfully.")
                    return await response.json()
                else:
                    logger.error(f"N8N error: {response.status} - {await response.text()}")
    except Exception as e:
        logger.error(f"Failed to trigger N8N: {e}")
    return None

async def background_automation_loop():
    """
    💰 AUTONOMOUS_PROFIT: Triggers n8n workflows for marketing, sales, and system maintenance.
    """
    logger.info("Automation & Profit agent initialized.")
    while True:
        try:
            # Example: Trigger periodic marketing workflow in n8n
            # This would be configured in the user's n8n instance at http://80.89.237.50:5678
            await trigger_n8n_webhook("periodic_marketing", {"status": "active", "source": "lia_swarm"})
            
            # Additional logic can be added here to monitor 'user_balances.json' 
            # and trigger n8n for low-balance notifications or upsell offers.
            
        except Exception as e:
            logger.error(f"[AUTOMATION] Error: {e}")
            
        await asyncio.sleep(3600) # Every hour
