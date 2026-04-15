import os
import json
import logging
from datetime import datetime
import pytz
import anthropic

logger = logging.getLogger(__name__)
TASHKENT_TZ = pytz.timezone("Asia/Tashkent")

SYSTEM_PROMPT = """Sen shaxsiy kotibsan. Foydalanuvchi o'zbek tilida vazifa aytadi.
JSON formatida javob ber.

BUGUNGI SANA: {current_datetime}

KATEGORIYALAR: ish, shaxsiy, uchrashuv
MUHIMLIK: urgent=true (muhim/shoshilinch), urgent=false (oddiy)
VAQT: ertaga, juma, bu hafta, yoki bugun

add_task formati:
{{"action":"add_task","event":{{"title":"sarlavha","date_iso":"2026-04-15","time_iso":"10:00","date_str":"15 aprel","time_str":"soat 10:00","category":"ish","urgent":false,"urgency_label":"Oddiy","note":null}}}}

info formati:
{{"action":"info","message":"javob"}}

Faqat JSON qaytار, boshqa hech narsa yozma."""


class AIBrain:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY topilmadi!")
        self.client = anthropic.Anthropic(api_key=api_key)

    async def analyze(self, user_text: str) -> dict:
        now = datetime.now(TASHKENT_TZ)
        day_map = {
            "Monday": "Dushanba", "Tuesday": "Seshanba", "Wednesday": "Chorshanba",
            "Thursday": "Payshanba", "Friday": "Juma", "Saturday": "Shanba", "Sunday": "Yakshanba"
        }
        current_datetime = now.strftime("%Y-%m-%d %A, soat %H:%M")
        for eng, uzb in day_map.items():
            current_datetime = current_datetime.replace(eng, uzb)

        system = SYSTEM_PROMPT.format(current_datetime=current_datetime)

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                system=system,
                messages=[{"role": "user", "content": user_text}]
            )
            raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Xato: {e}")
            return {"action": "info", "message": "Xatolik yuz berdi. Qaytadan urinib koring."}
