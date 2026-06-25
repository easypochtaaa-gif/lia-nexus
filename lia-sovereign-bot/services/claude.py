import openai
from loguru import logger
from config import settings
from utils.prompts import LIA_SYSTEM_PROMPT

class ClaudeService:
    def __init__(self):
        # We use the OpenAI client under the hood of ClaudeService to maintain compatibility
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())
        self.model = "gpt-4o"

    async def get_response(self, prompt: str, history: list = None, system_prompt: str = None):
        try:
            messages = []
            
            # Add system prompt
            messages.append({"role": "system", "content": system_prompt or LIA_SYSTEM_PROMPT})
            
            # Add history
            if history:
                for msg in history:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Add new prompt
            messages.append({"role": "user", "content": prompt})

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=4096
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"GPT API error: {e}")
            return "🌀 [NEURAL_LINK_ERROR] Связь с ядром GPT прервана. Проверьте конфигурацию."

    async def get_vision_response(self, prompt: str, image_base64: str, image_media_type: str = "image/jpeg"):
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {
                        "role": "system",
                        "content": LIA_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{image_media_type};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"GPT Vision API error: {e}")
            return "🌀 [VISION_LINK_ERROR] Не удалось проанализировать изображение через GPT Vision."

claude_service = ClaudeService()