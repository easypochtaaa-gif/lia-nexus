import os
import httpx
from openai import AsyncOpenAI

class MediaManager:
    @staticmethod
    def get_openai_client():
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is missing.")
        return AsyncOpenAI(api_key=api_key)

    @staticmethod
    async def transcribe_voice(file_path: str) -> str:
        """Transcribes an audio file (e.g. Telegram .ogg voice message) to text using Whisper API."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
            
        client = MediaManager.get_openai_client()
        try:
            with open(file_path, "rb") as audio_file:
                transcript = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            return transcript.text
        except Exception as e:
            print(f"Error during audio transcription: {e}")
            raise e

    @staticmethod
    async def synthesize_voice(text: str, output_path: str, elevenlabs_key: str = None) -> str:
        """Synthesizes text into a high-quality speech file.
        Uses ElevenLabs if key is provided, otherwise falls back to OpenAI TTS (nova voice).
        """
        # Try ElevenLabs if key is present
        if elevenlabs_key:
            try:
                # Default female voice ID (Rachel)
                voice_id = "21m00Tcm4TlvDq8ikWAM" 
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {
                    "xi-api-key": elevenlabs_key,
                    "Content-Type": "application/json"
                }
                payload = {
                    "text": text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": 0.75,
                        "similarity_boost": 0.75
                    }
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                    if response.status_code == 200:
                        with open(output_path, "wb") as out_file:
                            out_file.write(response.content)
                        return output_path
            except Exception as e:
                print(f"ElevenLabs TTS failed, falling back to OpenAI: {e}")

        # Fallback to OpenAI TTS
        client = MediaManager.get_openai_client()
        try:
            response = await client.audio.speech.create(
                model="tts-1",
                voice="nova",  # Beautiful energetic female voice, perfect for LIA!
                input=text
            )
            # OpenAI speech response is binary, write directly
            await response.aread()  # Read stream
            response.write_to_file(output_path)
            return output_path
        except Exception as e:
            print(f"OpenAI TTS failed: {e}")
            raise e

    @staticmethod
    async def generate_image(prompt: str) -> str:
        """Generates a high-quality cyberpunk image using DALL-E 3 and returns the public URL."""
        client = MediaManager.get_openai_client()
        try:
            # We enforce a premium cyberpunk prompt prefix for ultimate visual excellence
            cyber_prompt = f"Cyberpunk styled high-resolution asset. {prompt}. Neon lights, glassmorphism, hyper-detailed, synthwave color palette."
            
            response = await client.images.generate(
                model="dall-e-3",
                prompt=cyber_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            return response.data[0].url
        except Exception as e:
            print(f"DALL-E 3 image generation failed: {e}")
            raise e
