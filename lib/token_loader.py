import json
from pathlib import Path

def get_token():
    token_path = Path('C:/Users/StabX/.gemini/antigravity/brain/3febc255-e8de-4a47-9cee-c7e9c5563068/config/token.json')
    with token_path.open(encoding='utf-8') as f:
        data = json.load(f)
    return data['tg_bot_token']
