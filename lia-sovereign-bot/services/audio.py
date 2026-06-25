import requests
from loguru import logger
from config import settings

class AudioService:
    def __init__(self):
        # We fetch the key dynamically on call to ensure it's loaded
        self.api_url_stt = "https://api.openai.com/v1/audio/transcriptions"
        self.api_url_tts = "https://api.openai.com/v1/audio/speech"

    def transcribe_voice(self, file_path: str) -> str:
        key = settings.openai_api_key.get_secret_value()
        headers = {
            "Authorization": f"Bearer {key}"
        }
        
        try:
            with open(file_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(file_path), f, 'audio/ogg'),
                    'model': (None, 'whisper-1'),
                    'language': (None, 'ru')
                }
                res = requests.post(self.api_url_stt, headers=headers, files=files, timeout=30)
                res_data = res.json()
                
                if 'text' in res_data:
                    return res_data['text'].strip()
                else:
                    logger.error(f"Whisper response error: {res_data}")
                    return ""
        except Exception as e:
            logger.error(f"Whisper STT failed: {e}")
            return ""

    def synthesize_voice(self, text: str) -> bytes:
        key = settings.openai_api_key.get_secret_value()
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "tts-1",
            "voice": "nova", # Clean female voice for LIA
            "input": text[:4000] # OpenAI TTS limit is 4096 characters
        }
        
        try:
            res = requests.post(self.api_url_tts, headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                return res.content
            else:
                logger.error(f"OpenAI TTS error: {res.status_code} - {res.text}")
                return None
        except Exception as e:
            logger.error(f"OpenAI TTS failed: {e}")
            return None

import os
audio_service = AudioService()
