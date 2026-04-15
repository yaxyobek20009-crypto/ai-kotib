import os
import logging
import tempfile
from groq import AsyncGroq

logger = logging.getLogger(__name__)


class VoiceHandler:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY topilmadi!")
        self.client = AsyncGroq(api_key=api_key)

    async def transcribe(self, voice_bytes: bytes) -> str | None:
        try:
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
                tmp.write(voice_bytes)
                tmp_path = tmp.name
            with open(tmp_path, "rb") as audio_file:
                transcription = await self.client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=("voice.ogg", audio_file),
                    language="uz"
                )
            os.unlink(tmp_path)
            text = transcription.text.strip()
            return text if text else None
        except Exception as e:
            logger.error(f"Groq xatosi: {e}")
            return None
