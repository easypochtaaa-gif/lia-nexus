import html
import os
import re
import tempfile

from aiogram.types import FSInputFile
from loguru import logger
from openai import AsyncOpenAI

from config import settings


class VoiceService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())
        self.enabled = os.getenv("LIA_VOICE_ENABLED", "true").lower() not in {"0", "false", "off", "no"}
        self.model = os.getenv("LIA_TTS_MODEL", "gpt-4o-mini-tts")
        self.voice = os.getenv("LIA_TTS_VOICE", "nova")
        self.max_chars = int(os.getenv("LIA_TTS_MAX_CHARS", "900"))
        self.instructions = os.getenv(
            "LIA_TTS_INSTRUCTIONS",
            "Speak in a warm, confident, feminine voice with a soft, elegant tone. Keep it natural and respectful."
        )

    def prepare_text(self, text: str) -> str:
        clean = html.unescape(text or "")
        clean = re.sub(r"<[^>]+>", " ", clean)
        clean = re.sub(r"[`*_#>\[\](){}]", " ", clean)
        clean = re.sub(r"https?://\S+", " ссылка ", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean[:self.max_chars]

    async def create_voice_file(self, text: str) -> str | None:
        if not self.enabled:
            return None

        speech_text = self.prepare_text(text)
        if not speech_text:
            return None

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
        tmp_path = tmp.name
        tmp.close()

        try:
            response = await self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=speech_text,
                instructions=self.instructions,
                response_format="opus",
            )
            await response.astream_to_file(tmp_path)
            return tmp_path
        except Exception as e:
            logger.warning(f"TTS voice generation skipped: {e}")
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            return None

    async def send_voice(self, message, text: str):
        tmp_path = await self.create_voice_file(text)
        if not tmp_path:
            return

        try:
            await message.answer_voice(FSInputFile(tmp_path), caption="🎙 Голос LIA")
        except Exception as e:
            logger.warning(f"Telegram voice send skipped: {e}")
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


voice_service = VoiceService()