import os
from dotenv import load_dotenv

load_dotenv()

class SwarmConfig:
    # 🛰 IDENTITY
    VERSION = "1.0.0-SWARM"
    NAME = "LIA_SWARM_CORE"
    
    # 🔑 KEYS
    TOKEN = os.getenv('LIFE_LIA_TOKEN')
    ADMIN_ID = int(os.getenv('ADMIN_ID', 7915004877))
    
    # 📁 PATHS
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MEMORY_FILE = os.path.join(BASE_DIR, '..', 'memory.json')
    
    # ⚡ OPTIMIZATION
    MAX_CONCURRENT_TASKS = 10
    SYNC_INTERVAL = 300 # 5 minutes
