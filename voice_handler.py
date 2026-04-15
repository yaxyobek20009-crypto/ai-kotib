import os
import logging
import tempfile

logger = logging.getLogger(__name__)


class VoiceHandler:
    def __init__(self):
        import openai
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY topilmadi!")
        self.client = openai.AsyncOpenAI(api_key=api_key)

    async def transcribe(self, voice_bytes: bytes) -> str | None:
        try:
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
                tmp.write(voice_bytes)
                tmp_path = tmp.name
            with open(tmp_path, "rb") as audio_file:
                transcription = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="uz",
                    prompt="O'zbek tilida ish rejalari va vazifalar"
                )
            os.unlink(tmp_path)
            text = transcription.text.strip()
            return text if text else None
        except Exception as e:
            logger.error(f"Whisper xatosi: {e}")
            return None
