import openai
from config import settings
from loguru import logger

class OpenAIService:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())

    async def generate_image(self, prompt: str):
        try:
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=f"Cyberpunk style, neon, high detail: {prompt}",
                n=1,
                size="1024x1024"
            )
            return response.data[0].url
        except Exception as e:
            logger.error(f"DALL-E error: {e}")
            return None

    async def speech_to_text(self, audio_bytes):
        try:
            transcript = await self.client.audio.transcriptions.create(
                model="whisper-1", 
                file=("voice.ogg", audio_bytes)
            )
            return transcript.text
        except Exception as e:
            logger.error(f"Whisper error: {e}")
            return None

openai_service = OpenAIService()
